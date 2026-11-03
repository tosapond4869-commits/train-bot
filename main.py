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
        reply_text = search_train_direct(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ (เช่น 379 หรือ 283) ระบบจะดึงสถานะล่าสุดมาให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def search_train_direct(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    found_item = None
    
    try:
        # 1. ลองค้นหาจาก API รายชื่อรถรวมก่อน
        api_urls = [
            "https://ttsview.railway.co.th/v3/allTrack?lang=th",
            "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th"
        ]
        
        for url in api_urls:
            try:
                res = requests.get(url, headers=headers, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        for item in data:
                            code_val = str(item.get('train_code', item.get('trainNo', ''))).strip()
                            if train_num in code_val or code_val == train_num:
                                found_item = item
                                break
            except Exception:
                continue
            if found_item:
                break

        # 2. ถ้าในลิสต์รวมไม่เจอ ให้ยิงตรงไปที่ API ค้นหาหรือดึงข้อมูลตาม ID ขบวนโดยตรง
        if not found_item:
            direct_urls = [
                f"https://ttsview.railway.co.th/v3/searchQuery?train={train_num}&lang=th",
                f"https://ttsview.railway.co.th/v3/search?train={train_num}&lang=th"
            ]
            for d_url in direct_urls:
                try:
                    d_res = requests.get(d_url, headers=headers, timeout=4)
                    if d_res.status_code == 200:
                        d_data = d_res.json()
                        if d_data:
                            found_item = d_data[0] if isinstance(d_data, list) else d_data
                            break
                except Exception:
                    continue

        # หากเจอข้อมูล ไม่ว่าจะจากทางไหน ก็นำมาแสดงผล
        if found_item:
            train_code = found_item.get('train_code', found_item.get('trainNo', train_num))
            station = found_item.get('station_name', found_item.get('current_station', 'กำลังเดินทาง'))
            status = found_item.get('status', found_item.get('delay_status', 'ปกติ'))
            train_id = found_item.get('id', train_num)
            
            return (
                f"🚂 ขบวนรถ: {train_code}\n"
                f"📍 สถานีล่าสุด: {station}\n"
                f"⏱️ สถานะ: {status}\n\n"
                f"🔗 ดูแผนที่แบบละเอียด:\n"
                f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
            )

        # 3. ถ้าไม่พบจริงๆ ส่งลิงก์ตรงบังคับเปิดแผนที่ของขบวนนั้นให้ทันที
        return (
            f"⚠️ ระบบไม่พบข้อมูลสถานะสดของขบวน {train_num} ในขณะนี้\n\n"
            f"🔗 คลิกเพื่อเปิดดูผ่านแผนที่การรถไฟฯ โดยตรง:\n"
            f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        )
        
    except Exception as e:
        return (
            f"🔗 ตรวจสอบขบวน {train_num} ผ่านแผนที่โดยตรง:\n"
            f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
