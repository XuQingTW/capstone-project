# 專案文件 (Documentary)

## 專案簡介
這個專案為一個整合 [LINE Messaging API](https://developers.line.biz/zh-hant/) 與 [OpenAI ChatCompletion](https://platform.openai.com/docs/guides/chat) 的機器人應用。使用者透過 LINE Bot 傳遞訊息，後端會透過 OpenAI API 生成回覆內容，並由機器人自動回覆到使用者的 LINE 介面中。

## 主要功能
1. **接收 LINE 訊息**：以 `/callback` 路徑作為 Webhook 端點，接收並驗證 LINE 所傳來的事件。
2. **訊息處理與回覆**：對於文字訊息，呼叫 OpenAI ChatCompletion 生成回應，再使用 LINE API 回覆給用戶。
3. **串接測試 (Test)**：以 `pytest` 配合 `unittest.mock` 進行單元測試，模擬 LINE 事件與 OpenAI 回應。

## 專案結構
以下為主要程式檔與目錄說明：

```
.
├── src/
│   ├── main.py              # 主要邏輯與 OpenAI 服務封裝
│   └── linebot_connect.py   # Flask + LINE Bot 啟動與接收事件處理
├── tests/
│   ├── test_main.py         # 測試 main.py 中的功能
│   └── test_linebot_connect.py  # 測試 linebot_connect.py 中的功能
├── requirements.txt         # Python 相依套件列表
├── main.yml                 # GitHub Actions CI/CD 設定檔
├── README.md                # 簡易專案說明 (原始檔)
├── .gitignore
└── Dockerfile (若有)
```

- **`src/main.py`**
  - `SYSTEM_PROMPT`: 預設提供給 OpenAI 的系統提示字串，方便管理與維護。
  - `OpenAIService`: 包裝了呼叫 OpenAI ChatCompletion 的功能，供其他模組使用。
  - `UserData`: (示範用) 用於儲存使用者資訊與訊息。
  - `reply_message(event)`: 主要對外呼叫的函式，接收 LINE 事件物件，抽取文字後傳給 OpenAIService，並回傳最終回覆文字。

- **`src/linebot_connect.py`**
  - 建立 Flask app，並設定 `/callback` 路徑作為 LINE Webhook 的接收點。
  - `handler = WebhookHandler(channel_secret)`: 用於驗證 LINE 傳遞事件的簽名。
  - `callback()` 函式: 接收事件與 `X-Line-Signature` 驗證；若驗證正確則交由 `handler.handle` 處理。
  - `handle_message(event)`: 針對文字訊息，呼叫 `reply_message()` 取得 ChatGPT 回覆，再使用 `line_bot_api.reply_message()` 回傳。

- **`tests/test_main.py` & `tests/test_linebot_connect.py`**
  - 使用 `pytest` 與 `unittest.mock` 實現單元測試。
  - 模擬 LINE 事件、環境變數與 OpenAI 回傳，測試是否能正確取得回覆並回傳預期結果。
  - `test_main.py` 主要測試 `main.py` 的 `OpenAIService` 與 `reply_message()`。
  - `test_linebot_connect.py` 主要測試 Flask 路由與事件處理的行為。

- **`requirements.txt`**
  - 專案所需的 Python 套件：
    - `Flask`, `requests`, `line-bot-sdk>=3.0.0`, `openai`, `pytest` 等。

- **`main.yml` (GitHub Actions)**
  - 定義自動化測試與 CI/CD 流程：
    1. 安裝相依套件並執行 `pytest`。
    2. 以 Docker 建置並推送映像檔至 Docker Hub 或其他容器託管服務。

## 安裝與環境設定

1. **安裝 Python (>=3.7)**  
   建議使用 [pyenv](https://github.com/pyenv/pyenv) 或 [virtualenv](https://docs.python.org/3/library/venv.html) 等方式建立虛擬環境，避免套件衝突。

2. **安裝相依套件**  
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**  
   以下環境變數必須設定才能正常運作：
   - `OPENAI_API_KEY`: 你的 OpenAI API 金鑰
   - `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot 的 Channel Access Token
   - `LINE_CHANNEL_SECRET`: LINE Bot 的 Channel Secret

   可以在本機使用 `.env` 檔案或直接於 Shell 中進行設定：
   ```bash
   export OPENAI_API_KEY="sk-xxxxxx"
   export LINE_CHANNEL_ACCESS_TOKEN="xxxxx"
   export LINE_CHANNEL_SECRET="xxxxx"
   ```

4. **執行 Flask (本機測試)**  
   ```bash
   python src/linebot_connect.py
   ```
   服務預設於 `http://127.0.0.1:5000` 啟動，Webhook callback 位於 `http://127.0.0.1:5000/callback`。

## 使用方法
1. **部署 LINE Bot**  
   - 前往 [LINE 官方帳號後台](https://manager.line.biz/) 或 [LINE Developers](https://developers.line.biz/zh-hant/) 設定你的 Webhook URL 為 `https://YOUR_DOMAIN/callback`，並啟用訊息接收。
2. **傳送訊息測試**  
   - 加入 LINE Bot 為好友後，於對話視窗中輸入文字訊息。
   - Bot 會將訊息轉送至後端，呼叫 OpenAI 生成回覆，並用 LINE API 回覆給你。

## 測試
本專案使用 [pytest](https://docs.pytest.org/en/stable/) 進行測試：
```bash
pytest
```
- `tests/test_main.py`: 測試 `OpenAIService` 與 `reply_message`。
- `tests/test_linebot_connect.py`: 測試 Flask 路由的事件處理邏輯與簽名驗證。

## Docker 部署 (選擇性)
若需要容器化，參考專案中的 `Dockerfile` (若有) 與 `.github/workflows/main.yml`：
1. **建置容器**  
   ```bash
   docker build -t your-image-name .
   ```
2. **執行容器**  
   ```bash
   docker run -p 5000:5000 \
     -e OPENAI_API_KEY="sk-xxxxxx" \
     -e LINE_CHANNEL_ACCESS_TOKEN="xxxxxx" \
     -e LINE_CHANNEL_SECRET="xxxxxx" \
     your-image-name
   ```
   服務同樣在容器內部執行 `0.0.0.0:5000`，並對外映射至主機的 5000 埠。

## 常見問題與排錯
1. **簽名驗證失敗 (400 Bad Request)**  
   - 確認 `LINE_CHANNEL_SECRET` 與 LINE 後台設定相符。
2. **OpenAI 回覆為空或錯誤**  
   - 檢查 `OPENAI_API_KEY` 是否正確且有可用額度。
   - 檢查網路狀況或 OpenAI API 服務是否暫時不可用。
3. **Docker 部署失敗**  
   - 確認 Dockerfile 配置與環境變數設定是否正確。
   - 確認網路連線及 Docker Hub 帳號、金鑰是否正確無誤。

## 結論
本專案透過 Flask 結合 LINE Bot SDK 與 OpenAI API，構建了一個簡單又易於擴充的聊天機器人架構。若有需要擴充更多功能（如資料庫紀錄、其他多媒體訊息處理），可在現有結構上進行模組化開發。希望此文件能幫助你快速上手並維護此專案。

如需更多協助或有任何疑問，請於專案 issue 或 PR 中提出。