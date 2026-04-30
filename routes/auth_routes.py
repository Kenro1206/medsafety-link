from flask import make_response, request, session, redirect, render_template
from core.config_manager import load_settings
from core.auth import is_system_admin_institution


def register_auth_routes(app):

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
                session["logged_in"] = True
                session["login_institution_id"] = institution_id
                session["institution_id"] = institution_id
                if is_system_admin_institution(institution_id):
                    session["system_admin_institution_id"] = institution_id
                    operated_id = request.cookies.get("last_operated_institution_id", "").strip()
                    if operated_id in institutions:
                        session["institution_id"] = operated_id
                response = make_response(redirect("/admin/dashboard"))
                if remember_institution:
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

        return render_template(
            "login.html",
            message=message,
            saved_institution_id=saved_institution_id,
            show_menu=False
        )

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")
