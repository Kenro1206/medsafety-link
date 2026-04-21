import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")


def get_default_settings():
    return {
        "hospital": {
            "name": "未設定",
            "department": "未設定",
            "phone": ""
        },
        "admins": {
            "line_user_ids": []
        },
        "auth": {
            "admin_password": "admin"
        },
        "line": {
            "channel_access_token": ""
        },
        "google": {
            "service_account_file": "./service_account.json",
            "spreadsheet_id": ""
        },
        "business_hours": {
            "start": "08:30",
            "end": "17:15"
        },
        "holidays": [],
        "alerts": {
            "severe_codes": ["CALL", "INSULIN_OUT", "HYPO"]
        },
        "rich_menu": {
            "normal_id": "",
            "disaster_id": ""
        },
        "messages": {
            "auto_reply_business": "ご連絡ありがとうございます。内容を確認し、必要に応じて対応いたします。",
            "auto_reply_after_hours": "ご連絡ありがとうございます。現在は時間外のため、診療時間内に確認いたします。",
            "auto_reply_disaster": "ご連絡ありがとうございます。現在、災害対応モードで対応しております。",
            "broadcast_default": "【安否確認】現在の状況を返信してください。",
            "remind_default": "【再送】未回答のため再送します。",
            "individual_default": "状況を確認しました。必要なものがあればお知らせください。"
        },
        "default_created_at": datetime.now().isoformat()
    }


def ensure_settings():
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(get_default_settings(), f, ensure_ascii=False, indent=2)


def load_settings():
    ensure_settings()
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
