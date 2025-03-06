# 專案文件

## 專案概述

本專案整合 [LINE Messaging API](https://developers.line.biz/zh-hant/) 與 [OpenAI ChatCompletion](https://platform.openai.com/docs/guides/chat)（ChatGPT）的功能，打造一個能夠在 LINE 平台上即時提供工程技術支援與諮詢的智能助理。同時，專案擴展為 PowerBI 報表嵌入功能，讓使用者可以在網頁上直觀地展示與分析數據。此外，系統包含半導體設備的即時監控功能，能自動偵測異常並通過 LINE 機器人發送警報。系統還包含完整的使用者數據儲存、分析功能以及管理後台。

## 技術棧

- **Python 3.11**：專案主要開發語言，基於最新穩定版本
- **Flask**：輕量級後端 Web 框架，處理 API 請求與網頁展示
- **line-bot-sdk v3.x**：整合 LINE Bot API，處理訊息接收與回覆
- **OpenAI API**：調用 ChatGPT 模型生成智能回覆
- **PowerBI API**：嵌入 PowerBI 報表以進行數據展示
- **SQLite**：輕量級數據庫，儲存對話歷史、使用者偏好與設備數據
- **Schedule**：簡易任務排程，用於定期設備監控
- **Flask-Talisman**：實作內容安全政策(CSP)與其他安全防護
- **pytest**：進行單元測試與覆蓋率分析
- **Docker**：容器化部署，確保環境一致性
- **GitHub Actions**：CI/CD 流程自動化與安全掃描

## 主要功能

1. **LINE 訊息處理**  
   - 利用 `/callback` Webhook 接收並驗證 LINE 傳來的事件
   - 根據使用者訊息，調用 OpenAI ChatCompletion API 生成專業回覆，再透過 LINE Bot API 回傳結果
   - 實作訊息輸入驗證與清理，防止潛在的 XSS 攻擊
   - 支援快速回覆、按鈕模板等 LINE 互動元素

2. **智能對話生成**  
   - 根據預先定義的系統提示，結合使用者輸入生成邏輯嚴謹且具體建議的回應
   - 維護對話歷史紀錄，提供上下文相關的回覆
   - 透過 sanitize_input 函數進行輸入清理，增強安全性
   - 支援多語言回覆，包含繁體中文、簡體中文、英文、日文和韓文

3. **PowerBI 報表整合**  
   - 透過 OAuth2 客戶端憑證流程，取得 PowerBI API 存取權杖與嵌入 Token
   - 於 `/powerbi` 路由提供網頁介面展示 PowerBI 報表
   - 實作基於 IP 的請求限制，防止潛在的 DoS 攻擊
   - 在 LINE Bot 中提供快速查看報表的連結功能

4. **半導體設備監控**  
   - 即時監控各類半導體設備（黏晶機、打線機、切割機）的運作狀態與關鍵指標
   - 自動偵測設備異常，包括溫度、壓力、轉速、良率等指標超出閾值的情況
   - 以不同嚴重程度（警告、嚴重、緊急）分類設備異常
   - 透過 LINE 機器人即時發送警報通知給相關責任人員
   - 支援排程功能，定期檢查設備狀態（預設每 5 分鐘一次）
   - 提供設備狀態查詢指令，可查看所有設備概況或特定設備詳情

5. **資料儲存與分析**  
   - 使用 SQLite 資料庫儲存對話歷史、使用者偏好與設備監控數據
   - 實作完整的分析模組，追蹤用戶行為與系統使用狀況
   - 生成使用趨勢數據，包括每日訊息量、活躍用戶數等統計
   - 支援關鍵字追蹤與分析，了解使用者主要關注的話題
   - 儲存設備運行指標與警報歷史，便於後續分析與改進

6. **管理後台**  
   - 提供安全的管理員登入系統
   - 展示系統使用統計，包括總對話數、用戶數等關鍵指標
   - 查看個別使用者的完整對話歷史
   - 監控系統狀態，顯示各API連接情況
   - 查看設備監控概況與異常警報

7. **網站安全性強化**
   - 使用 Flask-Talisman 實作內容安全政策(CSP)，限制資源載入來源
   - 實作安全的 Cookie 設定（HttpOnly, Secure flags）
   - 設置適當的特性政策(Feature-Policy)，限制敏感 API 的使用
   - 處理代理標頭，確保在代理伺服器後方運作正常

8. **集中式配置管理**
   - 使用 config.py 統一管理所有環境變數與設定
   - 實作環境變數驗證機制，確保必要的設定存在
   - 集中式日誌配置，提供一致的日誌格式與級別

## 專案架構

```
.
├── src/
│   ├── __init__.py               # Python 包初始化檔案
│   ├── config.py                 # 集中式配置管理模組
│   ├── main.py                   # 核心業務邏輯與 OpenAI 服務封裝
│   ├── linebot_connect.py        # Flask 應用與 LINE Bot 事件處理
│   ├── powerbi_integration.py    # PowerBI API 整合與報表嵌入模組
│   ├── database.py               # 資料庫互動模組
│   ├── analytics.py              # 數據分析與統計模組
│   ├── equipment_monitor.py      # 半導體設備監控與異常偵測器
│   ├── equipment_scheduler.py    # 設備監控排程器
│   └── initial_data.py           # 初始設備資料生成腳本
├── tests/
│   ├── __init__.py               # 測試包初始化檔案
│   ├── conftest.py               # pytest 配置與共用 fixtures
│   ├── test_main.py              # 測試 OpenAI 服務及回覆函式
│   ├── test_linebot_connect.py   # 測試 LINE Bot 事件處理與簽名驗證
│   ├── test_powerbi_integration.py # 測試 PowerBI 整合模組
│   └── test_equipment_alert.py   # 測試設備警報功能
├── templates/
│   ├── index.html                # 服務狀態頁面
│   ├── powerbi.html              # PowerBI 報表展示頁面
│   ├── admin_dashboard.html      # 管理後台儀表板
│   ├── admin_login.html          # 管理員登入頁面
│   └── admin_conversation.html   # 對話記錄查詢頁面
├── .github/
│   └── workflows/
│       └── main.yml              # GitHub Actions CI/CD 設定檔
├── .env.example                  # 環境變數範例檔案
├── requirements.txt              # Python 套件相依列表
├── Dockerfile                    # Docker 部署設定檔
├── README.md                     # 專案簡介與快速上手指南
├── Documentary.md                # 專案詳細文件（本文件）
├── pytest.py                     # pytest 設定檔
└── .gitignore                    # 忽略檔案清單
```

## 環境設定

請依照以下步驟配置執行環境，確保各模組順利運作：

1. **環境變數設定**  
   依照 `.env.example` 建立 `.env` 檔案，設定下列必要環境變數：
   - **OpenAI 相關：**
     - `OPENAI_API_KEY`：你的 OpenAI API 金鑰
   - **LINE Bot 相關：**
     - `LINE_CHANNEL_ACCESS_TOKEN`：LINE Bot 存取金鑰
     - `LINE_CHANNEL_SECRET`：LINE Bot 密鑰
   - **PowerBI 相關：**
     - `POWERBI_CLIENT_ID`：Azure AD 應用程式用戶端 ID
     - `POWERBI_CLIENT_SECRET`：Azure AD 應用程式用戶端密碼
     - `POWERBI_TENANT_ID`：Azure 租戶 ID
     - `POWERBI_WORKSPACE_ID`：PowerBI 工作區 ID
     - `POWERBI_REPORT_ID`：PowerBI 報表 ID
   - **應用程式設定：**
     - `FLASK_DEBUG`：是否啟用 Flask 除錯模式（建議生產環境設為 False）
     - `PORT`：應用程式監聽的埠號（預設 5000）
   - **管理後台設定：**
     - `ADMIN_USERNAME`：管理員帳號
     - `ADMIN_PASSWORD`：管理員密碼
     - `SECRET_KEY`：Flask session 密鑰，用於管理員登入

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
   - LINE Webhook 接收端點為 `/callback`
   - PowerBI 報表嵌入頁面：`http://localhost:5000/powerbi`
   - 服務狀態頁面：`http://localhost:5000/`
   - 管理後台登入頁面：`http://localhost:5000/admin/login`

2. **Docker 部署**  
   使用 Docker 部署，確保環境一致性：
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

   Docker 映像檔採用官方 Python 3.11-slim 為基礎，並實作以下安全最佳實踐：
   - 使用非 root 用戶運行應用程式
   - 移除不必要的套件以減少攻擊面
   - 適當設定檔案權限

## 測試與 CI/CD

1. **單元測試**  
   使用 pytest 執行所有單元測試，確保各模組功能正常：
   ```bash
   pytest
   ```
   
   若要產生覆蓋率報告：
   ```bash
   pytest --cov=src --cov-report=xml
   ```

   測試涵蓋：
   - LINE Bot 事件處理與簽名驗證
   - OpenAI 回覆生成服務
   - PowerBI API 整合功能
   - 設備監控與警報功能
   - 路由與安全性驗證

2. **持續整合與部署**  
   GitHub Actions 自動化流程包含以下階段：

   a. **安全性掃描**
   - Bandit：掃描 Python 程式碼中的安全漏洞
   - Safety：檢查相依套件中的已知漏洞

   b. **測試階段**
   - 執行 flake8 程式碼品質檢查
   - 執行 pytest 單元測試與覆蓋率分析
   - 上傳測試覆蓋率報告至 Codecov

   c. **建置與部署**
   - 使用 Docker Buildx 建置最佳化的容器映像檔
   - 推送映像檔至 Docker Hub
   - 實作映像檔快取以加速建置流程

   d. **部署後安全掃描**
   - 使用 Trivy 掃描容器映像檔中的漏洞
   - 將掃描結果上傳至 GitHub Security

## 使用指南

### LINE Bot 功能
以下是 LINE Bot 支援的主要命令與功能：

- **一般對話**：直接輸入問題，AI 將生成回應
- **PowerBI 報表**：輸入「powerbi」或「報表」查看數據報表
- **設備狀態查詢**：輸入「設備狀態」或「機台狀態」查看所有設備的概況
- **設備詳情查詢**：輸入「設備詳情 [設備名稱]」（例如「設備詳情 黏晶機A1」）查看特定設備的詳細資訊
- **語言設定**：輸入「language:語言代碼」更改語言（例如「language:en」切換至英文）
- **幫助選單**：輸入「help」或「幫助」查看功能選單
- **使用說明**：輸入「使用說明」或「指南」獲取詳細使用方法
- **關於**：輸入「關於」或「about」查看系統簡介

### 管理後台
管理後台提供以下功能：

- **儀表板**：顯示系統使用統計，包括總訊息數、用戶數、過去24小時活動等
- **系統狀態**：監控 OpenAI API、LINE Bot API 與 PowerBI 設定的連接狀態
- **近期對話**：查看最近活躍的用戶及其對話摘要
- **對話記錄**：查看特定用戶的完整對話歷史

訪問流程：
1. 訪問 `/admin/login` 路徑
2. 使用設定的管理員帳號密碼登入
3. 登入後可查看儀表板與系統統計資料
4. 點擊「查看對話」可檢視特定用戶的完整對話歷史

## 半導體設備監控功能

本系統包含完整的半導體設備監控功能，能夠自動偵測異常並及時通知相關人員：

1. **支援設備類型**
   - **黏晶機 (Die Bonder)**：監控溫度、壓力、Pick準確率、良率等指標
   - **打線機 (Wire Bonder)**：監控溫度、壓力、金絲張力、良率等指標
   - **切割機 (Dicer)**：監控溫度、轉速、冷卻水溫、切割精度、良率等指標

2. **監控機制**
   - 使用背景執行緒定期檢查（預設每 5 分鐘）設備狀態
   - 自動比較當前指標值與設定的閾值（最小值、最大值）
   - 根據偏差程度決定警報嚴重性（警告、嚴重、緊急）
   - 偵測長時間運行的作業，避免設備過度使用

3. **警報機制**
   - 針對不同嚴重程度的異常使用不同的視覺標識（⚠️🔴🚨）
   - 自動發送 LINE 通知給設備負責人或區域管理員
   - 記錄所有警報至資料庫，便於後續追蹤與分析
   - AI 增強的異常描述，提供可能的原因和建議解決方案

4. **使用者訂閱機制**
   - 使用者可訂閱特定設備的警報通知
   - 可設定接收通知的層級（例如只接收嚴重與緊急警報）
   - 根據使用者負責區域自動分配通知

5. **查詢指令**
   - **設備狀態**：顯示所有設備的狀態摘要，包括總數、正常數量、異常數量等
   - **設備詳情 [設備名稱]**：顯示特定設備的詳細資訊，包括最新監測指標、未解決警報、目前運行作業等

6. **資料庫結構**
   - **equipment**：儲存設備基本資訊（ID、名稱、類型、位置等）
   - **equipment_metrics**：儲存設備監測指標（類型、值、閾值等）
   - **equipment_operation_logs**：儲存設備運轉記錄（開始時間、結束時間、批次號等）
   - **alert_history**：儲存警報歷史（警報類型、嚴重程度、狀態等）
   - **user_equipment_subscriptions**：儲存使用者設備訂閱關係

7. **整合 OpenAI**
   - 使用 OpenAI 分析異常情況，生成對應的解釋與建議
   - 根據設備特性提供專業的建議，協助技術人員快速解決問題

## 資料分析功能

系統包含完整的資料分析模組，用於追蹤與分析使用者行為：

1. **事件追蹤**
   - 記錄各種系統事件，如訊息發送、報表查看、語言變更等
   - 支援使用者 ID 關聯，便於分析個別使用者行為

2. **每日統計**
   - 生成每日使用統計，包括訊息總數、獨立使用者數、平均回應時間等
   - 支援數據匯出，便於進一步分析與報表生成

3. **關鍵字分析**
   - 追蹤使用者訊息中的關鍵字，分析熱門話題與使用趨勢
   - 提供最常使用關鍵字的排行統計

4. **使用趨勢**
   - 生成使用趨勢數據，展示系統使用隨時間的變化
   - 分析用戶活躍度與留存率

5. **語言偏好分析**
   - 追蹤使用者的語言偏好設定
   - 分析不同語言使用者的分佈與行為差異

6. **設備監控分析**
   - 分析設備異常發生的頻率與模式
   - 追蹤各類指標的變化趨勢，預測可能的問題
   - 評估警報系統的有效性與準確度

## 安全性考量

本專案實作多層次的安全防護機制：

1. **API 安全**
   - 所有 API 金鑰與敏感資訊均通過環境變數管理，不直接寫入程式碼
   - 實作 LINE 簽名驗證，確保請求來源
   - PowerBI 整合使用 OAuth2 客戶端憑證流程，不暴露敏感資訊

2. **網頁安全**
   - 使用 Flask-Talisman 實作嚴格的內容安全政策(CSP)
   - 設定安全的 Cookie 屬性（HttpOnly, Secure）
   - 強制使用 HTTPS 連線

3. **輸入驗證與清理**
   - 使用 sanitize_input 函數處理使用者輸入，防止潛在的注入攻擊
   - 實作請求速率限制，防止暴力攻擊

4. **容器安全**
   - 使用非 root 用戶運行容器化應用
   - 移除不必要的套件以減少攻擊面
   - 最小化容器映像檔大小

5. **管理後台安全**
   - 實作安全的管理員認證系統
   - 使用 Flask session 管理登入狀態，設定適當的 Cookie 安全屬性
   - 管理員路由使用裝飾器進行權限檢查

6. **持續安全監控**
   - 在 CI/CD 流程中包含自動化安全掃描
   - 使用 Trivy 檢測容器映像檔中的漏洞

## 常見問題與疑難排解

1. **簽名驗證失敗**  
   - 確認 `LINE_CHANNEL_SECRET` 與 LINE 開發者控制台設定一致
   - 檢查是否使用了 ngrok 等工具進行本地測試，可能影響 HTTPS 標頭

2. **API 回覆異常**  
   - 驗證 `OPENAI_API_KEY` 是否正確，並檢查 API 調用是否超出使用配額
   - 查看應用程式日誌中的詳細錯誤訊息
   - 確認網路連線是否穩定，特別是在容器化環境中

3. **PowerBI 嵌入報表失敗**  
   - 檢查所有 PowerBI 相關環境變數是否正確配置
   - 確認 Azure AD 應用程式已被授予適當的 PowerBI API 權限
   - 檢查 PowerBI 工作區與報表 ID 是否正確
   - 確認報表有公開存取權限或適當的權限設置

4. **設備監控問題**
   - 確認資料庫中已正確初始化設備資料表與範例資料
   - 檢查設備排程器是否已正確啟動（可透過日誌確認）
   - 測試設備警報功能可使用 tests/test_equipment_alert.py 模擬異常

5. **Docker 部署問題**
   - 確認已正確設置所有必要的環境變數
   - 檢查容器日誌以獲取詳細的錯誤訊息
   - 確認 Docker 主機的網路設定允許容器連接外部 API（OpenAI、LINE、PowerBI）

6. **資料庫相關問題**
   - 確認 `data` 目錄具有適當的讀寫權限
   - 檢查資料庫連接錯誤日誌
   - 如需重置資料庫，可刪除 `data/conversations.db` 檔案，系統將自動重新建立所需表格

7. **管理後台登入問題**
   - 確認環境變數 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 和 `SECRET_KEY` 已正確設定
   - 檢查瀏覽器 Cookie 設定，確保未禁用
   - 若忘記密碼，可通過修改環境變數重新設定

## 開發與擴展指南

1. **新增功能**
   - 遵循模組化設計，將新功能放置在適當的模組中
   - 為新功能編寫單元測試，確保代碼覆蓋率
   - 更新 Documentary.md 與 README.md，記錄新功能的使用方法

2. **更新相依套件**
   - 定期更新 requirements.txt 中的套件版本
   - 使用 GitHub Actions 中的 Safety 檢查來監控相依套件的漏洞
   - 更新後執行完整測試，確保系統兼容性

3. **擴展 AI 功能**
   - 可在 main.py 中修改 OpenAI 的提示和參數，以優化回覆品質
   - 考慮實作頻率限制，避免過度使用 OpenAI API
   - 擴展支援的語言或增加特殊領域的知識庫

4. **增強設備監控功能**
   - 在 equipment_monitor.py 中添加更多設備類型與監控指標
   - 擴展異常偵測演算法，提高準確度
   - 開發更詳細的設備管理介面，支援設備新增與修改
   - 整合機器學習模型預測設備故障

5. **增強分析功能**
   - 在 analytics.py 中新增更多分析指標
   - 開發更豐富的數據視覺化展示
   - 考慮實作預測分析，識別使用趨勢與模式

6. **本地開發提示**
   - 設置 FLASK_DEBUG=True 以啟用熱重載與詳細錯誤訊息
   - 使用 ngrok 等工具為本地伺服器建立公開 URL，以便測試 LINE Webhook
   - 考慮設置開發環境專用的 .env.dev 檔案，避免影響生產設定
