import json
import os

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

# 從 main.py 匯入我們寫好的回覆函式
from main import reply_message

# 讀取 key.json
key_path = os.getenv("KEY_JSON_PATH", "key.json")
with open(key_path, "r") as f:
    key = json.load(f)

app = Flask(__name__)

#登入https://developers.line.biz/zh-hant/
# 初始化 LINE Bot
line_bot_api = LineBotApi(key["line_Channel_access_token"])
handler = WebhookHandler(key["line_Channel_secret"])

@app.route("/callback", methods=['POST'])
def callback():
    """處理來自 LINE 平台的 Webhook 請求."""
    # 取得 X-Line-Signature
    signature = request.headers.get('X-Line-Signature')

    # 取得請求內容（body）
    body = request.get_data(as_text=True)

    try:
        # 驗證簽名並處理訊息
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 註冊事件處理：收到「文字訊息」時呼叫 handle_message()
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    # 呼叫我們在 main.py 中定義的 reply_message()，取得要回覆的內容
    message = reply_message(event)
    # 透過 line_bot_api 回覆訊息
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    # 在 Docker 容器中執行時，host 要設成 "0.0.0.0"
    app.run(host="0.0.0.0", port=5000, debug=True)
