import os
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
    
    # ตรวจสอบว่าเป็นตัวเลขทั้งหมดหรือไม่
    if user_message.isdigit():
        train_num = user_message
        
        # ตัวอย่างเงื่อนไขการแยกช่วงเลขขบวน (สามารถปรับเปลี่ยนช่วงเลขขบวนสินค้าตามจริงได้ทีหลังครับ)
        # สมมติว่าถ้าเลขขบวนอยู่ในช่วงรถสินค้า ให้วิ่งไปลิงก์สินค้า
        # หรือถ้าเป็นเลขขบวนปกติ ให้วิ่งไปลิงก์รถโดยสารสายตะวันออก
        
        # ตัวอย่าง: สมมติเลขขบวนรถสินค้าขึ้นต้นด้วย 5 หรือ 8 (หรือตามช่วงที่รถไฟใช้จริง)
        # ตรงนี้เราทำโครงสร้างแยกไว้ให้ก่อนครับ
        if train_num.startswith("5") or train_num.startswith("8"):
            reply_text = (
                f"📦 ตรวจสอบขบวนรถสินค้า: {train_num}\n\n"
                f"คลิกดูพิกัดและสถานะรถสินค้า:\n"
                f"https://ttsview.railway.co.th/v3/freight/?train={train_num}"
            )
        else:
            reply_text = (
                f"🚂 ตรวจสอบขบวนรถโดยสาร: {train_num}\n\n"
                f"คลิกดูพิกัดและสถานะบนแผนที่สายตะวันออก:\n"
                f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
            )
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 เพียงพิมพ์เลขขบวนรถที่ต้องการ (เช่น 281 หรือเลขขบวนสินค้า) ได้เลยครับ ระบบจะตรวจสอบให้อัตโนมัติ"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

