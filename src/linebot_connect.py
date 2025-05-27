import datetime
import functools
import logging
import os
import secrets
# import sqlite3  # <<<<<<< REMOVE THIS LINE
import threading
import time
from collections import defaultdict

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_talisman import Talisman
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    CarouselColumn,
    CarouselTemplate,
    Configuration,
    MessageAction,
    MessagingApi,
    PushMessageRequest,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TemplateMessage,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from werkzeug.middleware.proxy_fix import ProxyFix

from database import db
from equipment_scheduler import start_scheduler
from initial_data import initialize_equipment_data
from config import Config # <<<<<<< ADD THIS LINE

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數取得 LINE 金鑰
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise ValueError(
        "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET environment variables must be set."
    )

# Line Bot API 設定
configuration = Configuration(
    access_token=channel_access_token,
)
handler = WebhookHandler(channel_secret)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)
app.secret_key = os.urandom(24)  # 設定 Flask session 的密鑰

# 設定 Flask-Talisman for security headers
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdnjs.cloudflare.com"],
    'style-src': ["'self'", "https://cdnjs.cloudflare.com"],
    'img-src': ["'self'", "data:", "https://*.line-scdn.net"],
    'connect-src': ["'self'", "https://api.line.me"]
}
Talisman(app, content_security_policy=csp)


# 儲存每個聊天室的最後一次訊息時間和狀態 (用於速率限制和狀態管理)
last_message_time = defaultdict(datetime.datetime.min)
chat_states = defaultdict(lambda: {"state": "initial"})  # 為每個聊天室初始化狀態

# 速率限制設定
RATE_LIMIT_INTERVAL = 1  # 每個使用者發送訊息的最小間隔 (秒)

@app.route("/", methods=["GET"])
def index():
    return "Hello Line Bot"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    # 記錄使用者訊息
    db.add_message(
        sender_id=user_id,
        receiver_id="bot",  # 假設 bot 為接收者
        sender_role="user",
        content=user_message,
    )

    # Removed try-except block here. Let reply_message handle its own errors or let them propagate.
    response_text = reply_message(event)
    message = TextMessage(text=response_text)
    reply_request = ReplyMessageRequest(
        reply_token=event.reply_token, messages=[message]
    )
    line_bot_api.reply_message_with_http_info(reply_request)

    # 記錄機器人回覆
    db.add_message(
        sender_id="bot",
        receiver_id=user_id,
        sender_role="assistant",
        content=response_text,
    )


def reply_message(event) -> str:
    user_id = event.source.user_id
    user_message = event.message.text

    # 獲取使用者偏好設定 (為了語言和其他個人化)
    user_prefs = db.get_user_preference(user_id)
    user_language = user_prefs.get("language", Config.DEFAULT_LANGUAGE) # 從 Config 獲取預設語言

    # 處理語言設定
    if user_message.startswith("設定語言"):
        parts = user_message.split()
        if len(parts) == 2:
            lang = parts[1].lower()
            if lang == "英文":
                db.set_user_preference(user_id, language="en")
                return "Language set to English." if user_language == "en" else "語言已設定為英文。"
            elif lang == "中文":
                db.set_user_preference(user_id, language="zh-Hant")
                return "語言已設定為中文。" if user_language == "zh-Hant" else "Language set to Chinese."
            else:
                return "不支援的語言設定。請輸入 '設定語言 英文' 或 '設定語言 中文'。" if user_language == "zh-Hant" else "Unsupported language. Please type 'Set language English' or 'Set language Chinese'."
        else:
            return "請指定語言，例如：'設定語言 英文' 或 '設定語言 中文'。" if user_language == "zh-Hant" else "Please specify language, e.g., 'Set language English' or 'Set language Chinese'."

    # 處理設備資訊查詢
    elif user_message == "設備詳情":
        equipments = db.get_all_equipment() # 使用新的 get_all_equipment 方法
        if not equipments:
            return "目前沒有設備資訊。" if user_language == "zh-Hant" else "No equipment information available."

        reply = "目前設備狀態：\n" if user_language == "zh-Hant" else "Current Equipment Status:\n"
        for eq in equipments:
            reply += f"ID: {eq.get('equipment_id', 'N/A')}, "
            reply += f"名稱: {eq.get('name', 'N/A')}, " if user_language == "zh-Hant" else f"Name: {eq.get('name', 'N/A')}, "
            reply += f"類型: {eq.get('type', 'N/A')}, " if user_language == "zh-Hant" else f"Type: {eq.get('type', 'N/A')}, "
            reply += f"位置: {eq.get('location', 'N/A')}, " if user_language == "zh-Hant" else f"Location: {eq.get('location', 'N/A')}, "
            reply += f"狀態: {eq.get('status', 'N/A')}\n" if user_language == "zh-Hant" else f"Status: {eq.get('status', 'N/A')}\n"
        return reply

    # 處理異常查詢（只需查詢 abnormal_logs 表）
    elif user_message.startswith("查詢異常"):
        parts = user_message.split()
        if len(parts) < 2:
            return "請指定設備 ID，例如：'查詢異常 E-001'。" if user_language == "zh-Hant" else "Please specify equipment ID, e.g., 'Query anomaly E-001'."

        equipment_id = parts[1]

        abnormal_logs = db.get_abnormal_logs(equipment_id) # 呼叫 database.py 中已實現的方法

        if not abnormal_logs:
            return f"設備 {equipment_id} 沒有異常紀錄。" if user_language == "zh-Hant" else f"No anomaly records for equipment {equipment_id}."

        reply = f"設備 {equipment_id} 的最近異常紀錄：\n" if user_language == "zh-Hant" else f"Recent anomaly records for equipment {equipment_id}:\n"
        for log in abnormal_logs:
            # 確保日期時間物件正確格式化
            event_date_str = log['event_date'].strftime('%Y-%m-%d %H:%M') if isinstance(log['event_date'], (datetime.datetime, datetime.date)) else str(log['event_date'])
            reply += f"日期: {event_date_str}, "
            reply += f"類型: {log.get('abnormal_type', 'N/A')}, " if user_language == "zh-Hant" else f"Type: {log.get('abnormal_type', 'N/A')}, "
            reply += f"說明: {log.get('notes', 'N/A')}\n" if user_language == "zh-Hant" else f"Notes: {log.get('notes', 'N/A')}\n"
        return reply

    # 處理一般問候語
    elif user_message in ["哈囉", "你好", "hi", "hello"]:
        if user_language == "en":
            return "Hello! How can I help you today?"
        else:
            return "哈囉！您好，有什麼可以幫您的嗎？"

    # 其他未識別的訊息
    else:
        if user_language == "en":
            return (
                "I'm sorry, I don't understand that command. "
                "You can try 'Equipment Details' or 'Query Anomaly [Equipment ID]' or 'Set Language [English/Chinese]'."
            )
        else:
            return (
                "抱歉，我無法理解您的指令。您試試看輸入 '設備詳情'、"
                "'查詢異常 [設備ID]' 或 '設定語言 [英文/中文]'。"
            )


# Line Messaging API instance
line_bot_api = MessagingApi(ApiClient(configuration))


def send_notification(user_id, message):
    """發送 LINE 訊息給特定使用者"""
    try:
        message_obj = TextMessage(text=message)
        push_request = PushMessageRequest(to=user_id, messages=[message_obj])
        line_bot_api.push_message_with_http_info(push_request)
        return True
    except Exception:
        logger.error("發送通知失敗")
        return False


if __name__ == "__main__":
    # 確保 Config 模組在 Database 之前被載入，以便 Database 可以使用 Config.DB_SERVER 等
    from config import Config # 再次確認導入 Config
    # 首次啟動時初始化資料庫（會建立表，如果它們不存在）
    # db 已經在 database.py 中初始化為 Database() 實例，所以這裡無需再次調用

    # 載入初始設備資料
    initialize_equipment_data()
    # 啟動排程器（可能用於定期檢查設備狀態等）
    start_scheduler()

    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.environ.get("PORT", os.getenv("HTTPS_PORT", 443)))
    print(f"Flask app running on port {port} with debug mode: {debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)