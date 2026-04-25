from datetime import datetime
from flask import request

from core.config_manager import load_settings, save_settings
from services.line_service import get_severe_codes, notify_admin, reply_text
from services.sheets_service import append_response, load_patients, load_pending_users, save_pending_users, get_system_mode

ANSWER_MAP = {
    "1": ("SAFE", "無事"),
    "2": ("SICK", "体調不良"),
    "3": ("INSULIN_OUT", "薬・インスリン不足"),
    "4": ("HYPO", "低血糖が心配"),
    "5": ("CALL", "至急連絡希望"),
    "無事": ("SAFE", "無事"),
    "体調不良": ("SICK", "体調不良"),
    "薬": ("INSULIN_OUT", "薬・インスリン不足"),
    "インスリン": ("INSULIN_OUT", "薬・インスリン不足"),
    "低血糖": ("HYPO", "低血糖が心配"),
    "連絡": ("CALL", "至急連絡希望"),
    "call": ("CALL", "至急連絡希望"),
}


def classify_answer(text):
    value = (text or "").strip()
    lower = value.lower()
    for key, answer in ANSWER_MAP.items():
        if key in value or key in lower:
            return answer
    return "FREE_TEXT", value[:80] if value else "自由記述"


def register_webhook_routes(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        body = request.get_json(force=True, silent=True) or {}

        for event in body.get("events", []):
            try:
                if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
                    continue

                user_id = event.get("source", {}).get("userId", "")
                reply_token = event.get("replyToken")
                text = event.get("message", {}).get("text", "")
                patients = load_patients()
                patient = next((p for p in patients if p.get("line_user_id") == user_id), None)

                if not patient:
                    pending = load_pending_users()
                    if not any(r.get("line_user_id") == user_id for r in pending):
                        pending.append({
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "line_user_id": user_id,
                            "patient_name": "",
                            "display_text": text
                        })
                        save_pending_users(pending)

                    s = load_settings()
                    candidates = s.setdefault("setup", {}).setdefault("candidate_admin_line_ids", [])
                    if user_id and user_id not in candidates:
                        candidates.append(user_id)
                        save_settings(s)

                    if reply_token:
                        reply_text(reply_token, "メッセージを受け付けました。管理者が登録確認を行います。")
                    continue

                code, label = classify_answer(text)
                mode = get_system_mode()
                append_response(patient, user_id, mode, code, label)

                if code in get_severe_codes():
                    notify_admin(patient, code, label)

                if reply_token:
                    reply_text(reply_token, f"回答を受け付けました: {label}")
            except Exception as e:
                print("[WEBHOOK ERROR]", e)

        return "OK", 200
