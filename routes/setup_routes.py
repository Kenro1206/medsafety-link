from flask import request, render_template
from core.config_manager import load_settings, save_settings
from services.line_service import test_line_connection, push_text
from services.sheets_service import get_system_mode


def register_setup_routes(app):

    # =========================
    # デフォルト補完
    # =========================
    def ensure_defaults(s):
        s.setdefault("hospital", {"name": "", "department": "", "phone": ""})
        s.setdefault("auth", {"admin_password": "admin"})
        s.setdefault("admins", {"line_user_ids": []})
        s.setdefault("line", {"channel_access_token": ""})
        s.setdefault("google", {
            "service_account_file": "",
            "spreadsheet_id": ""
        })
        s.setdefault("setup", {
            "candidate_admin_line_ids": []
        })
        return s

    def normalize_settings():
        s = load_settings()
        return ensure_defaults(s)

    # =========================
    # /setup
    # =========================
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

                # 保存
                s["hospital"]["name"] = hospital_name
                s["hospital"]["department"] = department
                s["hospital"]["phone"] = request.form.get("hospital_phone", "").strip()
                s["auth"]["admin_password"] = admin_password
                s["line"]["channel_access_token"] = line_token
                s["google"]["spreadsheet_id"] = spreadsheet_id

                # 管理者LINE ID
                selected_candidate = request.form.get("admin_id_candidate", "").strip()
                manual_admin_ids = [
                    x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()
                ]

                if selected_candidate:
                    s["admins"]["line_user_ids"] = [selected_candidate]
                else:
                    s["admins"]["line_user_ids"] = manual_admin_ids

                # JSONファイル（ローカルのみ）
                uploaded = request.files.get("service_account_file")
                if uploaded and uploaded.filename:
                    if uploaded.filename.lower().endswith(".json"):
                        uploaded.save("./service_account.json")
                        s["google"]["service_account_file"] = "./service_account.json"
                    else:
                        raise ValueError("JSONファイルを選択してください。")

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

    # =========================
    # LINE接続テスト
    # =========================
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
                back_url="/setup",
                settings=s
            )
        except Exception as e:
            return render_template(
                "setup_result.html",
                title="LINE接続テスト",
                success=False,
                result_text=f"エラー: {e}",
                back_url="/setup",
                settings=s
            )

    # =========================
    # 特定IDへLINE送信テスト
    # =========================
    @app.route("/setup/test_line_to/<path:target_id>")
    def setup_test_line_to(target_id):
        s = normalize_settings()

        try:
            if not target_id.strip():
                raise ValueError("LINE ID が空です")

            ok, result = push_text(
                target_id,
                "【MedSafety Link テスト】このLINE IDは管理者候補です。"
            )

            return render_template(
                "setup_result.html",
                title="LINE送信テスト",
                success=ok,
                result_text=result if result else "送信しました",
                back_url="/setup",
                settings=s
            )

        except Exception as e:
            return render_template(
                "setup_result.html",
                title="LINE送信テスト",
                success=False,
                result_text=f"エラー: {e}",
                back_url="/setup",
                settings=s
            )

    # =========================
    # Google接続テスト
    # =========================
    @app.route("/setup/test_google")
    def setup_test_google():
        s = normalize_settings()

        try:
            mode = get_system_mode()

            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=True,
                result_text=f"接続成功（mode: {mode}）",
                back_url="/setup",
                settings=s
            )

        except Exception as e:
            return render_template(
                "setup_result.html",
                title="Google接続テスト",
                success=False,
                result_text=f"エラー: {e}",
                back_url="/setup",
                settings=s
            )
