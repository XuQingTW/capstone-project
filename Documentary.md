# 專案文件

## 專案概述

本專案的目的是整合 [LINE Messaging API](https://developers.line.biz/zh-hant/) 與 [OpenAI ChatCompletion](https://platform.openai.com/docs/guides/chat)（ChatGPT）的功能，打造一個能夠在 LINE 平台上即時提供工程技術支援與諮詢的智能助理。同時，專案擴展為 PowerBI 報表嵌入功能，讓使用者可以在網頁上直觀地展示與分析數據。詳細的 PowerBI 整合步驟請參考專案中的 [整合PowerBI.html](整合PowerBI.html) 文件。

## 技術棧

- **Python 3.9+**：專案主要開發語言
- **Flask**：後端 Web 框架，處理 API 請求與網頁展示
- **line-bot-sdk**：整合 LINE Bot API，處理訊息接收與回覆
- **OpenAI API**：調用 ChatGPT 生成智能回覆
- **PowerBI API**：嵌入 PowerBI 報表以進行數據展示
- **pytest**：進行單元測試
- **GitHub Actions**：CI/CD 流程與 Docker 映像檔自動建置

## 主要功能

1. **LINE 訊息處理**  
   - 利用 `/callback` Webhook 接收並驗證 LINE 傳來的事件。
   - 根據使用者訊息，調用 OpenAI ChatCompletion API 生成專業回覆，再透過 LINE Bot API 回傳結果。

2. **智能對話生成**  
   - 根據預先定義的系統提示，結合使用者輸入生成邏輯嚴謹且具體建議的回應，滿足工程技術諮詢需求。

3. **PowerBI 報表整合**  
   - 透過 OAuth2 客戶端憑證流程，取得 PowerBI API 存取權杖與嵌入 Token。
   - 於 `/powerbi` 路由提供網頁介面展示 PowerBI 報表，並附有詳細的整合步驟參考（請參閱 [整合PowerBI.html](整合PowerBI.html)）。

4. **測試與持續整合**  
   - 使用 `pytest` 與 `unittest.mock` 進行單元測試，確保各模組功能正常。
   - 利用 GitHub Actions 自動化測試、建置 Docker 映像檔與持續部署。

## 專案架構

```
.
├── src/
│   ├── main.py                 # 核心業務邏輯與 OpenAI 服務封裝
│   ├── linebot_connect.py      # Flask 應用與 LINE Bot 事件處理
│   └── powerbi_integration.py  # PowerBI API 整合與報表嵌入模組
├── tests/
│   ├── test_main.py            # 測試 OpenAI 服務及回覆函式
│   ├── test_linebot_connect.py # 測試 LINE Bot 事件處理與簽名驗證
│   └── test_powerbi_integration.py # 測試 PowerBI 整合模組
├── templates/
│   └── powerbi.html            # PowerBI 報表展示頁面
├── 整合PowerBI.html            # PowerBI 整合詳細步驟文件
├── requirements.txt            # Python 套件相依列表
├── main.yml                    # GitHub Actions CI/CD 設定檔
├── Dockerfile                  # Docker 部署設定檔（選用）
├── README.md                   # 專案簡介與快速上手指南
├── Documentary.md              # 專案詳細文件（本文件）
└── .gitignore                  # 忽略檔案清單
```

## 環境設定

請依照以下步驟配置執行環境，確保各模組順利運作：

1. **環境變數設定**  
   下列環境變數需正確設置：
   - **OpenAI 相關：**
     - `OPENAI_API_KEY`：你的 OpenAI API 金鑰。
   - **LINE Bot 相關：**
     - `LINE_CHANNEL_ACCESS_TOKEN`：LINE Bot 存取金鑰。
     - `LINE_CHANNEL_SECRET`：LINE Bot 密鑰。
   - **PowerBI 相關：**
     - `POWERBI_CLIENT_ID`
     - `POWERBI_CLIENT_SECRET`
     - `POWERBI_TENANT_ID`
     - `POWERBI_WORKSPACE_ID`
     - `POWERBI_REPORT_ID`

2. **安裝依賴套件**  
   執行以下指令安裝所需套件：
   ```bash
   pip install -r requirements.txt
   ```

## 執行應用

1. **本地執行**  
   啟動 Flask 應用：
   ```bash
   python src/linebot_connect.py
   ```
   - LINE Webhook 接收端點為 `/callback`。
   - 若要查看 PowerBI 報表嵌入頁面，請存取 `http://localhost:5000/powerbi`。

2. **Docker 部署**  
   若選用 Docker 部署，請依照以下步驟：
   ```bash
   docker build -t your-image-name .
   docker run -p 5000:5000 \
     -e OPENAI_API_KEY="your_openai_api_key" \
     -e LINE_CHANNEL_ACCESS_TOKEN="your_line_access_token" \
     -e LINE_CHANNEL_SECRET="your_line_channel_secret" \
     -e POWERBI_CLIENT_ID="your_powerbi_client_id" \
     -e POWERBI_CLIENT_SECRET="your_powerbi_client_secret" \
     -e POWERBI_TENANT_ID="your_powerbi_tenant_id" \
     -e POWERBI_WORKSPACE_ID="your_powerbi_workspace_id" \
     -e POWERBI_REPORT_ID="your_powerbi_report_id" \
     your-image-name
   ```

## 測試與 CI/CD

1. **單元測試**  
   使用 pytest 執行所有單元測試，確保各模組功能正常：
   ```bash
   pytest
   ```
   測試涵蓋：
   - LINE Bot 事件處理與簽名驗證
   - OpenAI 回覆生成服務
   - PowerBI API 整合功能

2. **持續整合**  
   GitHub Actions 透過 `main.yml` 定義以下流程：
   - 套件安裝與環境變數配置
   - 自動執行單元測試
   - 建置並推送 Docker 映像檔  
   詳細流程請參見 `main.yml`。

## 常見問題與疑難排解

1. **簽名驗證失敗**  
   - 請確認 `LINE_CHANNEL_SECRET` 與 LINE 後台設定保持一致。

2. **API 回覆異常**  
   - 驗證 `OPENAI_API_KEY` 是否正確，並檢查 API 調用是否超出使用配額。

3. **PowerBI 嵌入報表失敗**  
   - 請檢查所有 PowerBI 相關環境變數是否正確配置，並確認 Azure AD 註冊與權限設置無誤。
