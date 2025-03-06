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


@pytest.fixture
def mock_openai_chatcompletion():
    """
    Mocks the OpenAI API responses for testing
    """
    with patch('openai.OpenAI') as mock_openai_class:
        # Create the mock instance with the entire chain manually
        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        
        # Set up nested attributes
        mock_chat = MagicMock()
        mock_instance.chat = mock_chat
        
        mock_completions = MagicMock()
        mock_chat.completions = mock_completions
        
        mock_create = MagicMock()
        mock_completions.create = mock_create
        
        # Set up the return value structure
        mock_response = MagicMock()
        mock_create.return_value = mock_response
        
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "這是模擬的回應"
        mock_choice.message = mock_message
        
        mock_response.choices = [mock_choice]
        
        yield mock_create
        
def test_openai_service(mock_openai_chatcompletion):
    """
    測試 OpenAIService 類別是否能正確呼叫 openai.ChatCompletion.create，
    並回傳我們模擬的文字 "這是模擬的回應"
    """
    service = OpenAIService(message="Test message", user_id="test_user")
    response = service.get_response()

    assert response == "這是模擬的回應"
    mock_openai_chatcompletion.assert_called_once()  # 確認 API 確實被呼叫


def test_reply_message_function(mock_openai_chatcompletion):
    """
    測試 reply_message 函式是否能正確取得使用者訊息並回傳預期結果
    """
    event = MockEvent(user_message="Hello, AI!", user_id="user_123")
    reply = reply_message(event)
    assert reply == "這是模擬的回應"
    mock_openai_chatcompletion.assert_called_once()
