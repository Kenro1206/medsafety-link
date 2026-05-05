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

DEFAULT_ANSWER_CODES = ["SAFE", "SICK", "INSULIN_OUT", "HYPO", "CALL"]


def get_configured_answer_map():
    settings = load_settings()
    institution = settings.get("institutions", {}).get(get_current_institution_id(), {})
    options = institution.get("safety_reply_options") or settings.get("safety_reply_options", [])
    answer_map = {}

    for index, option in enumerate(options[:5]):
        number = str(index + 1)
        code = (option.get("code") or DEFAULT_ANSWER_CODES[index]).strip().upper()
        label = (option.get("label") or ANSWER_MAP.get(number, (code, number))[1]).strip()
        text_value = str(option.get("text") or number).strip()

        answer_map[number] = (code, label)
        if text_value:
            answer_map[text_value] = (code, label)
        if label:
            answer_map[label] = (code, label)

    return answer_map


def classify_answer(text):
    value = (text or "").strip()
    lower = value.lower()
    configured_map = get_configured_answer_map()

    if value in configured_map:
        return configured_map[value]

    for key, answer in configured_map.items():
        if key and not key.isdigit() and key in value:
            return answer

    for key, answer in ANSWER_MAP.items():
        if key.isdigit() and value == key:
            return answer
        if not key.isdigit() and (key in value or key in lower):
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


def find_institution_by_destination(destination):
    if not destination:
        return None
    for institution_id, institution in get_all_institutions().items():
        if institution.get("line", {}).get("bot_user_id", "") == destination:
            return institution_id
    return None


def patient_auto_reply_text(mode, label):
    settings = load_settings()
    institution = settings.get("institutions", {}).get(get_current_institution_id(), {})
    messages = institution.get("messages", {}) or settings.get("messages", {})

    if mode == "DISASTER":
        return f"回答を受け付けました: {label}"

    if is_business_time(settings.get("business_hours", {}), settings.get("holidays", [])):
        return f"回答を受け付けました: {label}"

    phone = institution.get("phone", "").strip()
    phone_part = f"（電話番号: {phone}）" if phone else ""
    return messages.get("auto_reply_after_hours", "").replace("{phone_part}", phone_part)


def record_webhook_status(status):
    settings = load_settings()
    history = settings.setdefault("webhook_status", {}).setdefault("recent", [])
    history.insert(0, status)
    del history[20:]
    save_settings(settings)


def register_webhook_routes(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        body = request.get_json(force=True, silent=True) or {}

        for event in body.get("events", []):
            status = {
                "timestamp": now_jst_iso(),
                "destination": body.get("destination", ""),
                "event_type": event.get("type", ""),
                "message_type": event.get("message", {}).get("type", ""),
                "line_user_id": event.get("source", {}).get("userId", ""),
                "text": "",
                "message_id": event.get("message", {}).get("id", ""),
                "destination_institution_id": "",
                "matched_institution_id": "",
                "patient_id": "",
                "action": "",
                "reply_result": "",
                "error": "",
            }
            try:
                message_type = event.get("message", {}).get("type", "")
                message_id = event.get("message", {}).get("id", "")
                text = get_event_text(event)
                if message_type == "image":
                    text = "画像メッセージ"
                status["text"] = text[:80] if text else ""
                if not text:
                    status["action"] = "ignored_non_text_event"
                    record_webhook_status(status)
                    continue

                user_id = event.get("source", {}).get("userId", "")
                reply_token = event.get("replyToken")
                destination_institution_id = find_institution_by_destination(body.get("destination", ""))
                institution_id, patient = find_patient_by_line_user_id(user_id)
                status["destination_institution_id"] = destination_institution_id or ""
                status["matched_institution_id"] = institution_id or ""

                if not patient:
                    target_institution_id = destination_institution_id or get_current_institution_id()
                    status["matched_institution_id"] = target_institution_id or ""
                    with use_institution(target_institution_id):
                        pending = load_pending_users()
                        if not any(r.get("line_user_id") == user_id for r in pending):
                            pending.append({
                                "timestamp": now_jst_iso(),
                                "line_user_id": user_id,
                                "patient_name": "",
                                "display_text": "画像メッセージを受信しました" if message_type == "image" else text
                            })
                            save_pending_users(pending)
                            status["action"] = "saved_pending_user"
                        else:
                            status["action"] = "pending_user_already_exists"

                        s = load_settings()
                        candidates = s.setdefault("setup", {}).setdefault("candidate_admin_line_ids", [])
                        if user_id and user_id not in candidates:
                            candidates.append(user_id)
                            save_settings(s)

                        if reply_token:
                            ok, result = reply_text(reply_token, "メッセージを受け付けました。管理者が登録確認を行います。")
                            status["reply_result"] = f"{ok}: {result}"
                    record_webhook_status(status)
                    continue

                with use_institution(institution_id):
                    status["patient_id"] = patient.get("patient_id", "")
                    mode = get_system_mode()
                    if message_type == "image":
                        code, label = "PHOTO", "画像を受信しました"
                        append_response(patient, user_id, mode, code, label, media_id=message_id)
                    else:
                        code, label = classify_answer(text)
                        append_response(patient, user_id, mode, code, label)
                    status["action"] = f"saved_response:{code}"

                    if code in get_severe_codes():
                        notify_admin(patient, code, label)

                    if reply_token:
                        reply_message = (
                            "画像を受け付けました。担当者が確認します。"
                            if message_type == "image"
                            else patient_auto_reply_text(mode, label)
                        )
                        ok, result = reply_text(reply_token, reply_message)
                        status["reply_result"] = f"{ok}: {result}"
                record_webhook_status(status)
            except Exception as e:
                status["error"] = str(e)
                record_webhook_status(status)
                print("[WEBHOOK ERROR]", e)

        return "OK", 200
