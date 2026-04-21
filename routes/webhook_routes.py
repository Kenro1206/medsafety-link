from flask import request


def register_webhook_routes(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        body = request.get_json(force=True, silent=True) or {}
        print(body)
        return "OK", 200
