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
        # ลองค้นหาผ่าน API หลายรูปแบบที่เว็บใช้งาน
        urls_to_try = [
            f"https://ttsview.railway.co.th/v3/search?train={train_num}&lang=th",
            f"https://ttsview.railway.co.th/v3/searchQuery?train={train_num}&lang=th",
            f"https://ttsview.railway.co.th/v3/getTrainTrackingList?train={train_num}&lang=th"
        ]
        
        found_item = None
        for api_url in urls_to_try:
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    if isinstance(data, list):
                        found_item = data[0]
                    else:
                        found_item = data
                    break
        
        # ถ้ายังไม่เจอใน API ค้นหาโดยตรง ให้ลองดึงจากลิสต์รวมทั้งหมด (allTrack)
        if not found_item:
            all_track_url = "https://ttsview.railway.co.th/v3/allTrack?lang=th"
            all_res = requests.get(all_track_url, headers=headers, timeout=5)
            if all_res.status_code == 200:
                for item in all_res.json():
                    if train_num in str(item.get('train_code', '')):
                        found_item = item
                        break
                        
        if found_item:
            train_code = found_item.get('train_code', train_num)
            train_name = found_item.get('train_name', found_item.get('name', ''))
            station = found_item.get('station_name', found_item.get('current_station', 'กำลังเดินทาง'))
            status = found_item.get('status', found_item.get('delay_status', 'ปกติ'))
            train_id = found_item.get('id', train_num)
            
            return (
                f"🚂 ขบวน: {train_code} {train_name}\n"
                f"📍 สถานีล่าสุด: {station}\n"
                f"⏱️ สถานะ: {status}\n\n"
                f"🔗 ดูแผนที่แบบละเอียด:\n"
                f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
            )

        return (
            f"❌ ไม่พบข้อมูลสถานะสดของขบวน {train_num} ในระบบขณะนี้\n"
            f"(แม้อาจจะอยู่นอกรอบเวลาวิ่ง หรือจอดอยู่ที่สถานีต้นทาง)\n\n"
            f"ลองตรวจสอบผ่านแผนที่โดยตรง:\n"
            f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        )
        
    except Exception as e:
        return f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
