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

# แคชสำหรับจำสถานีล่าสุดของแต่ละขบวน ป้องกันการส่งข้อความซ้ำซาก
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
            "🤖 สวัสดีครับ! บอทติดตามสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการเช็กแบบด่วนได้ทันที (เช่น 379 หรือ 4447)\n"
            "⏰ ระบบจะคอยสแกนทุกขบวนและแจ้งเตือนอัตโนมัติทุกๆ 1 นาทีครับ"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def check_single_train(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    api_list = [
        "https://ttsview.railway.co.th/v3/freight/allCargoTrack?lang=th",
        "https://ttsview.railway.co.th/v3/allTrack?lang=th",
        "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th"
    ]
    
    for url in api_list:
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for item in data:
                        code_str = str(item.get('train_code', item.get('trainNo', item.get('code', '')))).strip()
                        if train_num in code_str or code_str == train_num:
                            station = item.get('station_name', item.get('current_station', item.get('last_station', 'กำลังเดินทาง')))
                            time_str = item.get('time', item.get('update_time', item.get('arrival_time', 'ตรวจสอบในระบบ')))
                            status = item.get('status', item.get('delay_status', 'ปกติ'))
                            train_name = item.get('train_name', item.get('name', ''))
                            return (
                                f"🚂 ขบวนรถ: {train_num} {train_name}\n"
                                f"📍 สถานีล่าสุด: {station}\n"
                                f"⏱️ เวลา: {time_str}\n"
                                f"⚠️ สถานะ: {status}"
                            )
        except Exception:
            continue
            
    return f"❌ ขบวน {train_num} อาจจะจอดอยู่ที่สถานีต้นทาง หรืออยู่นอกรอบเวลาวิ่งในขณะนี้"

# ฟังก์ชันรันเบื้องหลัง เช็กทุกขบวนอัตโนมัติทุกๆ 1 นาที (60 วินาที)
def background_train_monitor():
    while True:
        time.sleep(60) 
        
        if not LINE_NOTIFY_TARGET:
            continue
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://ttsview.railway.co.th/'
        }
        
        api
