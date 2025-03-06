import pytest
from unittest.mock import patch, MagicMock
from linebot.v3.webhooks import MessageEvent, TextMessageContent, Source

# 匯入要測試的對象
from src.main import reply_message, OpenAIService, UserData


class MockEvent:
    """
    模擬 LINE 傳來的 event 物件:
    - event.message.text 為用戶的文字
    - event.source.user_id 為用戶 ID
    """
    def __init__(self, user_message, user_id):
        self.message = TextMessageContent(text=user_message, id="message123")
        self.source = MagicMock(spec=Source)
        self.source.user_id = user_id


class MockChoice:
    """模擬 OpenAI 回應的 choice 物件"""
    def __init__(self):
        self.message = MagicMock()
        self.message.content = "這是模擬的回應"


class MockResponse:
    """模擬 OpenAI 的回應物件"""
    def __init__(self):
        choice = MockChoice()
        self.choices = [choice]


@pytest.fixture
def mock_openai_client():
    """
    直接模擬 OpenAI 客戶端，確保 create 方法正確返回
    """
    # 建立一個帶有所需回應的 mock client
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MockResponse()
    
    # 讓 OpenAI 建構子返回我們的 mock client
    with patch('openai.OpenAI', return_value=mock_client):
        yield mock_client.chat.completions.create


def test_openai_service(mock_openai_client):
    """
    測試 OpenAIService 類別是否能正確呼叫 OpenAI API
    並回傳預期的模擬回應
    """
    service = OpenAIService(message="Test message", user_id="test_user")
    response = service.get_response()
    
    # 確認回傳了預期的回應
    assert response == "這是模擬的回應"
    
    # 確認 API 被呼叫
    mock_openai_client.assert_called_once()


def test_reply_message_function(mock_openai_client):
    """
    測試 reply_message 函式是否能正確取得使用者訊息並回傳預期結果
    """
    event = MockEvent(user_message="Hello, AI!", user_id="user_123")
    reply = reply_message(event)
    
    # 確認回傳了預期的回應
    assert reply == "這是模擬的回應"
    
    # 確認 API 被呼叫
    mock_openai_client.assert_called_once()