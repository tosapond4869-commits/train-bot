import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name_)

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
    
    # ตรวจสอบว่าเป็นตัวเลข (เลขขบวนรถ) หรือไม่
    if user_message.isdigit():
        train_num = user_message
        reply_text = search_train(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ ระบบจะค้นหาและดึงข้อมูลให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def search_train(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    try:
        # 1. ค้นหาจากฝั่งรถสินค้า (allCargoTrack)
        cargo_url = "https://ttsview.railway.co.th/v3/freight/allCargoTrack?lang=th"
        cargo_res = requests.get(cargo_url, headers=headers, timeout=5)
        if cargo_res.status_code == 200:
            for item in cargo_res.json():
                code_str = str(item.get('train_code', ''))
                if train_num in code_str:
                    return (
                        f"📦 พบข้อมูลขบวนรถสินค้า: {code_str}\n\n"
                        f"🔗 คลิกดูพิกัดแผนที่รถสินค้า:\n"
                        f"https://ttsview.railway.co.th/v3/freight/?train={train_num}"
                    )
                    
        # 2. ค้นหาจากระบบติดตามทั้งหมด (allTrack)
        all_track_url = "https://ttsview.railway.co.th/v3/allTrack?lang=th"
        all_track_res = requests.get(all_track_url, headers=headers, timeout=5)
        if all_track_res.status_code == 200:
            for item in all_track_res.json():
                code_str = str(item.get('train_code', ''))
                train_id = item.get('id', '')
                if train_num in code_str:
                    return (
                        f"🚂 พบข้อมูลขบวนรถ: {code_str}\n\n"
                        f"🔗 คลิกดูพิกัดแผนที่แบบละเอียด:\n"
                        f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
                    )

        # 3. ค้นหาจากรายการติดตามเชิงลึก (getTrainTrackingList)
        passenger_url = "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th"
        pass_res = requests.get(passenger_url, headers=headers, timeout=5)
        if pass_res.status_code == 200:
            for item in pass_res.json():
                code_str = str(item.get('train_code', ''))
                train_id = item.get('id', '')
                if train_num in code_str:
                    return (
                        f"🚂 พบข้อมูลขบวนรถโดยสาร: {code_str}\n\n"
                        f"🔗 คลิกดูพิกัดแผนที่แบบละเอียด:\n"
                        f"https://ttsview.railway.co.th/v3/trackMap/?train={train_id}"
                    )
                    
        # 4. ถ้าหาไม่พบจริงๆ ให้ส่งลิงก์ตรงสำรองไป
        return (
            f"❌ ไม่พบข้อมูลสถานะสดของขบวน {train_num} ในระบบขณะนี้\n"
            f"(อาจจะจอดอยู่ที่สถานีต้นทาง หรืออยู่นอกรอบเวลาวิ่ง)\n\n"
            f"ลองตรวจสอบผ่านแผนที่โดยตรง:\n"
            f"https://ttsview.railway.co.th/v3/trackMap/?line=3&train={train_num}"
        )
        
    except Exception as e:
        return f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
