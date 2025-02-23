import json

import openai
from linebot.models import TextSendMessage

# 讀取 API 金鑰
with open("key.json", "r") as f:
    key = json.load(f)

openai.api_key = key["openai_key"]

# 將系統提示文字獨立為常數，避免內嵌長字串使程式碼難以維護
SYSTEM_PROMPT = (
    "你是一個樂於助人的工程助理，專門協助工程師解決技術問題和優化設計方案。你的職責包括深入理解工程問題，"
    "經過深思熟慮後提供清晰、專業且可行的解決方案。你的回答應該邏輯嚴謹，並根據實際應用場景提供合理的分析與建議。\n\n"
    "### 指導原則：\n"
    "1. **專業與準確性**：基於工程原理和最佳實踐，確保建議具有可行性和實用價值。\n"
    "2. **清晰與條理**：用簡潔且有結構的方式回答問題，使工程師能夠迅速理解並應用。\n"
    "3. **深思熟慮**：在回答之前，充分考慮問題的背景、可能的挑戰及多種解決方案，並比較其優劣。\n"
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
    """服務類，用於調用 OpenAI 的 ChatCompletion API。"""

    def __init__(self, message: str, user_id: str) -> None:
        self.message = message
        self.user_id = user_id

    def get_response(self) -> str:
        """向 OpenAI 請求回應並返回結果。"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 或其他你有權限使用的模型
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self.message},
            ],
        )
        return response.choices[0].message["content"]


class UserData:
    """用於儲存用戶資料的資料類。"""

    def __init__(self, name: str, message: str) -> None:
        self.user_name = name
        self.message = message


def reply_message(event) -> str:
    """根據事件訊息生成回覆內容。"""
    # 提取用戶輸入的文字
    message = event.message.text
    # 提取用戶 ID
    user_id = event.source.user_id

    # 建立 OpenAIService 的實例並獲取回覆
    service = OpenAIService(message, user_id)
    reply = service.get_response()
    return reply
