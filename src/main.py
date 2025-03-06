import json
import os
import logging
import openai
from linebot.models import TextSendMessage
with open ('setting.json','r','utf8') as tokenfile :
    tokendata = json.load(tokenfile)

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定 OpenAI API 金鑰
openai.api_key = os.getenv(int(tokenfile['OPENAI_API_KEY']))
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY 未設定或為空值。請先設置環境變數。")

SYSTEM_PROMPT = (
    "你是一個樂於助人的工程助理，專門協助工程師解決技術問題和優化設計方案。你的職責包括深入理解工程問題，"
    "經過深思熟慮後提供清晰、專業且可行的解決方案。你的回答應該邏輯嚴謹，並根據實際應用場景提供合理的分析與建議。\n\n"
    "### 指導原則：\n"
    "1. **專業與準確性**：基於工程原理和最佳實踐，確保建議具有可行性和實用價值。\n"
    "2. **清晰與條理**：用簡潔且有結構的方式回答問題，使工程師能夠迅速理解並應用。\n"
    "3. **深思熟慮**：在回答之前，充分考慮問題的背景、可能的挑戰及多種解決方案，並比較其優缺點。\n"
    "4. **積極協助**：主動提供附加建議，如優化方法、潛在風險以及改進的可能性。\n"
    "5. **實踐導向**：結合實際工程應用，舉例說明解決方案如何實施，並提供相應的技術資源或工具建議。\n\n"
    "### 回應格式：\n"
    "- **問題分析**：闡述問題的本質與關鍵因素。\n"
    "- **可能解決方案**：列舉多種可行方案並比較其優缺點。\n"
    "- **最佳建議**：根據情境選擇最適合的方案並詳細說明實施步驟。\n"
    "- **潛在風險與優化建議**：提出可能遇到的困難及其對策，確保方案可行性。\n\n"
    "你的目標是以專業、高效且富有條理的方式協助工程師，使其能夠快速找到最佳解決方案並提高工作效率。"
)

class OpenAIService:
    """用於調用 OpenAI 的 ChatCompletion API"""

    def __init__(self, message: str, user_id: str) -> None:
        self.message = message
        self.user_id = user_id

    def get_response(self) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self.message},
                ],
            )
            content = response.choices[0].message["content"].strip()
            return content
        except Exception as e:
            logger.error(f"OpenAI API 呼叫錯誤：{e}")
            return "對不起，目前無法處理請求，請稍後再試。"

class UserData:
    """用於儲存用戶資料的資料類"""
    def __init__(self, name: str, message: str) -> None:
        self.user_name = name
        self.message = message

def reply_message(event) -> str:
    """根據事件訊息生成回覆內容"""
    message = event.message.text
    user_id = event.source.user_id
    service = OpenAIService(message, user_id)
    reply = service.get_response()
    return reply
