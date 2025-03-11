## 主要功能

- **LINE Bot 智能對話**：接收使用者訊息，利用 ChatGPT 生成專業、具實踐性的回應
- **PowerBI 報表嵌入**：整合 PowerBI API，在網頁上展示資料報表與分析結果
- **半導體設備監控**：即時監控黏晶機、打線機、切割機等設備的運作狀態，自動偵測異常並發送警報
- **多語言支援**：支援繁體中文、簡體中文、英文、日文與韓文等多種語言
- **資料分析與儲存**：使用 SQLite 資料庫儲存對話歷史、使用者偏好與設備監控資料
- **管理後台**：提供系統監控與管理功能，包括使用統計、對話記錄查詢等

## 技術棧

- **Python 3.11**：主要開發語言
- **Flask**：輕量級網頁框架
- **LINE Bot SDK v3.x**：處理 LINE 訊息互動
- **OpenAI API**：接入 ChatGPT 模型 (gpt-3.5-turbo)
- **PowerBI API**：嵌入 PowerBI 報表
- **SQLite**：輕量級資料庫
- **Flask-Talisman**：網頁安全增強
- **Schedule**：設備監控排程
- **pytest**：單元測試框架
- **Docker**：容器化部署
- **GitHub Actions**：CI/CD 自動化工作流程

## 專案架構

```
.
├── src/                          # 主要源碼
│   ├── __init__.py               # Python 包初始化
│   ├── main.py                   # 核心邏輯與 OpenAI 服務
│   ├── linebot_connect.py        # LINE Bot 事件處理
│   ├── powerbi_integration.py    # PowerBI API 整合
│   ├── config.py                 # 配置管理
│   ├── database.py               # 資料庫操作
│   ├── analytics.py              # 數據分析模組
│   ├── equipment_monitor.py      # 設備監控與異常偵測
│   ├── equipment_scheduler.py    # 設備監控排程器
│   ├── event_system.py           # 事件系統
│   ├── app.py                    # Flask 應用程式
│   └── initial_data.py           # 初始資料生成
├── tests/                        # 測試目錄
├── templates/                    # HTML 模板
├── .github/workflows/            # GitHub Actions 設定
├── Dockerfile                    # Docker 配置
├── requirements.txt              # 相依套件列表
└── Documentary.md                # 詳細專案文件
```

## 環境設定

### 必要環境變數

請建立 `.env` 檔案並設定以下環境變數：

```
# 一般設定
FLASK_DEBUG=False
PORT=5000
SECRET_KEY=your_secret_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# LINE Bot API
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# PowerBI API
POWERBI_CLIENT_ID=your_powerbi_client_id
POWERBI_CLIENT_SECRET=your_powerbi_client_secret
POWERBI_TENANT_ID=your_powerbi_tenant_id
POWERBI_WORKSPACE_ID=your_powerbi_workspace_id
POWERBI_REPORT_ID=your_powerbi_report_id

# 管理後台
ADMIN_USERNAME=admin_username
ADMIN_PASSWORD=admin_password
```

### 安裝相依套件

```bash
pip install -r requirements.txt
```

## 執行方式

### 本地開發

```bash
python -m src.linebot_connect
```

### Docker 部署

```bash
docker build -t line-bot-project .
docker run -p 5000:5000 --env-file .env line-bot-project
```

## 系統功能說明

### LINE Bot 指令

- **一般對話**：直接輸入問題，AI 將生成回應
- **PowerBI 報表**：輸入「powerbi」或「報表」查看數據報表
- **設備狀態**：輸入「設備狀態」或「機台狀態」查看所有設備概況
- **設備詳情**：輸入「設備詳情 [設備名稱]」查看特定設備的詳細資訊
- **語言設定**：輸入「language:語言代碼」更改語言 (例如「language:en」切換至英文)
- **幫助選單**：輸入「help」或「幫助」查看功能選單

### 管理後台

1. 訪問 `/admin/login` 進行登入
2. 查看系統統計資料、近期對話與設備狀態
3. 可檢視個別使用者的完整對話歷史

### 設備監控功能

- 監控三種半導體設備：黏晶機、打線機與切割機
- 針對溫度、壓力、良率等指標進行異常偵測
- 依嚴重程度自動發送 LINE 通知
- 提供設備詳情查詢功能

## 測試

執行單元測試：

```bash
pytest
```

產生測試覆蓋率報告：

```bash
pytest --cov=src --cov-report=xml
```

## CI/CD 工作流程

本專案使用 GitHub Actions 自動化下列流程：

1. **安全性掃描**：使用 Bandit 與 Safety 檢查程式碼與相依套件漏洞
2. **測試**：執行單元測試與程式碼品質檢查
3. **建置與部署**：建置 Docker 映像檔並發布
4. **部署後安全掃描**：使用 Trivy 掃描容器映像檔

## 問題排解

- **LINE 簽名驗證失敗**：檢查 LINE_CHANNEL_SECRET 設定
- **OpenAI API 回應異常**：確認 API 金鑰與使用額度
- **PowerBI 嵌入失敗**：檢查 PowerBI 相關設定與權限
- **設備監控問題**：確認資料庫初始化與排程器狀態

## 安全考量

本專案實作多層次安全防護：

- API 金鑰與敏感資訊透過環境變數管理
- 使用 Flask-Talisman 實作內容安全政策(CSP)
- 輸入驗證與清理，防止潛在攻擊
- 非 root 使用者運行 Docker 容器
- 實作請求速率限制，防止暴力攻擊

## 相關資源

- [LINE 開發者平台](https://developers.line.biz/zh-hant/)
- [OpenAI API 文件](https://platform.openai.com/docs/)
- [PowerBI REST API](https://docs.microsoft.com/zh-tw/power-bi/developer/)
- [Flask 文件](https://flask.palletsprojects.com/)

更多詳細資訊，請參閱專案中的 [Documentary.md](Documentary.md)
