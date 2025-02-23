from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from main import reply_message
import json

with open('key.json','r') as f:
    key = json.load(f)


#登入https://developers.line.biz/zh-hant/

app = Flask(__name__)

# 設定 Channel Access Token 和 Channel Secret

line_bot_api = LineBotApi( key["line_Channel_access_token"])
handler = WebhookHandler(key["line_Channel_secret"])

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 標頭
    signature = request.headers['X-Line-Signature']
    # 獲取請求的 body
    body = request.get_data(as_text=True)

    try:
        # 驗證請求並處理事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    replay_token = reply_message(event)
    message = reply_message(event)
    line_bot_api.reply_message(replay_token,message)

if __name__ == "__main__":
    app.run(port=8000)
