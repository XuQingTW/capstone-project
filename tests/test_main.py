import pytest
from unittest.mock import patch, MagicMock


# 匯入要測試的對象
from src.main import reply_message, OpenAIService, UserData


class MockEvent:
    """
    模擬 LINE 傳來的 event 物件:
    - event.message.text 為用戶的文字
    - event.source.user_id 為用戶 ID
    """
    def __init__(self, user_message, user_id):
        self.message = MagicMock()
        self.message.text = user_message
        self.source = MagicMock()
        self.source.user_id = user_id


@pytest.fixture
def mock_openai_chatcompletion():
    """
    利用 pytest fixture 模擬 openai.ChatCompletion.create 的回傳結果。
    每次測試前都會套用此 fixture，自動完成 mock 的注入。
    """
    with patch('openai.ChatCompletion.create') as mock_create:
        # 模擬 OpenAI 回傳的結構
        mock_create.return_value.choices = [
            MagicMock(message={"content": "這是模擬的回應"})
        ]
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
