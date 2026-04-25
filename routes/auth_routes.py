from flask import request, session, redirect, render_template
from core.config_manager import load_settings


def register_auth_routes(app):

    @app.route("/")
    def index():
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        message = ""

        if request.method == "POST":
            institution_id = request.form.get("institution_id", "").strip()
            password = request.form.get("password", "").strip()

            s = load_settings()
            institutions = s.get("institutions", {})

            institution = institutions.get(institution_id)

            if not institution:
                message = "施設IDが見つかりません。"
            elif password != institution.get("password", ""):
                message = "パスワードが違います。"
            else:
                session["logged_in"] = True
                session["institution_id"] = institution_id
                return redirect("/admin/settings")

        return render_template(
            "login.html",
            message=message,
            show_menu=False
        )

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")
