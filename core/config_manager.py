import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
PERSISTENT_DATA_DIR = "/var/data"


def _resolve_settings_path():
    configured_path = os.getenv("SETTINGS_PATH", "").strip()
    if configured_path:
        return configured_path

    persistent_path = os.path.join(PERSISTENT_DATA_DIR, "settings.json")
    if os.path.isdir(PERSISTENT_DATA_DIR):
        return persistent_path

    return DEFAULT_SETTINGS_PATH


SETTINGS_PATH = _resolve_settings_path()
AFTER_HOURS_MESSAGE = (
    "ご連絡ありがとうございます。現在は時間外のため、すぐに対応ができません。"
    "診療時間内に順次確認いたします。なお、緊急時や急を要する症状がある場合は、"
    "LINEではなく当院{phone_part}までお電話をして頂いたうえで、"
    "救急外来受診をご検討ください。"
)
OLD_AFTER_HOURS_MESSAGES = [
    "ご連絡ありがとうございます。現在は時間外のため、診療時間内に確認いたします。",
    (
        "ご連絡ありがとうございます。現在は時間外のため、すぐに対応ができません。"
        "診療時間内に順次確認いたします。なお、緊急の場合は当院{phone_part}までお電話をして頂いたうえで、"
        "救急外来受診をご検討ください。"
    ),
]


def _default_messages():
    return {
        "auto_reply_business": "ご連絡ありがとうございます。内容を確認し、必要に応じて対応いたします。",
        "auto_reply_after_hours": AFTER_HOURS_MESSAGE,
        "auto_reply_disaster": "ご連絡ありがとうございます。現在、災害対応モードで対応しております。",
        "broadcast_default": "【安否確認】現在の状況を返信してください。\n1. 無事\n2. 体調不良\n3. 薬・インスリンが不足\n4. 低血糖が心配\n5. 至急連絡希望",
        "remind_default": "【再送】安否確認への回答がまだ確認できていません。現在の状況を返信してください。",
        "individual_default": "状況を確認しました。必要なものがあればお知らせください。",
        "individual_templates": [
            "状況を確認しました。必要なものがあればお知らせください。",
            "ご連絡ありがとうございます。内容を確認し、必要に応じて担当者からご連絡します。",
            "緊急性が高い場合は、当院へお電話のうえ、救急外来受診をご検討ください。",
        ],
    }


def _default_safety_reply_options():
    return [
        {"label": "無事", "text": "1", "code": "SAFE"},
        {"label": "体調不良", "text": "2", "code": "SICK"},
        {"label": "薬・インスリン不足", "text": "3", "code": "INSULIN_OUT"},
        {"label": "低血糖が心配", "text": "4", "code": "HYPO"},
        {"label": "至急連絡希望", "text": "5", "code": "CALL"},
    ]


def get_message_presets():
    return {
        "t1dm": {
            "name": "1型糖尿病",
            "description": "インスリン、低血糖、連絡希望を重視する運用です。",
            "messages": {
                "broadcast_default": "【安否確認】現在の状況を返信してください。\n1. 無事\n2. 体調不良\n3. 薬・インスリンが不足\n4. 低血糖が心配\n5. 至急連絡希望",
                "remind_default": "【再送】安否確認への回答がまだ確認できていません。現在の状況を返信してください。",
                "individual_default": "状況を確認しました。インスリン、血糖値、補食などで困っていることがあればお知らせください。",
                "individual_templates": [
                    "状況を確認しました。インスリン、血糖値、補食などで困っていることがあればお知らせください。",
                    "低血糖症状がある場合は、可能であれば血糖測定と補食を行い、改善しない場合は電話でご連絡ください。",
                    "緊急性が高い場合は、LINEではなく当院へお電話のうえ、救急外来受診をご検討ください。",
                ],
            },
            "safety_reply_options": _default_safety_reply_options(),
        },
        "dialysis": {
            "name": "透析患者",
            "description": "透析可否、体調不良、シャントや水分・薬剤不足を重視する運用です。",
            "messages": {
                "broadcast_default": "【透析安否確認】現在の状況を返信してください。\n1. 無事\n2. 体調不良\n3. 透析に行けない可能性あり\n4. シャント・出血などが心配\n5. 至急連絡希望",
                "remind_default": "【再送】透析安否確認への回答がまだ確認できていません。現在の状況を返信してください。",
                "individual_default": "状況を確認しました。透析予定、体調、シャントの状態などで困っていることがあればお知らせください。",
                "individual_templates": [
                    "状況を確認しました。透析予定、体調、シャントの状態などで困っていることがあればお知らせください。",
                    "透析に来院できない可能性がある場合は、現在地と連絡可能な電話番号をお知らせください。",
                    "息苦しさ、胸痛、強い出血など緊急性が高い症状がある場合は、LINEではなく電話・救急外来をご検討ください。",
                ],
            },
            "safety_reply_options": [
                {"label": "無事", "text": "1", "code": "SAFE"},
                {"label": "体調不良", "text": "2", "code": "SICK"},
                {"label": "透析困難", "text": "3", "code": "DIALYSIS_DIFFICULT"},
                {"label": "シャント心配", "text": "4", "code": "SHUNT_CONCERN"},
                {"label": "至急連絡希望", "text": "5", "code": "CALL"},
            ],
        },
        "foot_care": {
            "name": "足病変",
            "description": "足の写真、感染徴候、受診相談を重視する運用です。",
            "messages": {
                "broadcast_default": "【足の状態確認】現在の状況を返信してください。写真も送信できます。\n1. 変化なし\n2. 痛み・赤みあり\n3. 傷・浸出液あり\n4. 発熱・悪化が心配\n5. 至急連絡希望",
                "remind_default": "【再送】足の状態確認への回答がまだ確認できていません。現在の状況を返信してください。必要に応じて写真も送信できます。",
                "individual_default": "足の状態を確認しました。可能であれば写真を追加で送信し、痛み・赤み・発熱の有無もお知らせください。",
                "individual_templates": [
                    "足の状態を確認しました。可能であれば写真を追加で送信し、痛み・赤み・発熱の有無もお知らせください。",
                    "傷が悪化している、赤みが広がる、発熱がある場合は、早めの受診をご検討ください。",
                    "緊急性が高い場合は、LINEではなく当院へお電話のうえ、救急外来受診をご検討ください。",
                ],
            },
            "safety_reply_options": [
                {"label": "変化なし", "text": "1", "code": "SAFE"},
                {"label": "痛み・赤み", "text": "2", "code": "FOOT_PAIN_REDNESS"},
                {"label": "傷・浸出液", "text": "3", "code": "FOOT_WOUND_DRAINAGE"},
                {"label": "発熱・悪化", "text": "4", "code": "FOOT_WORSE"},
                {"label": "至急連絡希望", "text": "5", "code": "CALL"},
            ],
        },
    }


def _default_institution():
    return {
        "name": "未設定",
        "department": "未設定",
        "phone": "",
        "contact": {"name": "", "email": ""},
        "password": "admin",
        "line": {"channel_access_token": "", "bot_user_id": ""},
        "google": {
            "service_account_file": "./service_account.json",
            "spreadsheet_id": "",
            "drive_folder_id": ""
        },
        "admins": {"line_user_ids": []},
        "message_profile": "t1dm",
        "messages": _default_messages(),
        "safety_reply_options": _default_safety_reply_options()
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
        "messages": _default_messages(),
        "safety_reply_options": _default_safety_reply_options(),
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


def _normalize_safety_reply_options(options):
    defaults = _default_safety_reply_options()
    normalized = []
    if not isinstance(options, list):
        options = []

    for index, fallback in enumerate(defaults):
        option = options[index] if index < len(options) and isinstance(options[index], dict) else {}
        normalized.append({
            "label": option.get("label") or fallback["label"],
            "text": str(option.get("text") or fallback["text"]),
            "code": (option.get("code") or fallback["code"]).strip().upper(),
        })

    return normalized


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

    messages = data.setdefault("messages", {})
    if messages.get("auto_reply_after_hours") in OLD_AFTER_HOURS_MESSAGES:
        messages["auto_reply_after_hours"] = AFTER_HOURS_MESSAGE

    for inst in data.get("institutions", {}).values():
        _merge_missing(inst, _default_institution())
        inst_messages = inst.setdefault("messages", {})
        if inst_messages.get("auto_reply_after_hours") in OLD_AFTER_HOURS_MESSAGES:
            inst_messages["auto_reply_after_hours"] = AFTER_HOURS_MESSAGE
        inst.setdefault("line", {}).setdefault("bot_user_id", "")
        inst["safety_reply_options"] = _normalize_safety_reply_options(inst.get("safety_reply_options"))

    data["safety_reply_options"] = _normalize_safety_reply_options(data.get("safety_reply_options"))

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
    settings_dir = os.path.dirname(SETTINGS_PATH)
    if settings_dir:
        os.makedirs(settings_dir, exist_ok=True)

    if os.path.exists(SETTINGS_PATH):
        backup_path = f"{SETTINGS_PATH}.backup"
        shutil.copy2(SETTINGS_PATH, backup_path)

    tmp_path = f"{SETTINGS_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, SETTINGS_PATH)


def get_settings_storage_status():
    return {
        "settings_path": SETTINGS_PATH,
        "default_settings_path": DEFAULT_SETTINGS_PATH,
        "persistent_data_dir": PERSISTENT_DATA_DIR,
        "persistent_data_dir_exists": os.path.isdir(PERSISTENT_DATA_DIR),
        "uses_persistent_path": SETTINGS_PATH.startswith(PERSISTENT_DATA_DIR + os.sep),
        "settings_exists": os.path.exists(SETTINGS_PATH),
        "backup_exists": os.path.exists(f"{SETTINGS_PATH}.backup"),
    }
