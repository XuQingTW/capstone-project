import json
import os

from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot.v3 import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from src.powerbi_integration import get_powerbi_embed_config

# 從 main.py 匯入我們寫好的回覆函式
from src.main import reply_message

# ==============================
# 從環境變數取得 LINE Bot 金鑰
# ==============================
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise ValueError("LINE 金鑰未正確設置。請確定環境變數 LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET 已設定。")

app = Flask(__name__)

#登入https://developers.line.biz/zh-hant/
# 初始化 LINE Bot
line_bot_api = MessagingApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    # 若完全沒有傳 signature，直接回傳 400
    if signature is None:
        abort(400)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 如果 signature 無效或驗簽失敗，也回傳 400
        abort(400)

    return 'OK'

# 註冊事件處理：收到「文字訊息」時呼叫 handle_message()
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    # 呼叫我們在 main.py 中定義的 reply_message()，取得要回覆的內容
    message = reply_message(event)
    # 透過 line_bot_api 回覆訊息
    line_bot_api.reply_message(event.reply_token, message)

def powerbi():
    try:
        config = get_powerbi_embed_config()
    except Exception as e:
        return f"Error: {str(e)}", 500
    return render_template("powerbi.html", config=config)

if __name__ == "__main__":
    # 在 Docker 容器中執行時，host 要設成 "0.0.0.0"
    app.run(host="0.0.0.0", port=5000, debug=True)
