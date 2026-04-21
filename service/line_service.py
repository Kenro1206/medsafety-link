import requests
from core.config_manager import load_settings


def get_line_token():
    s = load_settings()
    return s.get("line", {}).get("channel_access_token", "").strip()


def push_text(to_user_id, text):
    token = get_line_token()
    if not token:
        return False, "LINEチャネルアクセストークン未設定"

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": to_user_id,
        "messages": [{"type": "text", "text": text}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if 200 <= res.status_code < 300:
            return True, res.text
        return False, res.text
    except Exception as e:
        return False, str(e)


def test_line_connection():
    s = load_settings()
    admin_ids = s.get("admins", {}).get("line_user_ids", [])
    if not admin_ids:
        return False, "管理者LINE ID が未設定です。"

    return push_text(admin_ids[0], "【MedSafety Link テスト】LINE接続確認です。")
