import os
from flask import request, render_template

from core.config_manager import load_settings, save_settings
from services.line_service import test_line_connection, push_text
from services.sheets_service import get_system_mode


def register_setup_routes(app):

    def ensure_google_defaults(settings_obj):
        if "google" not in settings_obj:
            settings_obj["google"] = {}
        if "service_account_file" not in settings_obj["google"]:
            settings_obj["google"]["service_account_file"] = ""
        if "spreadsheet_id" not in settings_obj["google"]:
            settings_obj["google"]["spreadsheet_id"] = ""

    def ensure_line_defaults(settings_obj):
        if "line" not in settings_obj:
            settings_obj["line"] = {}
        if "channel_access_token" not in settings_obj["line"]:
            settings_obj["line"]["channel_access_token"] = ""

    def ensure_auth_defaults(settings_obj):
        if "auth" not in settings_obj:
            settings_obj["auth"] = {}
        if "admin_password" not in settings_obj["auth"]:
            settings_obj["auth"]["admin_password"] = "admin"

    def ensure_admin_defaults(settings_obj):
        if "admins" not in settings_obj:
            settings_obj["admins"] = {}
        if "line_user_ids" not in settings_obj["admins"]:
            settings_obj["admins"]["line_user_ids"] = []

    def ensure_hospital_defaults(settings_obj):
        if "hospital" not in settings_obj:
            settings_obj["hospital"] = {}
        for key in ["name", "department", "phone"]:
            if key not in settings_obj["hospital"]:
                settings_obj["hospital"][key] = ""

    def ensure_setup_defaults(settings_obj):
        if "setup" not in settings_obj:
            settings_obj["setup"] = {}
        if "candidate_admin_line_ids" not in settings_obj["setup"]:
            settings_obj["setup"]["candidate_admin_line_ids"] = []

    def normalize_settings():
        s = load_settings()
        ensure_google_defaults(s)
        ensure_line_defaults(s)
        ensure_auth_defaults(s)
        ensure_admin_defaults(s)
        ensure_hospital_defaults(s)
        ensure_setup_defaults(s)
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

                selected_candidate = request.form.get("admin_id_candidate", "").strip()
                manual_admin_ids = [
                    x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()
                ]

                if selected_candidate:
                    s["admins"]["line_user_ids"] = [selected_candidate]
                else:
                    s["admins"]["line_user_ids"] = manual_admin_ids

                s["line"]["channel_access_token"] = line_token
                s["google"]["spreadsheet_id"] = spreadsheet_id

                uploaded = request.files.get("service_account_file")
                if uploaded and uploaded.filename:
                    if uploaded.filename.lower().endswith(".json"):
                        save_path = "./service_account.json"
                        uploaded.save(save_path)
                        s["google"]["service_account_file"] = save_path
                    else:
                        raise ValueError("Googleサービスアカウントファイルは .json を選択してください。")
                else:
                    current_json = s["google"].get("service_account_file", "").strip()
                    if not current_json:
                        raise ValueError("GoogleサービスアカウントJSONファイルをアップロードしてください。")

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
            return render_template(
                "setup_result.html",
                title="LINE接続テスト",
                success=ok,
                result_text=result,
                back_url="/setup"
            )
        except Exception as e:
            return render_template(
                "setup_result.html",
                title="LINE接続テスト",
                success=False,
                result_text=f"LINE接続テスト中にエラーが発生しました: {e}",
                back_url="/setup"
            )

    @app.route("/setup/test_line_to/<path:target_id>")
    def setup_test_line_to(target_id):
        s = normalize_settings()

        try:
            if not target_id.strip():
                raise ValueError("送信先LINE IDが空です。")

            ok, result = push_text(target_id, "【MedSafety Link テスト】このLINE IDは管理者候補として認識されています。")
            return render_template(
                "setup_result.html",
                title="候補LINE IDテスト送信",
                success=ok,
                result_text=result if result else "送信しました。",
                back_url="/setup"
            )
        except Exception as e:
            return render_template(
                "setup_result.html",
                title="候補LINE IDテスト送信",
                success=False,
                result_text=f"テスト送信中にエラーが発生しました: {e}",
                back_url="/setup"
            )

    @app.route("/setup/test_google")
    def setup_test_google():
        s = normalize_settings()

        try:
            mode = get_system_mode()

　　　　　　　s = normalize_settings()

            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=True,
                result_text=f"Google接続成功。system_mode の現在値: {mode}",
                back_url="/setup"
                settings=s
            )
        except Exception as e:
            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=False,
                result_text=f"Google接続テスト中にエラーが発生しました: {e}",
                back_url="/setup"
            )
