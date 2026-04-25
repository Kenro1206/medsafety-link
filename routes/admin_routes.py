import re
from flask import request, render_template, redirect, session
from core.auth import require_login
from core.config_manager import load_settings, save_settings
from core.institution_context import get_current_institution_id, get_current_institution
from core.utils import help_link
from services.line_service import push_text
from services.sheets_service import (
    get_latest_responses,
    get_system_mode,
    load_patients,
    load_pending_users,
    save_patients,
    save_pending_users,
    set_latest_response_handled,
    set_system_mode,
)


def register_admin_routes(app):

    def safe_call(func, default):
        try:
            return func()
        except Exception as e:
            print("[ERROR]", e)
            return default

    def default_message(key):
        return load_settings().get("messages", {}).get(key, "")

    @app.route("/admin/settings")
    def admin_settings():
        auth = require_login()
        if auth:
            return auth

        return render_template(
            "settings.html",
            title="設定",
            institution_id=get_current_institution_id(),
            institution=get_current_institution(),
            current_mode=safe_call(get_system_mode, "NORMAL"),
            help_link=help_link
        )

    @app.route("/admin/settings/save", methods=["POST"])
    def admin_settings_save():
        auth = require_login()
        if auth:
            return auth

        institution_id = get_current_institution_id()
        s = load_settings()
        inst = s["institutions"][institution_id]

        inst["name"] = request.form.get("hospital_name", "").strip()
        inst["department"] = request.form.get("department", "").strip()
        inst["phone"] = request.form.get("hospital_phone", "").strip()
        inst["password"] = request.form.get("password", "").strip() or inst.get("password", "admin")
        inst["line"]["channel_access_token"] = request.form.get("line_token", "").strip()
        inst["google"]["spreadsheet_id"] = request.form.get("spreadsheet_id", "").strip()
        inst["admins"]["line_user_ids"] = [x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()]
        save_settings(s)
        return redirect("/admin/settings")

    @app.route("/admin/institutions", methods=["GET", "POST"])
    def institutions():
        auth = require_login()
        if auth:
            return auth

        s = load_settings()
        message = ""
        error_message = ""

        if request.method == "POST":
            action = request.form.get("action", "").strip()
            try:
                if action == "create":
                    institution_id = request.form.get("institution_id", "").strip()
                    if not re.fullmatch(r"[A-Za-z0-9_-]{3,40}", institution_id or ""):
                        raise ValueError("施設IDは3〜40文字の半角英数字、ハイフン、アンダースコアで入力してください。")
                    if institution_id in s.get("institutions", {}):
                        raise ValueError("この施設IDはすでに登録されています。")

                    s.setdefault("institutions", {})[institution_id] = {
                        "name": request.form.get("name", "").strip() or institution_id,
                        "department": request.form.get("department", "").strip(),
                        "phone": "",
                        "password": request.form.get("password", "").strip() or "admin",
                        "line": {"channel_access_token": ""},
                        "google": {"service_account_file": "./service_account.json", "spreadsheet_id": ""},
                        "admins": {"line_user_ids": []}
                    }
                    message = "施設を追加しました。"

                elif action == "update":
                    institution_id = request.form.get("institution_id", "").strip()
                    inst = s.get("institutions", {}).get(institution_id)
                    if not inst:
                        raise ValueError("施設が見つかりません。")
                    inst["name"] = request.form.get("name", "").strip() or inst.get("name", institution_id)
                    inst["department"] = request.form.get("department", "").strip()
                    password = request.form.get("password", "").strip()
                    if password:
                        inst["password"] = password
                    message = "施設情報を更新しました。"

                elif action == "switch":
                    institution_id = request.form.get("institution_id", "").strip()
                    if institution_id not in s.get("institutions", {}):
                        raise ValueError("施設が見つかりません。")
                    session["institution_id"] = institution_id
                    s["default_institution_id"] = institution_id
                    message = "操作対象の施設を切り替えました。"

                else:
                    raise ValueError("不明な操作です。")

                save_settings(s)
                s = load_settings()
            except Exception as e:
                error_message = str(e)

        return render_template(
            "institutions.html",
            title="施設ID管理",
            institutions=s.get("institutions", {}),
            current_institution_id=get_current_institution_id(),
            message=message,
            error_message=error_message,
        )

    @app.route("/admin/register", methods=["GET", "POST"])
    def register_patients():
        auth = require_login()
        if auth:
            return auth

        message = ""
        error_message = ""
        if request.method == "POST":
            try:
                patient_id = request.form.get("patient_id", "").strip()
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                line_user_id = request.form.get("line_user_id", "").strip()
                if not patient_id or not name:
                    raise ValueError("患者IDと氏名は必須です。")
                patients = load_patients()
                existing = next((p for p in patients if p.get("patient_id") == patient_id), None)
                if existing:
                    existing.update({"name": name, "phone": phone, "line_user_id": line_user_id})
                    message = "患者情報を更新しました。"
                else:
                    patients.append({"patient_id": patient_id, "name": name, "phone": phone, "line_user_id": line_user_id})
                    message = "患者を登録しました。"
                save_patients(patients)
            except Exception as e:
                error_message = f"保存エラー: {e}"

        patients = safe_call(load_patients, [])
        pending_users = safe_call(load_pending_users, [])
        unlinked_patients = [p for p in patients if not p.get("line_user_id")]
        return render_template("register.html", title="患者登録", patients=patients, pending_users=pending_users, unlinked_patients=unlinked_patients, message=message, error_message=error_message)

    @app.route("/admin/link", methods=["POST"])
    def link_patient():
        auth = require_login()
        if auth:
            return auth

        line_user_id = request.form.get("line_user_id", "").strip()
        patient_id = request.form.get("patient_id", "").strip()
        patients = load_patients()
        for patient in patients:
            if patient.get("patient_id") == patient_id:
                patient["line_user_id"] = line_user_id
        save_patients(patients)
        pending = [r for r in load_pending_users() if r.get("line_user_id") != line_user_id]
        save_pending_users(pending)
        return redirect("/admin/register")

    @app.route("/admin/responders")
    def responders():
        auth = require_login()
        if auth:
            return auth

        patients = safe_call(load_patients, [])
        latest = safe_call(get_latest_responses, {})
        severe = set(load_settings().get("alerts", {}).get("severe_codes", []))
        rows = []
        for patient in patients:
            response = latest.get(patient.get("patient_id", ""), {})
            code = response.get("code", "")
            handled = str(response.get("handled", "")).upper() in ["TRUE", "済", "DONE", "1"]
            row_class = "safe-row"
            if code in severe and not handled:
                row_class = "severe"
            elif code and not handled:
                row_class = "yellow"
            rows.append({
                "patient_id": patient.get("patient_id", ""),
                "name": patient.get("name", ""),
                "phone": patient.get("phone", ""),
                "timestamp": response.get("timestamp", "未回答"),
                "answer_code": code or "NO_RESPONSE",
                "answer_label": response.get("label", "未回答"),
                "is_handled": handled,
                "row_class": row_class,
            })
        return render_template("responders.html", title="回答一覧", responders=rows)

    @app.route("/admin/responders/handle", methods=["POST"])
    def handle_responder():
        auth = require_login()
        if auth:
            return auth
        set_latest_response_handled(request.form.get("patient_id", "").strip(), True)
        return redirect("/admin/responders")

    @app.route("/admin/responders/unhandle", methods=["POST"])
    def unhandle_responder():
        auth = require_login()
        if auth:
            return auth
        set_latest_response_handled(request.form.get("patient_id", "").strip(), False)
        return redirect("/admin/responders")

    @app.route("/admin/broadcast")
    def broadcast():
        auth = require_login()
        if auth:
            return auth
        return render_template("broadcast.html", title="一斉送信", default_message=default_message("broadcast_default"))

    @app.route("/admin/broadcast/send", methods=["POST"])
    def broadcast_send():
        auth = require_login()
        if auth:
            return auth
        message = request.form.get("message", "").strip()
        return render_template("broadcast_result.html", title="一斉送信結果", **send_to_patients(load_patients(), message))

    @app.route("/admin/remind")
    def remind():
        auth = require_login()
        if auth:
            return auth
        return render_template("remind.html", title="未回答再送", default_message=default_message("remind_default"))

    @app.route("/admin/remind/send", methods=["POST"])
    def remind_send():
        auth = require_login()
        if auth:
            return auth
        message = request.form.get("message", "").strip()
        latest = get_latest_responses()
        targets = [p for p in load_patients() if p.get("line_user_id") and p.get("patient_id") not in latest]
        return render_template("broadcast_result.html", title="再送結果", **send_to_patients(targets, message))

    @app.route("/admin/mode", methods=["GET", "POST"])
    def mode():
        auth = require_login()
        if auth:
            return auth
        if request.method == "POST":
            set_system_mode(request.form.get("mode", "NORMAL"))
            return redirect("/admin/mode")
        return render_template("mode.html", title="モード切替", current_mode=safe_call(get_system_mode, "NORMAL"))

    @app.route("/admin/help/<topic>")
    def help_page(topic):
        auth = require_login()
        if auth:
            return auth
        body = {
            "settings": "LINEチャネルアクセストークン、GoogleスプレッドシートID、管理者LINE IDを設定します。",
            "register": "未登録ユーザーのLINE user_idを患者マスタへ紐付けます。",
            "responders": "最新回答、緊急度、対応状況を確認します。",
        }.get(topic, "ヘルプは準備中です。")
        return render_template("help.html", title="ヘルプ", body=body)

    def send_to_patients(patients, message):
        results = []
        success = 0
        fail = 0
        for patient in patients:
            if not patient.get("line_user_id"):
                continue
            ok, detail = push_text(patient.get("line_user_id"), message)
            success += 1 if ok else 0
            fail += 0 if ok else 1
            results.append({"patient_id": patient.get("patient_id", ""), "name": patient.get("name", ""), "ok": ok, "detail": detail})
        return {"success": success, "fail": fail, "results": results}
