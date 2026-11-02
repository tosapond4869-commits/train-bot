import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'kpJT0c7AdgfQ4NyIAPeNdOlRcg5KMcyhTazAjEaVxyETKghJLXXoYksLie7x2exUEHwbcHQH9HWuZk35Ugl76mx1a0dwauu826LxHCAo1YOfm9NwCl6aXnBFHkVJP+q8qXtwXvtEvBs2EmFc+a91VwdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'A67694a93deb3ade941d4073641ebc1a'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=['GET'])
def home():
    return "Train Bot is running!"

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
    text = event.message.text.strip()
    if text.startswith("ติดตาม "):
        train_no = text.replace("ติดตาม ", "")
        reply = f"✅ บันทึกการติดตามขบวนรถ {train_no} เรียบร้อยครับ!"
    else:
        reply = f"🤖 บอทได้รับข้อความแล้ว: {text}"
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
