from flask import request, session, redirect, render_template
from core.auth import get_admin_password


def register_auth_routes(app):
    @app.route("/")
    def index():
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        message = ""

        if request.method == "POST":
            if request.form.get("password", "") == get_admin_password():
                session["logged_in"] = True
                return redirect("/admin/settings")
            message = "パスワードが違います。"

        return render_template("login.html", message=message)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")
