from flask import request, render_template, redirect

from core.auth import require_login
from core.config_manager import load_settings, save_settings
from core.utils import help_link
from services.line_service import test_line_connection, push_text
from services.sheets_service import (
    load_patients,
    save_patients,
    load_pending_users,
    save_pending_users,
    load_responses,
    get_latest_responses,
    get_system_mode,
    set_system_mode
)


def register_admin_routes(app):

    # =========================
    # 共通安全ラッパー
    # =========================
    def safe_call(func, default):
        try:
            return func()
        except Exception as e:
            print(f"[ERROR] {func.__name__}:", e)
            return default

    # =========================
    # 設定画面
    # =========================
    @app.route("/admin/settings")
    def admin_settings():
        auth = require_login()
        if auth:
            return auth

        s = load_settings()

        current_mode = safe_call(get_system_mode, "NORMAL")

        return render_template(
            "settings.html",
            title="設定",
            settings=s,
            current_mode=current_mode,
            help_link=help_link
        )

    @app.route("/admin/settings/save", methods=["POST"])
    def admin_settings_save():
        auth = require_login()
        if auth:
            return auth

        s = load_settings()

        s["hospital"]["name"] = request.form.get("hospital_name", "").strip()
        s["hospital"]["department"] = request.form.get("department", "").strip()
        s["hospital"]["phone"] = request.form.get("hospital_phone", "").strip()

        s["auth"]["admin_password"] = request.form.get("admin_password", "admin").strip()

        s["admins"]["line_user_ids"] = [
            x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()
        ]

        s["line"]["channel_access_token"] = request.form.get("line_token", "").strip()
        s["google"]["service_account_file"] = request.form.get("google_service_account_file", "").strip()
        s["google"]["spreadsheet_id"] = request.form.get("google_spreadsheet_id", "").strip()

        save_settings(s)

        return redirect("/admin/settings")

    # =========================
    # 患者登録
    # =========================
    @app.route("/admin/register")
    def admin_register():
        auth = require_login()
        if auth:
            return auth

        patients = safe_call(load_patients, [])
        pending = safe_call(load_pending_users, [])

        unlinked = [p for p in patients if not p.get("line_user_id", "").strip()]

        return render_template(
            "register.html",
            title="患者登録",
            pending_users=pending,
            patients=patients,
            unlinked_patients=unlinked
        )

    @app.route("/admin/link", methods=["POST"])
    def admin_link():
        auth = require_login()
        if auth:
            return auth

        patient_id = request.form.get("patient_id", "").strip()
        line_user_id = request.form.get("line_user_id", "").strip()

        patients = safe_call(load_patients, [])

        for p in patients:
            if p.get("patient_id") == patient_id:
                p["line_user_id"] = line_user_id

        safe_call(lambda: save_patients(patients), None)

        s = load_settings()
        push_text(line_user_id, s["messages"].get("registration_complete", "登録完了しました"))

        return redirect("/admin/register")

    # =========================
    # 回答一覧
    # =========================
    @app.route("/admin/responders")
    def admin_responders():
        auth = require_login()
        if auth:
            return auth

        patients = safe_call(load_patients, [])
        latest = safe_call(get_latest_responses, {})

        patient_map = {p.get("patient_id"): p for p in patients}

        s = load_settings()
        severe_codes = s.get("alerts", {}).get("severe_codes", [])

        responder_rows = []

        for pid, r in latest.items():
            p = patient_map.get(pid, {})

            responder_rows.append({
                "patient_id": pid,
                "name": p.get("name", ""),
                "phone": p.get("phone", ""),
                "timestamp": r.get("timestamp", ""),
                "answer_label": r.get("answer_label", ""),
                "answer_code": r.get("answer_code", ""),
                "is_severe": r.get("answer_code") in severe_codes
            })

        return render_template(
            "responders.html",
            title="回答一覧",
            responders=responder_rows,
            default_message=s.get("messages", {}).get("individual_default", "")
        )

    # =========================
    # 個別送信
    # =========================
    @app.route("/admin/responders/message", methods=["POST"])
    def admin_responders_message():
        auth = require_login()
        if auth:
            return auth

        patient_id = request.form.get("patient_id")
        message = request.form.get("message")

        patients = safe_call(load_patients, [])

        patient = next((p for p in patients if p.get("patient_id") == patient_id), None)

        if not patient:
            return "患者が見つかりません"

        line_user_id = patient.get("line_user_id")

        if not line_user_id:
            return "LINE未登録"

        push_text(line_user_id, message)

        return redirect("/admin/responders")

    # =========================
    # 一斉送信
    # =========================
    @app.route("/admin/broadcast")
    def admin_broadcast():
        auth = require_login()
        if auth:
            return auth

        s = load_settings()

        return render_template(
            "broadcast.html",
            title="一斉送信",
            default_message=s.get("messages", {}).get("broadcast_default", "")
        )

    @app.route("/admin/broadcast/send", methods=["POST"])
    def admin_broadcast_send():
        auth = require_login()
        if auth:
            return auth

        message = request.form.get("message")

        patients = safe_call(load_patients, [])

        for p in patients:
            uid = p.get("line_user_id")
            if uid:
                push_text(uid, message)

        return redirect("/admin/broadcast")

    # =========================
    # 未回答再送
    # =========================
    @app.route("/admin/remind")
    def admin_remind():
        auth = require_login()
        if auth:
            return auth

        s = load_settings()

        return render_template(
            "remind.html",
            title="未回答再送",
            default_message=s.get("messages", {}).get("remind_default", "")
        )

    @app.route("/admin/remind/send", methods=["POST"])
    def admin_remind_send():
        auth = require_login()
        if auth:
            return auth

        message = request.form.get("message")

        patients = safe_call(load_patients, [])
        responses = safe_call(load_responses, [])

        responded_ids = {r.get("patient_id") for r in responses}

        for p in patients:
            if p.get("patient_id") not in responded_ids:
                uid = p.get("line_user_id")
                if uid:
                    push_text(uid, message)

        return redirect("/admin/remind")

    # =========================
    # モード切替
    # =========================
    @app.route("/admin/mode", methods=["GET", "POST"])
    def admin_mode():
        auth = require_login()
        if auth:
            return auth

        if request.method == "POST":
            mode = request.form.get("mode", "NORMAL")
            safe_call(lambda: set_system_mode(mode), None)
            return redirect("/admin/mode")

        current_mode = safe_call(get_system_mode, "NORMAL")

        return render_template(
            "mode.html",
            title="モード切替",
            current_mode=current_mode
        )

    # =========================
    # LINEテスト
    # =========================
    @app.route("/admin/test_line")
    def admin_test_line():
        auth = require_login()
        if auth:
            return auth

        ok, msg = test_line_connection()

        return f"結果: {'成功' if ok else '失敗'}<br>{msg}"
