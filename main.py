import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    
    if user_message.isdigit():
        train_num = user_message
        reply_text = search_train_detail(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ (เช่น 379 หรือ 283) ระบบจะดึงสถานะล่าสุดมาให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def search_train_detail(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    try:
        # เรียกใช้งาน API ค้นหาข้อมูลขบวนรถโดยตรงตามเลขขบวน
        api_url = f"https://ttsview.railway.co.th/v3/searchQuery?train={train_num}&lang=th"
        response = requests.get(api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # ตรวจสอบว่ามีข้อมูลขบวนรถส่งกลับมาหรือไม่
            if data:
                # รองรับทั้งกรณีที่เป็นอาเรย์หรือ object เดี่ยว
                item = data[0] if isinstance(data, list) else data
                
                train_code = item.get('train_code', train_num)
                train_name = item.get('train_name', item.get('name', ''))
                station = item.get('station_name', item.get('current_station', 'กำลังเดินทาง'))
                status = item.get('status', item.get('delay_status', 'ปกติ'))
                train_id = item.get('id', train_num)
                
                return (
                    f"🚂 ขบวน: {train_code} {train_name}\n"
                    f"📍 สถานีล่าสุด: {station}\n"
                    f"⏱️ สถานะ: {status}\n\n"
                    f"🔗 ดูแผนที่แบบละเอียด:\n"
                    f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
                )
                
        # หากไม่พบจาก API ค้นหา ให้ลองเช็กจากลิสต์รวมทั้งหมด (allTrack) สำรอง
        all_track_url = "https://ttsview.railway.co.th/v3/allTrack?lang=th"
        all_res = requests.get(all_track_url, headers=headers, timeout=5)
        if all_res.status_code == 200:
            for item in all_res.json():
                code_str = str(item.get('train_code', ''))
                if train_num in code_str:
                    train_id = item.get('id', '')
                    station = item.get('station_name', 'กำลังวิ่งบนเส้นทาง')
                    status = item.get('status', 'ปกติ')
                    return (
                        f"🚂 ขบวนรถ: {code_str}\n"
                        f"📍 สถานีล่าสุด: {station}\n"
                        f"⏱️ สถานะ: {status}\n\n"
                        f"🔗 ดูแผนที่แบบละเอียด:\n"
                        f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
                    )

        return (
            f"❌ไม่พบข้อมูลสถานะสดของขบวน {train_num} ในระบบขณะนี้\n"
            f"(แม้อาจจะอยู่นอกรอบเวลาวิ่ง หรือจอดอยู่ที่สถานีต้นทาง)\n\n"
            f"ลองตรวจสอบผ่านแผนที่โดยตรง:\n"
            f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        )
        
    except Exception as e:
        return f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
