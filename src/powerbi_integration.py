import os
import requests
import logging

logger = logging.getLogger(__name__)

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
        logger.error(f"取得 access token 失敗：{response.text}")
        raise Exception("無法取得 PowerBI 存取權杖，請檢查憑證設定。")
    json_resp = response.json()
    access_token = json_resp.get("access_token")
    if not access_token:
        logger.error(f"回應中未包含 access_token：{json_resp}")
        raise Exception("PowerBI 回應中未包含 access_token")
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
        logger.error(f"取得 embed token 失敗：{response.text}")
        raise Exception("無法取得 PowerBI Embed Token")
    json_resp = response.json()
    embed_token = json_resp.get("token")
    if not embed_token:
        logger.error(f"回應中未包含 embed token：{json_resp}")
        raise Exception("PowerBI 回應中未包含 embed token")
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
