from flask import request, render_template

from core.config_manager import load_settings, save_settings
from services.line_service import test_line_connection, push_text
from services.sheets_service import get_system_mode


def register_setup_routes(app):

    def ensure_defaults(s):
        if "hospital" not in s:
            s["hospital"] = {}
        s["hospital"].setdefault("name", "")
        s["hospital"].setdefault("department", "")
        s["hospital"].setdefault("phone", "")

        if "auth" not in s:
            s["auth"] = {}
        s["auth"].setdefault("admin_password", "admin")

        if "admins" not in s:
            s["admins"] = {}
        s["admins"].setdefault("line_user_ids", [])

        if "line" not in s:
            s["line"] = {}
        s["line"].setdefault("channel_access_token", "")

        if "google" not in s:
            s["google"] = {}
        s["google"].setdefault("service_account_file", "")
        s["google"].setdefault("spreadsheet_id", "")

        if "setup" not in s:
            s["setup"] = {}
        s["setup"].setdefault("candidate_admin_line_ids", [])

        return s


    def normalize_settings():
        s = load_settings()
        s = ensure_defaults(s)
        save_settings(s)
        return s


    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        s = normalize_settings()
        message = ""
        error_message = ""

        if request.method == "POST":
            try:
                hospital_name = request.form.get("hospital_name", "").strip()
                department = request.form.get("department", "").strip()
                admin_password = request.form.get("admin_password", "").strip()
                line_token = request.form.get("line_token", "").strip()
                spreadsheet_id = request.form.get("spreadsheet_id", "").strip()

                if not hospital_name:
                    raise ValueError("病院名を入力してください。")

                if not department:
                    raise ValueError("診療科を入力してください。")

                if not admin_password:
                    raise ValueError("管理者パスワードを入力してください。")

                if not line_token:
                    raise ValueError("LINEチャネルアクセストークンを入力してください。")

                if not spreadsheet_id:
                    raise ValueError("スプレッドシートIDを入力してください。")

                s["hospital"]["name"] = hospital_name
                s["hospital"]["department"] = department
                s["hospital"]["phone"] = request.form.get("hospital_phone", "").strip()

                s["auth"]["admin_password"] = admin_password
                s["line"]["channel_access_token"] = line_token
                s["google"]["spreadsheet_id"] = spreadsheet_id

                selected_candidate = request.form.get("admin_id_candidate", "").strip()
                manual_admin_ids = [
                    x.strip()
                    for x in request.form.get("admin_ids", "").split(",")
                    if x.strip()
                ]

                if selected_candidate:
                    s["admins"]["line_user_ids"] = [selected_candidate]
                else:
                    s["admins"]["line_user_ids"] = manual_admin_ids

                uploaded = request.files.get("service_account_file")

                if uploaded and uploaded.filename:
                    if uploaded.filename.lower().endswith(".json"):
                        uploaded.save("./service_account.json")
                        s["google"]["service_account_file"] = "./service_account.json"
                    else:
                        raise ValueError("Googleサービスアカウントファイルは .json を選択してください。")

                save_settings(s)
                message = "設定を保存しました。"

            except Exception as e:
                error_message = f"保存エラー: {e}"

        return render_template(
            "setup.html",
            title="初期セットアップ",
            settings=s,
            message=message,
            error_message=error_message
        )


    @app.route("/setup/test_line")
    def setup_test_line():
        s = normalize_settings()

        try:
            ok, result = test_line_connection()

            if not result:
                result = "LINEからの応答が空です。トークン設定を確認してください。"

            return render_template(
                "setup_result.html",
                title="LINE接続テスト",
                success=ok,
                result_text=str(result),
                back_url="/setup",
                settings=s
            )

        except Exception as e:
            return render_template(
                "setup_result.html",
                title="LINE接続テスト",
                success=False,
                result_text=f"例外発生: {e}",
                back_url="/setup",
                settings=s
            )


    @app.route("/setup/test_line_to/<path:target_id>")
    def setup_test_line_to(target_id):
        s = normalize_settings()

        try:
            if not target_id.strip():
                raise ValueError("送信先LINE IDが空です。")

            ok, result = push_text(
                target_id,
                "【MedSafety Link テスト】このLINE IDは管理者候補として認識されています。"
            )

            if not result:
                result = "LINEからの応答が空です。"

            return render_template(
                "setup_result.html",
                title="候補LINE IDテスト送信",
                success=ok,
                result_text=str(result),
                back_url="/setup",
                settings=s
            )

        except Exception as e:
            return render_template(
                "setup_result.html",
                title="候補LINE IDテスト送信",
                success=False,
                result_text=f"例外発生: {e}",
                back_url="/setup",
                settings=s
            )


    @app.route("/setup/test_google")
    def setup_test_google():
        s = normalize_settings()

        try:
            mode = get_system_mode()

            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=True,
                result_text=f"Google接続成功。system_mode の現在値: {mode}",
                back_url="/setup",
                settings=s
            )

        except Exception as e:
            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=False,
                result_text=f"Google接続テスト中にエラーが発生しました: {e}",
                back_url="/setup",
                settings=s
            )
