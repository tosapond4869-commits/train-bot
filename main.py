import os
import requests
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
        reply_text = fetch_specific_train_detail(train_num)
    else:
        reply_text = (
            "สวัสดีครับ! บอทเช็คสถานะรถไฟ\n\n"
            "📌 พิมพ์เลขขบวนรถที่ต้องการตรวจสอบได้เลยครับ (เช่น 379 หรือ 4447) ระบบจะดึงสถานะล่าสุดมาให้ทันที"
        )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def fetch_specific_train_detail(train_num):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://ttsview.railway.co.th/'
    }
    
    # 1. ลองค้นหาผ่าน API ค้นหาเฉพาะขบวนโดยตรง
    direct_search_urls = [
        f"https://ttsview.railway.co.th/v3/searchQuery?train={train_num}&lang=th",
        f"https://ttsview.railway.co.th/v3/search?train={train_num}&lang=th"
    ]
    
    found_item = None
    
    for url in direct_search_urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data:
                    found_item = data[0] if isinstance(data, list) else data
                    break
        except Exception:
            continue
            
    # 2. ถ้ายังไม่พบ ลองค้นจากลิสต์รวมทั้งหมด (ทั้งรถโดยสารและรถสินค้า)
    if not found_item:
        fallback_urls = [
            "https://ttsview.railway.co.th/v3/freight/allCargoTrack?lang=th",
            "https://ttsview.railway.co.th/v3/allTrack?lang=th",
            "https://ttsview.railway.co.th/v3/getTrainTrackingList?lang=th"
        ]
        for f_url in fallback_urls:
            try:
                res = requests.get(f_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        for item in data:
                            code_str = str(item.get('train_code', item.get('trainNo', item.get('code', '')))).strip()
                            if train_num in code_str or code_str == train_num:
                                found_item = item
                                break
            except Exception:
                continue
            if found_item:
                break

    # ถ้าเจอข้อมูลไม่ว่าจะจากทางไหน นำมาแสดงผลทันที
    if found_item:
        train_code = found_item.get('train_code', found_item.get('trainNo', train_num))
        train_name = found_item.get('train_name', found_item.get('name', ''))
        station = found_item.get('station_name', found_item.get('current_station', found_item.get('last_station', 'สถานีต้นทาง')))
        time_str = found_item.get('time', found_item.get('update_time', found_item.get('arrival_time', 'ตรวจสอบในระบบ')))
        status = found_item.get('status', found_item.get('delay_status', 'ปกติ'))
        
        return (
            f"🚂 ขบวนรถ: {train_code} {train_name}\n"
            f"📍 สถานีล่าสุด: {station}\n"
            f"⏱️ เวลา: {time_str}\n"
            f"⚠️ สถานะ: {status}"
        )
    
    # 3. ถ้าเป็นขบวนที่อยู่นอกรอบเวลาจริงๆ ให้แสดงข้อพร้อมลิงก์สำรองที่ถูกต้อง
    return (
        f"❌ ขบวน {train_num} อาจจะจอดอยู่ที่สถานีต้นทางหรืออยู่นอกรอบเวลาวิ่งในขณะนี้\n\n"
        f"🔗 ตรวจสอบผ่านเว็บไซต์ รฟท. โดยตรง:\n"
        f"https://ttsview.railway.co.th/v3/?train={train_num}"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
