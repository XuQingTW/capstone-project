# client.py
import requests

def send_json():
    url = 'https://127.0.0.1:443/resolvealarms'
    payload = {
        "error_id": 107,  # 暫時依照error_id 做查詢
        "resolved_by": "user001",
        "resolution_notes": ""  # 可無
    }

    try:
        resp = requests.post(url, json=payload, timeout=5, verify=False)
        resp.raise_for_status()
    except requests.RequestException as e:
        print("Request failed:", e)
        return

if __name__ == '__main__':
    send_json()
