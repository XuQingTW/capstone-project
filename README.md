# Capstone Project: LINE Bot 與 ChatGPT 整合及 PowerBI 報表嵌入

## 專案簡介
本專案結合 LINE 官方帳號、OpenAI 的 ChatGPT 與 PowerBI 報表嵌入功能，打造一個能夠提供工程技術支援與諮詢的智能助理平台。使用者可以透過 LINE 傳送訊息，由系統呼叫 ChatGPT API 生成專業回答，同時在網頁上嵌入 PowerBI 報表，以進行即時數據展示與分析。

## 主要功能
- **LINE Bot 智能對話**  
  接收使用者訊息，利用 ChatGPT 產生專業且具實踐性的回覆，再回傳給使用者。
  
- **PowerBI 報表嵌入**  
  整合 PowerBI API，透過 OAuth2 認證流程取得存取權杖與嵌入 Token，並在網頁上動態展示報表。

- **測試與 CI/CD**  
  使用 pytest 進行單元測試，並利用 GitHub Actions 自動化執行測試與 Docker 映像檔建置，確保專案品質。

## 技術棧
- **後端框架**：Flask
- **LINE Bot SDK**：處理 LINE 訊息的接收與回覆
- **OpenAI API**：產生 ChatGPT 對話回覆
- **PowerBI API**：嵌入 PowerBI 報表
- **測試框架**：pytest

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
請確認在執行前已正確配置下列環境變數：

- **OpenAI 相關：**
  - `OPENAI_API_KEY`：OpenAI API 金鑰

- **LINE Bot 相關：**
  - `LINE_CHANNEL_ACCESS_TOKEN`：LINE 存取金鑰
  - `LINE_CHANNEL_SECRET`：LINE 密鑰

- **PowerBI 相關：**
  - `POWERBI_CLIENT_ID`
  - `POWERBI_CLIENT_SECRET`
  - `POWERBI_TENANT_ID`
  - `POWERBI_WORKSPACE_ID`
  - `POWERBI_REPORT_ID`

## 安裝步驟
1. **安裝依賴套件**  
   執行以下指令安裝所有相依的 Python 套件：
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**  
   根據上方說明，設定所有必須的 API 金鑰與參數。

## 運行專案
- **本地執行**  
  啟動 Flask 伺服器：
  ```bash
  python src/linebot_connect.py
  ```
  LINE Webhook 接收端點為 `/callback`。  
  若要檢視 PowerBI 報表嵌入頁面，請瀏覽 `http://localhost:5000/powerbi`。

- **Docker 部署**  
  若使用 Docker 部署，可參考以下指令：
  ```bash
  docker build -t capstone-project .
  docker run -p 5000:5000 \
    -e OPENAI_API_KEY="your_openai_api_key" \
    -e LINE_CHANNEL_ACCESS_TOKEN="your_line_access_token" \
    -e LINE_CHANNEL_SECRET="your_line_channel_secret" \
    -e POWERBI_CLIENT_ID="your_powerbi_client_id" \
    -e POWERBI_CLIENT_SECRET="your_powerbi_client_secret" \
    -e POWERBI_TENANT_ID="your_powerbi_tenant_id" \
    -e POWERBI_WORKSPACE_ID="your_powerbi_workspace_id" \
    -e POWERBI_REPORT_ID="your_powerbi_report_id" \
    capstone-project
  ```

## 測試指南
使用 pytest 執行所有單元測試，確保各模組功能正常：
```bash
pytest
```
測試涵蓋 LINE Bot 事件處理、OpenAI 回覆生成以及 PowerBI 整合功能。

## CI/CD 流程
本專案利用 GitHub Actions 自動執行下列流程：
- 套件安裝與環境變數配置
- 自動執行單元測試
- 建置並推送 Docker 映像檔  
詳細配置請參見 `main.yml`。

## 常見問題與疑難排解
- **LINE 簽名驗證失敗**：請確認 `LINE_CHANNEL_SECRET` 與 LINE 後台設定一致。
- **API 回覆異常**：檢查 `OPENAI_API_KEY` 是否正確，並確認是否超出使用配額。
- **PowerBI 報表嵌入失敗**：請確認所有 PowerBI 相關環境變數正確配置，並檢查 Azure AD 註冊與權限設定是否正確。

## 相關連結
- [LINE 官方帳號管理](https://manager.line.biz/)
- [LINE API 文件（中文）](https://developers.line.biz/zh-hant/)
- [OpenAI API 文件](https://platform.openai.com/docs/)
- [PowerBI API 文件](https://docs.microsoft.com/zh-tw/power-bi/developer/)

## 未來發展方向
- 擴充圖片與多媒體訊息處理功能，豐富互動體驗。
- 優化錯誤處理與回覆機制，提升系統穩定性。
- 整合使用者資料庫，記錄與分析互動歷史。
- 擴展 PowerBI 報表功能，支援更多數據來源與分析視角。

## 結語
本專案致力於打造一個高效、專業且具擴展性的智能工程助理平台，結合前沿 AI 對話技術與動態數據展示，為工程師提供最佳的技術支援與決策參考。歡迎各界開發者參與並持續改進，共同推動智能化技術的創新應用。
