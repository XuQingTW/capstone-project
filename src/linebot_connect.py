import os
import logging
import time
from flask import Flask, request, abort, render_template
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from src.powerbi_integration import get_powerbi_embed_config
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from collections import defaultdict

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數取得 LINE 金鑰
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise ValueError("LINE 金鑰未正確設置。請確定環境變數 LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET 已設定。")

# 判斷是否在測試環境 - Moved earlier to ensure it's set before app initialization
is_testing = os.environ.get('TESTING', 'False').lower() == 'true'

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))

csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        'https://cdn.powerbi.com',
        "'unsafe-inline'",  # Only needed for inline PowerBI embed script
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",  # Only needed for inline styles
    ],
    'img-src': "'self'",
    'frame-src': [
        'https://app.powerbi.com',
        'https://cdn.powerbi.com',
    ],
    'connect-src': [
        "'self'",
        'https://api.powerbi.com',
        'https://login.microsoftonline.com',
    ]
}

# Only apply Talisman in non-testing environments to avoid redirects during tests
if not is_testing:
    Talisman(app, 
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        force_https=True,
        session_cookie_secure=True,
        session_cookie_http_only=True,
        feature_policy="geolocation 'none'; microphone 'none'; camera 'none'"
    )
else:
    logger.info("Running in test mode - Talisman security features disabled")

# Handle proxy headers (if behind a proxy)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Setup with the appropriate API client configuration
configuration = Configuration(access_token=channel_access_token)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)

request_counts = defaultdict(list)

def rate_limit_check(ip, max_requests=30, window_seconds=60):
    """
    簡單的 IP 請求限制，防止暴力攻擊
    """
    current_time = time.time()
    
    # 清理舊的請求記錄
    request_counts[ip] = [timestamp for timestamp in request_counts[ip] 
                         if current_time - timestamp < window_seconds]
    
    # 檢查請求數量
    if len(request_counts[ip]) >= max_requests:
        return False
    
    # 記錄新請求
    request_counts[ip].append(current_time)
    return True

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    if not signature:
        logger.error("缺少 X-Line-Signature 標頭。")
        abort(400)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"驗證失敗：{e}")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip().lower()
    # 當使用者輸入 "powerbi" 或 "報表" 時，回覆 PowerBI 報表連結
    if text in ["powerbi", "報表", "powerbi報表"]:
        try:
            config = get_powerbi_embed_config()
            embed_url = config["embedUrl"]
            reply_text = f"請點選下方連結查看 PowerBI 報表：{embed_url}"
        except Exception as e:
            logger.error(f"取得 PowerBI 資訊失敗：{e}")
            reply_text = f"取得 PowerBI 報表資訊失敗：{str(e)}"
        
        # Create message object for v3 API
        message = TextMessage(text=reply_text)
        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[message]
        )
        line_bot_api.reply_message_with_http_info(reply_request)
    else:
        # 其他情況仍由 ChatGPT 處理
        from src.main import reply_message  # Import here to avoid circular imports
        response_text = reply_message(event)
        
        # Create message object for v3 API
        message = TextMessage(text=response_text)
        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[message]
        )
        line_bot_api.reply_message_with_http_info(reply_request)

@app.route("/powerbi")
def powerbi():
    # Add basic rate limiting
    if not rate_limit_check(request.remote_addr):
        return "請求太多，請稍後再試。", 429
        
    try:
        config = get_powerbi_embed_config()
    except Exception as e:
        logger.error("PowerBI 整合錯誤")
        return "系統錯誤，請稍後再試。", 500
    return render_template("powerbi.html", config=config)

@app.route("/")
def index():
    """首頁，顯示簡單的服務狀態"""
    return render_template("index.html")

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)