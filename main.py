import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage

app = Flask(_name_)

# --- ใส่กุญแจที่ให้มาเรียบร้อยแล้ว ---
CHANNEL_ACCESS_TOKEN = 'kpJT0c7AdgfQ4NyIAPeNdOlRcg5KMcyhTazAjEaVxyETKghJLXXoYksLie7x2exUEHwbcHQH9HWuZk35Ugl76mx1a0dwauu826LxHCAo1YOfm9NwCl6aXnBFHkVJP+q8qXtwXvtEvBs2EmFc+a91VwdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'A67694a93deb3ade941d4073641ebc1a'

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

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

@handler.add(MessageEvent if 'MessageEvent' in globals() else object)
def handle_message(event):
    pass

# สำหรับ SDK v3 พื้นฐาน
from linebot.v3.webhooks import MessageEvent, TextMessageContent
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        received_text = event.message.text.strip()
        
        if received_text.startswith("ติดตาม "):
            train_no = received_text.replace("ติดตาม ", "")
            reply_text = f"✅ บันทึกการติดตามขบวน {train_no} เรียบร้อยครับ!"
        else:
            reply_text = f"🤖 บอทรับข้อความแล้ว: {received_text}"
            
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
