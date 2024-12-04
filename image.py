import os
from datetime import datetime
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler # 處理來自 LINE 的 Webhook 請求。
from linebot.v3.exceptions import InvalidSignatureError # 捕捉 Webhook 請求的簽名驗證錯誤。
from linebot.v3.messaging import (
    Configuration, # 配置與 LINE Messaging API 的交互，比如設置 CHANNEL_ACCESS_TOKEN。
    ApiClient, # 用於建立與 LINE API 的連接。
    MessagingApi, # 與 LINE API 進行消息傳遞的功能。
    MessagingApiBlob # 專門用於下載二進制內容，比如處理圖片、音頻等多媒體消息。
)
from linebot.v3.webhooks.models import MessageEvent # 用於處理消息事件，如用戶發送的文本、圖片、貼圖等消息。

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN") or open("CHANNEL_ACCESS_TOKEN.txt", "r", encoding="utf-8").read().strip()
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET") or open("CHANNEL_SECRET.txt", "r", encoding="utf-8").read().strip()

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

FILE_SAVE_DIR = "Save_Path"

if not os.path.exists(FILE_SAVE_DIR):
    os.makedirs(FILE_SAVE_DIR)

@app.route("/callback", methods=['POST'])
def callback():
    """Line SDK BOT Server Callback"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent)
def handle_event(event):
    """通用的事件處理"""
    if event.message.type == "image":
        handle_image_message(event)

def handle_image_message(event):
    """處理用戶發送的圖片消息"""
    image_message = event.message
    user_id = event.source.user_id
    message_id = image_message.id

    app.logger.info(f"Received image from user {user_id}, message ID: {message_id}")

    # 使用 MessagingApiBlob 下載圖片內容
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
        try:
            # 取得圖片內容，這裡返回的是二進制數據
            image_content = line_bot_blob_api.get_message_content(message_id)
        except Exception as e:
            app.logger.error(f"Error getting image content: {str(e)}")
            return

        # 儲存圖片
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_file_name = f"{timestamp}_{user_id}.jpg"
        file_path = os.path.join(FILE_SAVE_DIR, safe_file_name)

        try:
            # 直接寫入二進制內容到文件
            with open(file_path, 'wb') as fd:
                fd.write(image_content)
            app.logger.info(f"Image saved: {file_path}")
        except Exception as e:
            app.logger.error(f"Error saving image: {str(e)}")
            return

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
