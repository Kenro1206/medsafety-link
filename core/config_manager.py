import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
SETTINGS_PATH = os.getenv("SETTINGS_PATH", DEFAULT_SETTINGS_PATH)
AFTER_HOURS_MESSAGE = (
    "ご連絡ありがとうございます。現在は時間外のため、すぐに対応ができません。"
    "診療時間内に順次確認いたします。なお、緊急の場合は当院{phone_part}までお電話をして頂いたうえで、"
    "救急外来受診をご検討ください。"
)


def _default_institution():
    return {
        "name": "未設定",
        "department": "未設定",
        "phone": "",
        "password": "admin",
        "line": {"channel_access_token": ""},
        "google": {
            "service_account_file": "./service_account.json",
            "spreadsheet_id": ""
        },
        "admins": {"line_user_ids": []}
    }


def get_default_settings():
    return {
        "institutions": {"default": _default_institution()},
        "default_institution_id": "default",
        "business_hours": {"start": "08:30", "end": "17:15"},
        "holidays": [],
        "alerts": {"severe_codes": ["CALL", "INSULIN_OUT", "HYPO"]},
        "system_admins": {"institution_ids": []},
        "rich_menu": {"normal_id": "", "disaster_id": ""},
        "messages": {
            "auto_reply_business": "ご連絡ありがとうございます。内容を確認し、必要に応じて対応いたします。",
            "auto_reply_after_hours": AFTER_HOURS_MESSAGE,
            "auto_reply_disaster": "ご連絡ありがとうございます。現在、災害対応モードで対応しております。",
            "broadcast_default": "【安否確認】現在の状況を返信してください。\n1. 無事\n2. 体調不良\n3. 薬・インスリンが不足\n4. 低血糖が心配\n5. 至急連絡希望",
            "remind_default": "【再送】安否確認への回答がまだ確認できていません。現在の状況を返信してください。",
            "individual_default": "状況を確認しました。必要なものがあればお知らせください。"
        },
        "setup": {"candidate_admin_line_ids": []},
        "default_created_at": datetime.now().isoformat()
    }


def _merge_missing(target, defaults):
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_missing(target[key], value)
    return target


def normalize_settings(data):
    defaults = get_default_settings()

    if "institutions" not in data:
        inst = _default_institution()
        inst["name"] = data.get("hospital", {}).get("name", inst["name"])
        inst["department"] = data.get("hospital", {}).get("department", inst["department"])
        inst["phone"] = data.get("hospital", {}).get("phone", "")
        inst["password"] = data.get("auth", {}).get("admin_password", inst["password"])
        inst["line"] = data.get("line", inst["line"])
        inst["google"] = data.get("google", inst["google"])
        inst["admins"] = data.get("admins", inst["admins"])
        data["institutions"] = {"default": inst}
        data["default_institution_id"] = "default"

    _merge_missing(data, defaults)

    old_after_hours = "ご連絡ありがとうございます。現在は時間外のため、診療時間内に確認いたします。"
    messages = data.setdefault("messages", {})
    if messages.get("auto_reply_after_hours") == old_after_hours:
        messages["auto_reply_after_hours"] = AFTER_HOURS_MESSAGE

    for inst in data.get("institutions", {}).values():
        _merge_missing(inst, _default_institution())

    default_id = data.get("default_institution_id")
    if default_id not in data.get("institutions", {}):
        data["default_institution_id"] = next(iter(data["institutions"]), "default")

    return data


def ensure_settings():
    if not os.path.exists(SETTINGS_PATH):
        settings_dir = os.path.dirname(SETTINGS_PATH)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)

        if SETTINGS_PATH != DEFAULT_SETTINGS_PATH and os.path.exists(DEFAULT_SETTINGS_PATH):
            with open(DEFAULT_SETTINGS_PATH, "r", encoding="utf-8") as src:
                data = json.load(src)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(normalize_settings(data), f, ensure_ascii=False, indent=2)
            return

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(get_default_settings(), f, ensure_ascii=False, indent=2)


def load_settings():
    ensure_settings()
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return normalize_settings(data)


def save_settings(data):
    data = normalize_settings(data)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
