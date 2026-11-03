import os
import time
import threading
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_NOTIFY_TARGET = os.environ.get('LINE_NOTIFY_TARGET', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

sent_cache = {}

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
        reply_text = check_single_train(train_num)
    else:
        reply_text = (
            "🤖 สวัสดีครับคุณเจมส์! บอทติดตามสถานะรถไฟสาย 3\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการเช็กแบบด่วนได้ทันที (เช่น 379 หรือ 4447)\n"
            "⏰ ระบบกำลังสแกนและพร้อมแจ้งเตือนอัตโนมัติครับ"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def fetch_train_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    urls = [
        "https://ttsmaster.railway.co.th/v3/api/trainList?line=3",
        "https://ttsview.railway.co.th/v3/allTrack?lang=th",
        "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th"
    ]
    
    all_trains = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    all_trains.extend(data)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            all_trains.extend(v)
        except Exception:
            continue
            
    return all_trains

def check_single_train(train_num):
    trains = fetch_train_data()
    
    for item in trains:
        code_str = str(item.get('train_code', item.get('trainNo', item.get('code', item.get('trainNumber', item.get('train_id', '')))))).strip()
        if train_num in code_str or code_str == train_num:
            station = item.get('station_name', item.get('current_station', item.get('last_station', item.get('station', 'กำลังเดินทาง'))))
            time_str = item.get('time', item.get('update_time', item.get('arrival_time', 'ตรวจสอบในระบบ')))
            status = item.get('status', item.get('delay_status', 'ปกติ'))
            train_name = item.get('train_name', item.get('name', ''))
            return (
                f"🚂 ขบวนรถ: {train_num} {train_name}\n"
                f"📍 สถานีล่าสุด: {station}\n"
                f"⏱️ เวลา: {time_str}\n"
                f"⚠️ สถานะ: {status}"
            )
            
    return f"❌ ไม่พบข้อมูลสดของขบวน {train_num} ในขณะนี้ (อาจอยู่นอกรอบเวลาเดินรถหรือจอดอยู่ที่สถานีต้นทาง)"

def background_train_monitor():
    print("🚀 Background Train Monitor Started...")
    while True:
        time.sleep(60) 
        
        if not LINE_NOTIFY_TARGET:
            continue
            
        try:
            trains = fetch_train_data()
            seen_trains = set()
            
            for item in trains:
                train_code = str(item.get('train_code', item.get('trainNo', item.get('code', item.get('trainNumber', item.get('train_id', '')))))).strip()
                if not train_code or train_code in seen_trains:
                    continue
                seen_trains.add(train_code)
                
                station = item.get('station_name', item.get('current_station', item.get('last_station', item.get('station', 'กำลังเดินทาง'))))
                time_str = item.get('time', item.get('update_time', item.get('arrival_time', 'ข้อมูลสด')))
                status = item.get('status', item.get('delay_status', 'ปกติ'))
                train_name = item.get('train_name', item.get('name', ''))
                
                last_station = sent_cache.get(train_code, "")
                if train_code not in sent_cache:
                    sent_cache[train_code] = station
                    continue
                    
                if station and station != last_station:
                    sent_cache[train_code] = station
                    notification_text = (
                        f"🚨 แจ้งเตือนสถานะรถไฟอัตโนมัติ\n\n"
                        f"🚂 ขบวนรถ: {train_code} {train_name}\n"
                        f"📍 สถานีล่าสุด: {station}\n"
                        f"⏱️ เวลา: {time_str}\n"
                        f"⚠️ สถานะ: {status}"
                    )
                    try:
                        line_bot_api.push_message(LINE_NOTIFY_TARGET, TextSendMessage(text=notification_text))
                    except Exception:
                        pass
        except Exception:
            pass

monitor_thread = threading.Thread(target=background_train_monitor, daemon=True)
monitor_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
