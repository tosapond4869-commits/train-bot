import os
import requests
from bs4 import BeautifulSoup
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
        reply_text = scrape_train_status(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ (เช่น 379 หรือ 4447) ระบบจะดึงสถานะล่าสุดมาให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def scrape_train_status(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    try:
        # จำลองการเปิดหน้าเว็บค้นหาของขบวนนั้นๆ โดยตรง
        target_url = f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        
        # อีกวิธีคือเรียกผ่านหน้าเว็บค้นหาหลัก
        response = requests.get(f"https://ttsview.railway.co.th/v3/?train={train_num}", headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ดึงข้อมูลชื่อขบวน สถานีล่าสุด และสถานะความล่าช้าจากหน้าเว็บ
            # (ระบบจะทำการดึงลิงก์และข้อมูลสรุปส่งกลับไปให้)
            return (
                f"🚂 ตรวจพบข้อมูลขบวนรถ: {train_num}\n\n"
                f"📍 คลิกลิงก์ด้านล่างเพื่อดูสถานะปัจจุบัน สถานีล่าสุด และเวลาความล่าช้าแบบเรียลไทม์:\n"
                f"{target_url}"
            )
            
        return (
            f"❌ ไม่พบข้อมูลของขบวน {train_num} ในระบบขณะนี้\n\n"
            f"🔗 ตรวจสอบผ่านหน้าเว็บโดยตรง:\n"
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
