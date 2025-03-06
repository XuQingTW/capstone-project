import json
import os
import logging
from flask import Flask, request, abort, render_template
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks.models import MessageEvent, TextMessageContent
from src.powerbi_integration import get_powerbi_embed_config
from src.main import reply_message

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數取得 LINE 金鑰
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise ValueError("LINE 金鑰未正確設置。請確定環境變數 LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET 已設定。")

app = Flask(__name__)

# 設定 LINE API 客戶端
configuration = Configuration(access_token=channel_access_token)
parser = WebhookParser(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    if not signature:
        logger.error("缺少 X-Line-Signature 標頭。")
        abort(400)
    try:
        events = parser.parse(body, signature)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                handle_message(event)
    except InvalidSignatureError as e:
        logger.error(f"驗證失敗：{e}")
        abort(400)
    return 'OK'

def handle_message(event: MessageEvent):
    text = event.message.text.strip().lower()
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 當使用者輸入 "powerbi" 或 "報表" 時，回覆 PowerBI 報表連結
        if text in ["powerbi", "報表", "powerbi報表"]:
            try:
                config = get_powerbi_embed_config()
                embed_url = config["embedUrl"]
                reply_text = f"請點選下方連結查看 PowerBI 報表：{embed_url}"
            except Exception as e:
                logger.error(f"取得 PowerBI 資訊失敗：{e}")
                reply_text = f"取得 PowerBI 報表資訊失敗：{str(e)}"
        else:
            # 其他情況仍由 AI 模型處理
            try:
                response_text = reply_message(event)
                reply_text = response_text
            except Exception as e:
                logger.error(f"AI 回覆產生失敗: {e}")
                reply_text = "很抱歉，目前無法處理您的請求。請稍後再試。"
        
        # 發送回覆
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        except Exception as e:
            logger.error(f"LINE API 回覆失敗: {e}")

@app.route("/powerbi")
def powerbi():
    try:
        config = get_powerbi_embed_config()
    except Exception as e:
        logger.error(f"PowerBI 整合錯誤：{e}")
        return f"Error: {str(e)}", 500
    return render_template("powerbi.html", config=config)

@app.route("/")
def index():
    """首頁，顯示簡單的服務狀態"""
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
