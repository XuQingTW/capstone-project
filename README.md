## 主要功能
- **LINE Bot 智能對話**  
  接收使用者訊息，利用 ChatGPT 生成專業、具實踐性的回應，並回傳給使用者。

- **PowerBI 報表嵌入**  
  整合 PowerBI API，使用 OAuth2 客戶端憑證流程取得存取權杖與嵌入 Token，並在網頁上展示 PowerBI 報表。

- **測試與 CI/CD**  
  使用 pytest 進行單元測試，並利用 GitHub Actions 自動化測試、Docker 建置與部署，確保專案品質與穩定性。

## 技術棧
- **後端框架**：Flask
- **LINE Bot SDK**：處理 LINE 訊息接收與回覆
- **OpenAI API**：調用 ChatGPT 生成回應
- **PowerBI API**：嵌入並展示 PowerBI 報表
- **測試框架**：pytest
- **CI/CD 工具**：GitHub Actions

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
├── Documentary.md              # 專案詳細文件（進一步技術與流程說明）
└── .gitignore                  # 忽略檔案清單
```

## 環境設定
請根據下列說明配置環境變數，確保所有模組均能正確運作：

- **OpenAI 相關：**
  - `OPENAI_API_KEY`：你的 OpenAI API 金鑰

- **LINE Bot 相關：**
  - `LINE_CHANNEL_ACCESS_TOKEN`：LINE Bot 存取金鑰
  - `LINE_CHANNEL_SECRET`：LINE Bot 密鑰

- **PowerBI 相關：**
  - `POWERBI_CLIENT_ID`
  - `POWERBI_CLIENT_SECRET`
  - `POWERBI_TENANT_ID`
  - `POWERBI_WORKSPACE_ID`
  - `POWERBI_REPORT_ID`

## 安裝步驟
1. **安裝依賴套件**  
   執行以下命令以安裝所有相依套件：
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**  
   根據上方說明，設定所有必須的 API 金鑰與參數（可透過 .env 或系統環境變數設定）。

## 運行專案
- **本地執行**  
  啟動 Flask 伺服器：
  ```bash
  python src/linebot_connect.py
  ```
  - LINE Webhook 接收端點為 `/callback`。
  - 若要查看 PowerBI 報表嵌入頁面，請瀏覽 `http://localhost:5000/powerbi`。

- **Docker 部署**  
  若選用 Docker 部署，請參考以下指令：
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

## 測試指南與 CI/CD
- **單元測試**  
  使用 pytest 執行所有單元測試，確保各模組功能正常：
  ```bash
  pytest
  ```
  測試涵蓋 LINE Bot 事件處理、OpenAI 回覆生成以及 PowerBI 整合功能。

- **持續整合**  
  本專案使用 GitHub Actions 自動進行以下流程：
  - 套件安裝與環境變數配置
  - 執行單元測試
  - Docker 映像檔建置與推送  
  詳情請參見 [main.yml](main.yml)。

## 常見問題與疑難排解
- **LINE 簽名驗證失敗**  
  - 請確認 `LINE_CHANNEL_SECRET` 與 LINE 後台設定一致。

- **API 回覆異常**  
  - 檢查 `OPENAI_API_KEY` 是否正確，並確認未超出使用配額。

- **PowerBI 報表嵌入失敗**  
  - 確認所有 PowerBI 相關環境變數已正確配置，並檢查 Azure AD 註冊與權限設定是否正確。

## 相關連結
- [LINE 官方帳號管理](https://manager.line.biz/)
- [LINE API 文件（中文）](https://developers.line.biz/zh-hant/)
- [OpenAI API 文件](https://platform.openai.com/docs/)
- [PowerBI API 文件](https://docs.microsoft.com/zh-tw/power-bi/developer/)

## 專案文件與詳細說明
更多詳細技術與整合步驟，請參閱專案文件：
- [整合PowerBI.html](整合PowerBI.html) – PowerBI 整合完整步驟說明
- [Documentary.md](Documentary.md) – 專案詳細文件
