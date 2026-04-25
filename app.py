import os
from flask import Flask, request, redirect
from dotenv import load_dotenv

from routes.auth_routes import register_auth_routes
from routes.admin_routes import register_admin_routes
from routes.webhook_routes import register_webhook_routes
from routes.setup_routes import register_setup_routes
from core.config_manager import load_settings

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")


@app.route("/healthz")
def healthz():
    return {"status": "ok", "service": "MedSafety Link"}, 200


@app.before_request
def check_setup():
    open_paths = {"/setup", "/setup/test_line", "/setup/test_google", "/setup/init_google", "/login", "/logout", "/callback", "/healthz"}

    if request.path.startswith("/static/"):
        return None

    if request.path in open_paths or request.path.startswith("/setup/test_line_to/"):
        return None

    s = load_settings()
    if not s.get("institutions"):
        return redirect("/setup")

    return None


register_auth_routes(app)
register_admin_routes(app)
register_webhook_routes(app)
register_setup_routes(app)
