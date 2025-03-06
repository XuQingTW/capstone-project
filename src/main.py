import os
import json
import logging
from openai import OpenAI

# OpenAI integration for chat responses
class UserData:
    """存儲用戶對話記錄的類"""
    def __init__(self):
        self.conversations = {}

    def get_conversation(self, user_id):
        """取得特定用戶的對話記錄，若不存在則初始化"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def add_message(self, user_id, role, content):
        """新增一則訊息到用戶的對話記錄中"""
        conversation = self.get_conversation(user_id)
        conversation.append({"role": role, "content": content})
        return conversation

user_data = UserData()

class OpenAIService:
    """處理與 OpenAI API 的互動邏輯"""
    def __init__(self, message, user_id):
        self.user_id = user_id
        self.message = message
        # 從環境變數獲取 OpenAI API 金鑰
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API 金鑰未設置")
        self.client = OpenAI(api_key=self.api_key)

    def get_response(self):
        """向 OpenAI API 發送請求並獲取回應"""
        # 添加用戶的新訊息
        conversation = user_data.add_message(self.user_id, "user", self.message)
        
        try:
            # 呼叫 OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation,
                max_tokens=500
            )
            
            # 取得 AI 回應
            ai_message = response.choices[0].message.content
            
            # 將 AI 回應加入對話歷史
            user_data.add_message(self.user_id, "assistant", ai_message)
            
            return ai_message
        except Exception as e:
            logging.error(f"OpenAI API 錯誤: {e}")
            return "抱歉，我無法處理您的請求。請稍後再試。"

def reply_message(event):
    """處理用戶訊息並回傳 AI 回應"""
    # For LINE v3 API compatibility
    user_message = event.message.text
    user_id = event.source.user_id
    
    # 使用 OpenAI 服務產生回應
    openai_service = OpenAIService(message=user_message, user_id=user_id)
    response = openai_service.get_response()
    
    return response

# 如果直接執行此檔案，則啟動 Flask 應用
if __name__ == "__main__":
    from src.linebot_connect import app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
