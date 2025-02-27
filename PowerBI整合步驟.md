本文件說明如何在現有的 Flask 專案中整合 PowerBI，主要步驟包括：
	1.	環境設定與參數準備
在 Azure AD 中註冊應用以取得下列參數，並設定為環境變數：
	•	POWERBI_CLIENT_ID
	•	POWERBI_CLIENT_SECRET
	•	POWERBI_TENANT_ID
	•	POWERBI_WORKSPACE_ID
	•	POWERBI_REPORT_ID
	2.	建立 PowerBI 整合模組
使用 Python 撰寫一個模組，透過 OAuth2 客戶端憑證流程取得存取權杖，並呼叫 PowerBI API 生成嵌入所需的 Token 與 Embed URL。
	3.	修改 Flask 路由
新增 /powerbi 路由，呼叫上述模組取得 PowerBI 報表嵌入設定，再使用前端 PowerBI Client SDK 將報表嵌入頁面中。
	4.	建立 HTML 模板
在 templates 資料夾中建立 HTML 模板，利用 PowerBI Client SDK 將報表呈現在網頁中。

1. 環境設定

請在部署前確保設定下列環境變數，例如使用 .env 檔或直接在 Shell 中設定：

export POWERBI_CLIENT_ID="your_client_id"
export POWERBI_CLIENT_SECRET="your_client_secret"
export POWERBI_TENANT_ID="your_tenant_id"
export POWERBI_WORKSPACE_ID="your_workspace_id"
export POWERBI_REPORT_ID="your_report_id"

2. PowerBI 整合模組 (src/powerbi_integration.py)

建立一個新的 Python 檔案 src/powerbi_integration.py，內容如下：

import os
import requests

# 從環境變數讀取 PowerBI API 所需參數
POWERBI_CLIENT_ID = os.getenv("POWERBI_CLIENT_ID")
POWERBI_CLIENT_SECRET = os.getenv("POWERBI_CLIENT_SECRET")
POWERBI_TENANT_ID = os.getenv("POWERBI_TENANT_ID")
POWERBI_WORKSPACE_ID = os.getenv("POWERBI_WORKSPACE_ID")
POWERBI_REPORT_ID = os.getenv("POWERBI_REPORT_ID")

if not all([POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID, POWERBI_WORKSPACE_ID, POWERBI_REPORT_ID]):
    raise ValueError("請確保已設置所有 PowerBI 所需的環境變數：POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID, POWERBI_WORKSPACE_ID, POWERBI_REPORT_ID。")

def get_powerbi_access_token() -> str:
    """
    透過 OAuth2 客戶端憑證流程取得 PowerBI API 存取權杖
    """
    url = f"https://login.microsoftonline.com/{POWERBI_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': POWERBI_CLIENT_ID,
        'client_secret': POWERBI_CLIENT_SECRET,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise Exception("無法取得 PowerBI 存取權杖，請檢查憑證設定。")
    access_token = response.json().get("access_token")
    return access_token

def get_powerbi_embed_token(access_token: str) -> str:
    """
    呼叫 PowerBI API 產生報表的 Embed Token
    """
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{POWERBI_WORKSPACE_ID}/reports/{POWERBI_REPORT_ID}/GenerateToken"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {"accessLevel": "view"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception("無法取得 PowerBI Embed Token")
    embed_token = response.json().get("token")
    return embed_token

def get_powerbi_embed_config() -> dict:
    """
    組合 PowerBI 嵌入所需的設定，包含 embed URL 與 token
    """
    access_token = get_powerbi_access_token()
    embed_token = get_powerbi_embed_token(access_token)
    embed_url = f"https://app.powerbi.com/reportEmbed?reportId={POWERBI_REPORT_ID}&groupId={POWERBI_WORKSPACE_ID}"
    return {
        "embedUrl": embed_url,
        "accessToken": embed_token,
        "reportId": POWERBI_REPORT_ID,
        "workspaceId": POWERBI_WORKSPACE_ID
    }

3. 修改 Flask 路由

在原有的 Flask 專案中（例如 src/linebot_connect.py），新增一個 /powerbi 路由來展示 PowerBI 報表。修改後的範例如下：

from flask import Flask, request, abort, render_template
# 引入原有 LINE Bot 相關模組...
from src.powerbi_integration import get_powerbi_embed_config

app = Flask(__name__)

# ...原有 /callback 路由等

# 新增 /powerbi 路由，提供 PowerBI 報表嵌入頁面
@app.route("/powerbi")
def powerbi():
    try:
        config = get_powerbi_embed_config()
    except Exception as e:
        return f"Error: {str(e)}", 500
    return render_template("powerbi.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

4. 建立 HTML 模板 (templates/powerbi.html)

在專案根目錄下建立 templates 資料夾，並新增檔案 powerbi.html，內容如下：

<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>PowerBI 報表展示</title>
    <!-- 載入 PowerBI Client SDK -->
    <script src="https://cdn.powerbi.com/libs/powerbi-client/latest/powerbi.min.js"></script>
</head>
<body>
    <h2>PowerBI 報表展示</h2>
    <div id="reportContainer" style="height:800px;"></div>
    <script>
        // 取得後端傳入的嵌入設定
        var embedConfig = {
            type: 'report',
            tokenType: powerbi.models.TokenType.Embed,
            accessToken: "{{ config.accessToken }}",
            embedUrl: "{{ config.embedUrl }}",
            id: "{{ config.reportId }}",
            settings: {
                filterPaneEnabled: false,
                navContentPaneEnabled: true
            }
        };

        // 將報表嵌入到網頁中
        var reportContainer = document.getElementById('reportContainer');
        powerbi.embed(reportContainer, embedConfig);
    </script>
</body>
</html>

整合步驟總結
	1.	環境變數設定
設定 PowerBI 所需參數：
	•	POWERBI_CLIENT_ID
	•	POWERBI_CLIENT_SECRET
	•	POWERBI_TENANT_ID
	•	POWERBI_WORKSPACE_ID
	•	POWERBI_REPORT_ID
	2.	建立 PowerBI 整合模組
在 src/powerbi_integration.py 中撰寫取得存取權杖與生成 Embed Token 的功能。
	3.	新增 Flask 路由
修改專案（如 src/linebot_connect.py），新增 /powerbi 路由並利用 render_template 載入 powerbi.html 模板。
	4.	建立 HTML 模板
在 templates 資料夾中建立 powerbi.html，並使用 PowerBI Client SDK 將報表嵌入頁面中。

完成上述步驟後，啟動 Flask 專案，並透過瀏覽器存取 http://<your_host>:5000/powerbi，即可看到 PowerBI 報表嵌入展示的頁面。
