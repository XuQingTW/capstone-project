以下提供一個完整的範例，示範如何在現有的 Flask 專案中整合 PowerBI。基本流程如下：
	1.	申請與設定 PowerBI API 所需參數
	•	在 Azure AD 中註冊應用，取得 client_id、client_secret 與 tenant_id。
	•	在 PowerBI 中準備好要嵌入的報表，記錄其 workspace（group）ID 及 report ID。
	•	將上述參數設定為環境變數：
	•	POWERBI_CLIENT_ID
	•	POWERBI_CLIENT_SECRET
	•	POWERBI_TENANT_ID
	•	POWERBI_WORKSPACE_ID
	•	POWERBI_REPORT_ID
	2.	撰寫 PowerBI 整合模組
使用 Python 的 requests 呼叫 Microsoft 的 OAuth2 服務取得存取權杖，再進一步呼叫 PowerBI API 產生嵌入用的 token 與 URL。
	3.	建立 PowerBI 展示頁面
在 Flask 中新增一個路由（例如 /powerbi），透過剛剛撰寫的模組取得 embed token 與 embed URL，並利用 PowerBI Client JavaScript SDK 將報表嵌入頁面中。

下面提供完整的程式碼範例：

1. 新增模組：src/powerbi_integration.py

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

2. 修改 Flask 專案，新增 PowerBI 路由
在原有的 src/linebot_connect.py 中（或依需求另外建立一個模組），新增一個 /powerbi 路由。
此範例使用 Flask 的 render_template，需在專案根目錄建立 templates 資料夾，並新增 HTML 模板檔案。

修改後的部分範例如下：

# 其他引用保持不變
from flask import Flask, request, abort, render_template
# 新增 PowerBI 模組引用
from src.powerbi_integration import get_powerbi_embed_config

app = Flask(__name__)

# 原有 /callback 路由等保留
# ...

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

3. 建立 HTML 模板：templates/powerbi.html

建立一個新的資料夾 templates，並在其中建立檔案 powerbi.html。內容如下：

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

整合步驟說明：
	1.	環境變數設定
請在部署前設定以下環境變數（例如透過 .env 檔案或直接在 Shell 中設定）：
	•	POWERBI_CLIENT_ID
	•	POWERBI_CLIENT_SECRET
	•	POWERBI_TENANT_ID
	•	POWERBI_WORKSPACE_ID
	•	POWERBI_REPORT_ID
	2.	安裝相依套件
若尚未安裝 requests、Flask 等相依套件，可執行：

pip install flask requests


	3.	啟動專案
執行修改後的 Flask 專案：

python src/linebot_connect.py

確認 /powerbi 路徑能正確載入 PowerBI 報表。

此範例展示如何利用 PowerBI API 取得嵌入用 token 與 URL，並在 Flask 應用中建立報表展示頁面。根據實際需求，你可能還需要調整權限設定或加入前端更多互動功能。

以上即為將 PowerBI 整合到你現有專案中的完整實作範例。