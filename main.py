import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, InvalidSignatureError)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    
    if "ขบวน" in user_message or user_message.isdigit():
        train_num = user_message.replace("ขบวน", "").strip()
        reply_text = (
            f"🚂 กำลังตรวจสอบสถานะขบวนรถ: {train_num}\n\n"
            f"สามารถดูตำแหน่งและพิกัดเรียลไทม์สายตะวันออกได้ที่:\n"
            f"https://ttsmaster.railway.co.th/v3/trackMap/?line=3"
        )
    else:
        reply_text = (
            f"สวัสดีครับ! บอทแจ้งเตือนและเช็คสถานะรถไฟพร้อมใช้งาน\n"
            f"พิมพ์เลขขบวนรถที่ต้องการตรวจสอบ (เช่น 281 หรือ ขบวน 281) ได้เลยครับ"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
