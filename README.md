# LINE Bot + OpenAI + PowerBI 整合專案

本專案整合了 LINE Messaging API 與 OpenAI ChatGPT 的功能，打造一個能夠在 LINE 平台上即時提供工程技術支援與諮詢的智能助理。同時，專案也擴展了 PowerBI 報表嵌入功能，讓使用者可以在網頁上直觀地展示與分析數據。

## 主要功能

- **LINE Bot 智能對話**  
  接收使用者訊息，利用 ChatGPT 生成專業、具實踐性的回應，並回傳給使用者。支援多種語言，包括繁體中文、簡體中文、英文、日文和韓文。

- **PowerBI 報表嵌入**  
  整合 PowerBI API，使用 OAuth2 客戶端憑證流程取得存取權杖與嵌入 Token，並在網頁上展示 PowerBI 報表。

- **資料分析與儲存**  
  使用 SQLite 資料庫儲存對話歷史與使用者偏好，提供持久化數據存儲與分析功能。

- **管理後台**  
  提供系統監控與管理功能，包括使用統計、對話記錄查詢與系統狀態監控。

- **安全性與合規性**  
  實作內容安全政策、XSS 防護、安全 Cookie 處理以及適當的輸入過濾。

- **完整測試與 CI/CD**  
  使用 pytest 進行單元測試，並利用 GitHub Actions 自動化測試、Docker 建置與部署，確保專案品質與穩定性。

## 技術棧

- **後端框架**：Flask 2.3+
- **LINE 整合**：LINE Bot SDK v3.x
- **AI 整合**：OpenAI API (gpt-3.5-turbo)
- **數據視覺化**：PowerBI API
- **資料庫**：SQLite
- **安全性**：Flask-Talisman
- **測試框架**：pytest 7.3+
- **CI/CD 工具**：GitHub Actions
- **容器化**：Docker

## 專案架構

```
.
├── src/
│   ├── __init__.py             # Python 包初始化
│   ├── main.py                 # 核心業務邏輯與 OpenAI 服務
│   ├── linebot_connect.py      # Flask 應用與 LINE Bot 事件處理
│   ├── powerbi_integration.py  # PowerBI API 整合模組
│   ├── config.py               # 集中式配置管理
│   ├── database.py             # 資料庫互動模組
│   └── analytics.py            # 數據分析與統計模組
├── tests/
│   ├── test_main.py            # 測試 OpenAI 服務及回覆函式
│   ├── test_linebot_connect.py # 測試 LINE Bot 事件處理
│   └── test_powerbi_integration.py # 測試 PowerBI 整合
├── templates/
│   ├── index.html              # 服務狀態頁面
│   ├── powerbi.html            # PowerBI 報表展示頁面
│   ├── admin_dashboard.html    # 管理後台儀表板
│   ├── admin_login.html        # 管理員登入頁面
│   └── admin_conversation.html # 對話記錄查詢頁面
├── .github/workflows/main.yml  # GitHub Actions CI/CD 設定
├── Dockerfile                  # Docker 部署設定
├── requirements.txt            # Python 套件相依列表
├── README.md                   # 專案簡介（本文件）
├── Documentary.md              # 專案詳細文件
└── .gitignore                  # 忽略檔案清單
```

## 環境設定

請依照以下設定環境變數，確保所有模組均能正確運作：

- **應用程式設定：**
  - `FLASK_DEBUG`：是否啟用 Flask 除錯模式（建議生產環境設為 False）
  - `PORT`：應用程式監聽的埠號（預設 5000）
  - `SECRET_KEY`：Flask sessions 密鑰（用於管理員登入）

- **OpenAI 相關：**
  - `OPENAI_API_KEY`：OpenAI API 金鑰

- **LINE Bot 相關：**
  - `LINE_CHANNEL_ACCESS_TOKEN`：LINE Bot 存取金鑰
  - `LINE_CHANNEL_SECRET`：LINE Bot 密鑰

- **PowerBI 相關：**
  - `POWERBI_CLIENT_ID`：Azure AD 應用程式用戶端 ID
  - `POWERBI_CLIENT_SECRET`：Azure AD 應用程式用戶端密碼
  - `POWERBI_TENANT_ID`：Azure 租戶 ID
  - `POWERBI_WORKSPACE_ID`：PowerBI 工作區 ID
  - `POWERBI_REPORT_ID`：PowerBI 報表 ID

- **管理後台設定：**
  - `ADMIN_USERNAME`：管理員帳號
  - `ADMIN_PASSWORD`：管理員密碼

## 安裝步驟

1. **複製專案儲存庫**
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **建立環境變數檔案**
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，填入所需的環境變數
   ```

3. **安裝相依套件**
   ```bash
   pip install -r requirements.txt
   ```

## 執行專案

### 本地開發
啟動 Flask 伺服器：
```bash
python -m src.linebot_connect
```
- LINE Webhook 接收端點：`/callback`
- PowerBI 報表嵌入頁面：`http://localhost:5000/powerbi`
- 服務狀態頁面：`http://localhost:5000/`
- 管理後台入口：`http://localhost:5000/admin/login`

### Docker 部署
若使用 Docker 部署：
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
  -e ADMIN_USERNAME="your_admin_username" \
  -e ADMIN_PASSWORD="your_admin_password" \
  -e SECRET_KEY="your_secret_key" \
  capstone-project
```

## 測試與 CI/CD

### 單元測試
使用 pytest 執行所有單元測試：
```bash
pytest
```

若要產生覆蓋率報告：
```bash
pytest --cov=src --cov-report=xml
```

測試涵蓋：
- LINE Bot 事件處理與簽名驗證
- OpenAI 回覆生成
- PowerBI API 整合
- 路由與安全性測試

### 持續整合與部署
GitHub Actions 工作流程自動執行以下步驟：

1. **安全性掃描**
   - Bandit：掃描 Python 程式碼中的安全漏洞
   - Safety：檢查相依套件中的已知漏洞

2. **測試階段**
   - 執行 flake8 程式碼品質檢查
   - 執行 pytest 單元測試與覆蓋率分析
   - 上傳測試覆蓋率報告至 Codecov

3. **建置與部署**
   - 使用 Docker Buildx 建置容器映像檔
   - 推送映像檔至 Docker Hub
   - 實作映像檔快取以加速建置流程

4. **部署後安全掃描**
   - 使用 Trivy 掃描容器映像檔中的漏洞
   - 將掃描結果上傳至 GitHub Security

## 使用指南

### LINE Bot 功能
- **一般對話**：直接輸入問題，AI 將生成回應
- **PowerBI 報表**：輸入「powerbi」或「報表」查看數據報表
- **語言設定**：輸入「language:語言代碼」更改語言（例如「language:en」切換至英文）
- **幫助選單**：輸入「help」或「幫助」查看功能選單

### 管理後台
- 訪問 `/admin/login` 路徑，使用設定的管理員帳號密碼登入
- 查看系統統計數據、近期對話記錄與系統狀態
- 檢視個別使用者的完整對話歷史

## 疑難排解

- **LINE 簽名驗證失敗**
  - 確認 `LINE_CHANNEL_SECRET` 與 LINE 開發者控制台設定一致
  - 檢查是否使用了 ngrok 等工具進行本地測試，可能影響 HTTPS 標頭

- **API 回覆異常**
  - 檢查 `OPENAI_API_KEY` 是否正確，並確認未超出使用配額
  - 查看應用程式日誌中的詳細錯誤訊息

- **PowerBI 報表嵌入失敗**
  - 確保所有 PowerBI 相關環境變數已正確配置
  - 檢查 Azure AD 應用程式已被授予適當的 PowerBI API 權限
  - 確認報表有公開存取權限或適當的權限設置

- **Docker 部署問題**
  - 確認已正確設置所有必要的環境變數
  - 檢查容器日誌以獲取詳細的錯誤訊息
  - 確認 Docker 主機的網路設定允許容器連接外部 API

## 安全性考量

本專案實作多層次的安全防護機制：

- **API 安全**：環境變數管理、LINE 簽名驗證、OAuth2 認證流程
- **網頁安全**：內容安全政策(CSP)、安全 Cookie 屬性、HTTPS 強制
- **輸入驗證**：使用者輸入清理、XSS 防護、請求速率限制
- **容器安全**：非 root 使用者執行、最小化攻擊面、CI/CD 安全掃描

## 相關資源

- [LINE 開發者平台](https://developers.line.biz/zh-hant/)
- [OpenAI API 文件](https://platform.openai.com/docs/)
- [PowerBI REST API 文件](https://docs.microsoft.com/zh-tw/power-bi/developer/)
- [Flask 文件](https://flask.palletsprojects.com/)

## 詳細文件

更多詳細技術資訊與整合步驟，請參閱:
- [Documentary.md](Documentary.md) – 專案詳細文件
