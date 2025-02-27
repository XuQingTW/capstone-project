# 專案文件

## 專案概述

本專案致力於整合 [LINE Messaging API](https://developers.line.biz/zh-hant/) 與 [OpenAI ChatCompletion](https://platform.openai.com/docs/guides/chat)，打造一個能夠在 LINE 平台上即時提供技術支援與諮詢的智能助理。專案核心包含智能對話生成，並進一步擴展為 PowerBI 報表嵌入功能，方便用戶在網頁上直觀地展示與分析數據。

## 主要功能

1. **LINE 訊息處理**  
   - 利用 `/callback` Webhook 接收並驗證 LINE 傳來的事件。
   - 針對使用者的文字訊息，調用 OpenAI ChatCompletion API 生成專業回覆，並透過 LINE Bot API 回傳結果。

2. **智能對話生成**  
   - 根據預先定義的系統提示，結合使用者輸入生成邏輯嚴謹且具體建議的回應，滿足工程技術諮詢需求。

3. **PowerBI 報表整合**  
   - 完成 PowerBI API 的存取與報表嵌入，透過 OAuth2 認證流程獲取存取權杖與嵌入 Token。
   - 提供一個網頁介面（例如 `/powerbi` 路由）以展示 PowerBI 報表，便於用戶進行數據分析與監控。

4. **測試與持續整合**  
   - 利用 `pytest` 與 `unittest.mock` 進行單元測試，確保 LINE Bot、OpenAI 服務與 PowerBI 整合模組的功能穩定。
   - 透過 GitHub Actions 自動化測試與 Docker 映像檔建置，實現 CI/CD 流程。

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
├── requirements.txt            # Python 套件相依列表
├── main.yml                    # GitHub Actions CI/CD 設定檔
├── Dockerfile                  # Docker 部署設定檔（選用）
├── README.md                   # 專案簡介與快速上手指南
├── Documentary.md              # 專案詳細文件
└── .gitignore                  # 忽略檔案清單
```

## 環境設定

請依照以下步驟配置執行環境：

1. **環境變數設定**  
   下列環境變數需正確設定，才能保證各模組順利運作：
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
   使用下列指令安裝所需套件：
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
   - 如需查看 PowerBI 報表嵌入頁面，請存取類似 `http://localhost:5000/powerbi` 的 URL。

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
   使用 pytest 執行測試，確保各模組功能正常：
   ```bash
   pytest
   ```
   測試範圍包括：
   - LINE Bot 事件處理與簽名驗證。
   - OpenAI 回覆生成服務。
   - PowerBI API 整合功能。

2. **持續整合**  
   GitHub Actions 透過 `main.yml` 定義以下流程：
   - 套件安裝與環境變數設定。
   - 自動執行所有單元測試。
   - 建置並推送 Docker 映像檔至容器託管平台。

## 常見問題與疑難排解

1. **簽名驗證失敗**  
   - 請確認 `LINE_CHANNEL_SECRET` 與 LINE 後台設定保持一致。

2. **API 回覆異常**  
   - 驗證 `OPENAI_API_KEY` 是否正確，並檢查 API 調用是否超出使用配額。

3. **PowerBI 嵌入報表失敗**  
   - 請檢查所有 PowerBI 相關環境變數是否配置正確，並確認 Azure AD 註冊與權限設置無誤。

## 未來發展方向

- **功能擴充**：支持圖片與多媒體訊息處理，提升對話的豐富度。
- **錯誤處理優化**：增強各模組的錯誤捕捉與回應機制，提高系統穩定性。
- **數據管理**：加入使用者資料庫管理功能，記錄與分析互動歷史。
- **報表展示**：擴展 PowerBI 報表功能，結合更多數據來源進行多角度分析。

## 結語

本專案通過結合先進的對話 AI 與實時數據展示技術，致力於為工程師與技術團隊提供一個高效、專業的解決方案。藉由清晰的系統架構與完善的測試流程，專案具備良好的擴展性與維護性。歡迎有興趣的開發者參與進一步的改進，共同推動智能工程助理的創新應用。
