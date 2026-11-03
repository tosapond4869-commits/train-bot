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
        reply_text = get_train_live_status(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ (เช่น 379 หรือ 4447) ระบบจะดึงสถานะและเวลาล่าสุดมาให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def get_train_live_status(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    try:
        found_item = None
        
        # 1. ลองค้นหาจาก API รายการรถทั้งหมดทั้งขบวนโดยสารและรถสินค้า
        api_urls = [
            "https://ttsview.railway.co.th/v3/allTrack?lang=th",
            "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th",
            "https://ttsview.railway.co.th/v3/freight/allCargoTrack?lang=th"
        ]
        
        for url in api_urls:
            try:
                res = requests.get(url, headers=headers, timeout=5)
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

        # ถ้าพบข้อมูลจากระบบ ให้ดึงฟิลด์รายละเอียดออกมาแสดง
        if found_item:
            train_code = found_item.get('train_code', found_item.get('trainNo', train_num))
            train_name = found_item.get('train_name', found_item.get('name', ''))
            station = found_item.get('station_name', found_item.get('current_station', 'กำลังเดินทาง'))
            time_str = found_item.get('time', found_item.get('update_time', found_item.get('arrival_time', 'ตรวจสอบในแผนที่')))
            status = found_item.get('status', found_item.get('delay_status', 'ปกติ'))
            train_id = found_item.get('id', train_num)
            
            return (
                f"🚂 ขบวน: {train_code} {train_name}\n"
                f"📍 สถานีล่าสุด: {station}\n"
                f"⏱️ เวลา: {time_str}\n"
                f"⚠️ สถานะความล่าช้า: {status}\n\n"
                f"🔗 ดูพิกัดแผนที่แบบละเอียด:\n"
                f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
            )

        # 2. หากขบวนนั้นจอดอยู่หรืออยู่นอกรอบเวลาวิ่ง ทำให้ดึงจากลิสต์กลางไม่เจอ ส่งลิงก์ตรงให้กดเช็ก
        return (
            f"❌ ไม่พบข้อมูลสถานะสดของขบวน {train_num} ในระบบขณะนี้\n"
            f"(อาจจะจอดอยู่ที่สถานีต้นทาง หรืออยู่นอกรอบเวลาวิ่งในขณะนี้)\n\n"
            f"🔗 ตรวจสอบสถานะและเวลาผ่านแผนที่โดยตรง:\n"
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
