import pytest
from unittest.mock import patch, MagicMock
from linebot.exceptions import InvalidSignatureError
from src.linebot_connect import app, handler

# 從 linebot_connect.py 匯入 Flask app 與 handler
from linebot_connect import app, handler


@pytest.fixture
def client():
    """
    建立 Flask 測試客戶端（test_client），
    讓我們可以模擬對 /callback 路徑發出請求。
    """
    with app.test_client() as client:
        yield client


@patch.object(handler, 'handle')
def test_callback_valid_signature(mock_handle, client):
    """
    測試有正確 X-Line-Signature 時的行為
    - 預期會呼叫 handler.handle
    - 返回 200 OK
    """
    # 假設我們自己生成的 X-Line-Signature
    # 這裡可以用任何非空字串代表
    headers = {'X-Line-Signature': 'valid_signature'}
    data = '{"events": [{"type": "message","message":{"type":"text","text":"Hello"},"replyToken":"dummy_token","source":{"userId":"user123"}}]}'

    resp = client.post('/callback', data=data, headers=headers)
    assert resp.status_code == 200
    mock_handle.assert_called_once_with(data, 'valid_signature')


def test_callback_no_signature(client):
    """
    測試未帶 X-Line-Signature 時的行為
    - 預期會產生 400 Bad Request
    """
    data = '{"events":[]}'
    resp = client.post('/callback', data=data)
    assert resp.status_code == 400


@patch.object(handler, 'handle', side_effect=InvalidSignatureError)
def test_callback_invalid_signature(mock_handle, client):
    """
    測試偽造或無效 X-Line-Signature 時的行為
    - 由於 handler.handle 會拋出 InvalidSignatureError
    - Flask 會回傳 400 Bad Request
    """
    headers = {'X-Line-Signature': 'invalid_signature'}
    data = '{"events":[]}'
    resp = client.post('/callback', data=data, headers=headers)
    assert resp.status_code == 400
    mock_handle.assert_called_once()
