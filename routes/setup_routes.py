import os
from flask import request, render_template

from core.config_manager import BASE_DIR, load_settings, save_settings
from services.line_service import test_line_connection, push_text
from services.sheets_service import ensure_spreadsheet_schema, get_service_account_email, get_system_mode


def register_setup_routes(app):

    def get_setup_context():
        s = load_settings()
        institution_id = s.get("default_institution_id")
        institution = s.get("institutions", {}).get(institution_id)
        return s, institution_id, institution

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        s, institution_id, institution = get_setup_context()
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

                institution["name"] = hospital_name
                institution["department"] = department
                institution["phone"] = request.form.get("hospital_phone", "").strip()
                institution["password"] = admin_password
                institution["line"]["channel_access_token"] = line_token
                institution["google"]["spreadsheet_id"] = spreadsheet_id

                selected_candidate = request.form.get("admin_id_candidate", "").strip()
                manual_admin_ids = [x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()]
                institution["admins"]["line_user_ids"] = [selected_candidate] if selected_candidate else manual_admin_ids

                uploaded = request.files.get("service_account_file")
                if uploaded and uploaded.filename:
                    if not uploaded.filename.lower().endswith(".json"):
                        raise ValueError("Googleサービスアカウントファイルは .json を選択してください。")
                    path = os.path.join(BASE_DIR, f"service_account_{institution_id}.json")
                    uploaded.save(path)
                    institution["google"]["service_account_file"] = path

                save_settings(s)
                message = "設定を保存しました。"
                s, institution_id, institution = get_setup_context()
            except Exception as e:
                error_message = f"保存エラー: {e}"

        return render_template(
            "setup.html",
            title="初期セットアップ",
            settings=s,
            institution_id=institution_id,
            institution=institution,
            service_account_email=get_service_account_email(),
            message=message,
            error_message=error_message
        )

    @app.route("/setup/test_line")
    def setup_test_line():
        s, _, _ = get_setup_context()
        try:
            ok, result = test_line_connection()
            return render_template("setup_result.html", title="LINE接続テスト", success=ok, result_text=str(result), back_url="/setup", settings=s)
        except Exception as e:
            return render_template("setup_result.html", title="LINE接続テスト", success=False, result_text=f"例外発生: {e}", back_url="/setup", settings=s)

    @app.route("/setup/test_line_to/<path:target_id>")
    def setup_test_line_to(target_id):
        s, _, _ = get_setup_context()
        try:
            if not target_id.strip():
                raise ValueError("送信先LINE IDが空です。")
            ok, result = push_text(target_id, "【MedSafety Link テスト】このLINE IDは管理者候補として認識されています。")
            return render_template("setup_result.html", title="候補LINE IDテスト送信", success=ok, result_text=str(result), back_url="/setup", settings=s)
        except Exception as e:
            return render_template("setup_result.html", title="候補LINE IDテスト送信", success=False, result_text=f"例外発生: {e}", back_url="/setup", settings=s)


    @app.route("/setup/init_google")
    def setup_init_google():
        s, _, _ = get_setup_context()
        try:
            initialized = ensure_spreadsheet_schema()
            detail = "必要なシート構成を確認しました。"
            if initialized:
                detail += " 初期化/更新: " + ", ".join(initialized)
            return render_template("setup_result.html", title="Googleシート初期化", success=True, result_text=detail, back_url="/setup", settings=s)
        except Exception as e:
            return render_template("setup_result.html", title="Googleシート初期化", success=False, result_text=f"Googleシート初期化中にエラーが発生しました: {e}", back_url="/setup", settings=s)

    @app.route("/setup/test_google")
    def setup_test_google():
        s, _, _ = get_setup_context()
        try:
            mode = get_system_mode()
            return render_template("setup_result.html", title="Google接続テスト", success=True, result_text=f"Google接続成功。system_mode の現在値: {mode}", back_url="/setup", settings=s)
        except Exception as e:
            return render_template("setup_result.html", title="Google接続テスト", success=False, result_text=f"Google接続テスト中にエラーが発生しました: {e}", back_url="/setup", settings=s)
