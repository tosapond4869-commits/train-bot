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

def get_train_status(train_num):
    """
    ฟังก์ชันดึงสถานะขบวนรถไฟเรียลไทม์จากระบบ TrainMaster การรถไฟฯ
    """
    url = f"https://ttsview.railway.co.th/check_status.php?train_no={train_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ค้นหาข้อความสถานีในตารางข้อมูล
            # ตัวอย่างโครงสร้างข้อมูลจากหน้าเว็บ
            status_element = soup.find('div', {'id': 'result'}) or soup.find('table')
            
            if status_element:
                text_content = status_element.get_text(separator="\n", strip=True)
                # ดึงเฉพาะข้อความส่วนสำคัญ หรือตัดคำตอบกลับ
                lines = [line for line in text_content.split('\n') if line]
                if len(lines) > 0:
                    summary = "\n".join(lines[:6]) # นำ 6 บรรทัดแรกมาแสดง
                    return f"🚂 สถานะขบวนรถ {train_num}\n\n{summary}"
        
        # หากดึงข้อมูลอัตโนมัติไม่สำเร็จ ให้ fallback ส่งลิงก์แผนที่ตามเดิม
        return (
            f"🚂 ตรวจสอบขบวนรถ: {train_num}\n\n"
            f"ดูพิกัดตำแหน่งเรียลไทม์บนแผนที่สายตะวันออก:\n"
            f"https://ttsmaster.railway.co.th/v3/trackMap/?line=3"
        )
    except Exception as e:
        # กรณีเกิดข้อผิดพลาดในการเชื่อมต่อ
        return (
            f"🚂 ตรวจสอบขบวนรถ: {train_num}\n\n"
            f"ดูพิกัดตำแหน่งเรียลไทม์บนแผนที่สายตะวันออก:\n"
            f"https://ttsmaster.railway.co.th/v3/trackMap/?line=3"
        )

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
    
    # เช็คว่าผู้ใช้พิมพ์เลขขบวนรถหรือไม่
    if "ขบวน" in user_message or user_message.isdigit():
        train_num = user_message.replace("ขบวน", "").strip()
        reply_text = get_train_status(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะขบวนรถไฟพร้อมใช้งาน\n"
            "พิมพ์เลขขบวนรถที่ต้องการ (เช่น 281 หรือ ขบวน 1138) ได้เลยครับ"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
