import requests
from core.config_manager import load_settings
from core.institution_context import get_current_institution


def get_line_token():
    institution = get_current_institution()
    if not institution:
        return ""
    return institution.get("line", {}).get("channel_access_token", "").strip()


def push_text(to_user_id, text):
    token = get_line_token()

    if not token:
        return False, "LINEチャネルアクセストークンが未設定です。"

    if not to_user_id:
        return False, "送信先LINE IDが未設定です。"

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {"to": to_user_id, "messages": [{"type": "text", "text": text}]}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if 200 <= res.status_code < 300:
            return True, "送信成功"
        return False, f"LINE送信失敗: status={res.status_code}, body={res.text}"
    except Exception as e:
        return False, f"LINE送信例外: {e}"


def reply_text(reply_token, text):
    token = get_line_token()

    if not token:
        return False, "LINEチャネルアクセストークンが未設定です。"

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if 200 <= res.status_code < 300:
            return True, "返信成功"
        return False, f"LINE返信失敗: status={res.status_code}, body={res.text}"
    except Exception as e:
        return False, f"LINE返信例外: {e}"


def test_line_connection():
    token = get_line_token()

    if not token:
        return False, "LINEチャネルアクセストークンが未設定です。"

    url = "https://api.line.me/v2/bot/info"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return True, f"LINE接続成功: {res.text}"
        return False, f"LINE接続失敗: status={res.status_code}, body={res.text}"
    except Exception as e:
        return False, f"LINE接続テスト例外: {e}"


def notify_admin(patient, code, label):
    institution = get_current_institution()
    admin_ids = institution.get("admins", {}).get("line_user_ids", []) if institution else []

    if not admin_ids:
        return False, "管理者LINE IDが未設定です。"

    msg = f"""【新着回答】
患者ID: {patient.get('patient_id', '')}
氏名: {patient.get('name', '')}
電話番号: {patient.get('phone', '')}
回答: {label}
コード: {code}"""

    results = []
    for admin_id in admin_ids:
        ok, result = push_text(admin_id, msg)
        results.append((admin_id, ok, result))

    return True, str(results)


def get_severe_codes():
    s = load_settings()
    return set(s.get("alerts", {}).get("severe_codes", []))
