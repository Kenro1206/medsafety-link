import copy
import re

from flask import make_response, request, session, redirect, render_template
from core.config_manager import load_settings, save_settings
from core.auth import FACILITY_MANAGER_LOGIN_ID, is_system_admin_institution


def register_auth_routes(app):
    def start_session(institution_id):
        session["logged_in"] = True
        session["login_institution_id"] = institution_id
        session["institution_id"] = institution_id
        if is_system_admin_institution(institution_id):
            session["system_admin_institution_id"] = institution_id

    def remember_institution_cookie(response, institution_id, remember=True):
        if remember:
            response.set_cookie(
                "last_institution_id",
                institution_id,
                max_age=60 * 60 * 24 * 180,
                httponly=True,
                samesite="Lax",
                secure=request.is_secure,
            )
        else:
            response.delete_cookie("last_institution_id")
        return response

    @app.route("/")
    def index():
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        message = ""
        saved_institution_id = request.cookies.get("last_institution_id", "").strip()

        if request.method == "POST":
            institution_id = request.form.get("institution_id", "").strip()
            password = request.form.get("password", "").strip()
            remember_institution = request.form.get("remember_institution") == "on"
            saved_institution_id = institution_id

            s = load_settings()
            institutions = s.get("institutions", {})

            institution = institutions.get(institution_id)

            if not institution:
                message = "施設IDが見つかりません。"
            elif password != institution.get("password", ""):
                message = "パスワードが違います。"
            else:
                start_session(institution_id)
                if is_system_admin_institution(institution_id):
                    operated_id = request.cookies.get("last_operated_institution_id", "").strip()
                    if institution_id != FACILITY_MANAGER_LOGIN_ID and operated_id in institutions:
                        session["institution_id"] = operated_id
                response = make_response(redirect("/admin/dashboard"))
                return remember_institution_cookie(response, institution_id, remember_institution)

        return render_template(
            "login.html",
            message=message,
            saved_institution_id=saved_institution_id,
            show_menu=False
        )

    @app.route("/facility/register", methods=["GET", "POST"])
    def register_facility():
        message = ""
        if request.method == "POST":
            institution_id = request.form.get("institution_id", "").strip()
            name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            password = request.form.get("password", "").strip()
            password_confirm = request.form.get("password_confirm", "").strip()

            try:
                if not re.fullmatch(r"[A-Za-z0-9_-]{3,40}", institution_id or ""):
                    raise ValueError("施設IDは3〜40文字の半角英数字、ハイフン、アンダースコアで入力してください。")
                if not name:
                    raise ValueError("施設名を入力してください。")
                if not password:
                    raise ValueError("パスワードを入力してください。")
                if password != password_confirm:
                    raise ValueError("確認用パスワードが一致しません。")

                settings = load_settings()
                if institution_id in settings.get("institutions", {}):
                    raise ValueError("この施設IDはすでに登録されています。")

                settings.setdefault("institutions", {})[institution_id] = {
                    "name": name,
                    "department": department,
                    "phone": "",
                    "password": password,
                    "line": {"channel_access_token": "", "bot_user_id": ""},
                    "google": {"service_account_file": "./service_account.json", "spreadsheet_id": ""},
                    "admins": {"line_user_ids": []},
                    "messages": copy.deepcopy(settings.get("messages", {})),
                    "safety_reply_options": copy.deepcopy(settings.get("safety_reply_options", [])),
                }
                save_settings(settings)
                start_session(institution_id)
                response = make_response(redirect(f"/admin/settings?active_institution_id={institution_id}"))
                return remember_institution_cookie(response, institution_id, True)
            except Exception as e:
                message = str(e)

        return render_template("facility_register.html", title="新規施設登録", message=message, show_menu=False)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")
