from flask import request

from core.institution_context import get_all_institutions, get_current_institution_id, use_institution
from core.config_manager import load_settings, save_settings
from core.time_utils import is_business_time, now_jst_iso
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


def get_event_text(event):
    event_type = event.get("type")
    if event_type == "message" and event.get("message", {}).get("type") == "text":
        return event.get("message", {}).get("text", "")

    if event_type == "postback":
        data = event.get("postback", {}).get("data", "")
        if data.startswith("answer="):
            return data.split("=", 1)[1]
        return data

    return ""


def find_patient_by_line_user_id(user_id):
    for institution_id in get_all_institutions():
        try:
            with use_institution(institution_id):
                patient = next((p for p in load_patients() if p.get("line_user_id") == user_id), None)
                if patient:
                    return institution_id, patient
        except Exception as e:
            print(f"[WEBHOOK INSTITUTION SKIP] {institution_id}: {e}")
    return None, None


def patient_auto_reply_text(mode, label):
    settings = load_settings()
    messages = settings.get("messages", {})
    institution = settings.get("institutions", {}).get(get_current_institution_id(), {})

    if mode == "DISASTER":
        return f"回答を受け付けました: {label}"

    if is_business_time(settings.get("business_hours", {})):
        return f"回答を受け付けました: {label}"

    phone = institution.get("phone", "").strip()
    phone_part = f"（電話番号: {phone}）" if phone else ""
    return messages.get("auto_reply_after_hours", "").replace("{phone_part}", phone_part)


def register_webhook_routes(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        body = request.get_json(force=True, silent=True) or {}

        for event in body.get("events", []):
            try:
                text = get_event_text(event)
                if not text:
                    continue

                user_id = event.get("source", {}).get("userId", "")
                reply_token = event.get("replyToken")
                institution_id, patient = find_patient_by_line_user_id(user_id)

                if not patient:
                    with use_institution(get_current_institution_id()):
                        pending = load_pending_users()
                        if not any(r.get("line_user_id") == user_id for r in pending):
                            pending.append({
                                "timestamp": now_jst_iso(),
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

                with use_institution(institution_id):
                    code, label = classify_answer(text)
                    mode = get_system_mode()
                    append_response(patient, user_id, mode, code, label)

                    if code in get_severe_codes():
                        notify_admin(patient, code, label)

                    if reply_token:
                        reply_text(reply_token, patient_auto_reply_text(mode, label))
            except Exception as e:
                print("[WEBHOOK ERROR]", e)

        return "OK", 200
