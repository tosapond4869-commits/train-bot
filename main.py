import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import time
import threading

app = Flask(_name_)

# --- ใส่กุญแจที่ก๊อปปี้มาจาก LINE ตรงนี้ ---
LINE_CHANNEL_ACCESS_TOKEN = 'kpJT0c7AdgfQ4NyIAPeNdOlRcg5KMcyhTazAjEaVxyETKghJLXXoYksLie7x2exUEHwbcHQH9HWuZk35Ugl76mx1a0dwauu826LxHCAo1YOfm9NwCl6aXnBFHkVJP+q8qXtwXvtEvBs2EmFc+a91VwdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'a67694a93deb3ade941d4073641ebc1a'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# เก็บรายชื่อขบวนที่ผู้ใช้แต่ละคนสนใจ (ตัวอย่างชั่วคราวในความจำ)
user_subscriptions = {}

@app.route("/", methods=['GET'])
def home():
    return "Train Bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.text.strip()
    
    if text.startswith("ติดตาม "):
        train_no = text.replace("ติดตาม ", "")
        if user_id not in user_subscriptions:
            user_subscriptions[user_id] = []
        if train_no not in user_subscriptions[user_id]:
            user_subscriptions[user_id].append(train_no)
            reply_text = f"✅ บันทึกการติดตามขบวน {train_no} เรียบร้อยครับ!"
        else:
            reply_text = f"⚠️ คุณติดตามขบวน {train_no} นี้อยู่แล้วครับ"
            
    elif text == "รายการที่ติดตาม":
        trains = user_subscriptions.get(user_id, [])
        reply_text = f"🚆 ขบวนที่คุณกำลังติดตาม: {', '.join(trains) if trains else 'ยังไม่มี'}"
    else:
        reply_text = "คำสั่งแนะนำ:\n- พิมพ์ 'ติดตาม [เลขขบวน]' เช่น ติดตาม 2256\n- พิมพ์ 'รายการที่ติดตาม' เพื่อดูขบวนทั้งหมด"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
