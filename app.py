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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret")


@app.before_request
def check_setup():
    open_paths = {
        "/setup",
        "/setup/test_line",
        "/setup/test_google",
        "/login",
        "/logout",
        "/callback"
    }

    if request.path.startswith("/static/"):
        return None

    if request.path in open_paths:
        return None

    s = load_settings()

    google_ready = bool(s.get("google", {}).get("spreadsheet_id", "").strip())
    line_ready = bool(s.get("line", {}).get("channel_access_token", "").strip())

    if not google_ready or not line_ready:
        return redirect("/setup")

    return None


register_auth_routes(app)
register_admin_routes(app)
register_webhook_routes(app)
register_setup_routes(app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5005))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
