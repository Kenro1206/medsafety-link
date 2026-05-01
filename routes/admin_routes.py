import copy
import os
import re
from flask import make_response, request, render_template, redirect, session, jsonify
from core.auth import require_login, require_system_admin
from core.config_manager import SETTINGS_PATH, get_settings_storage_status, load_settings, save_settings
from core.institution_context import get_current_institution_id, get_current_institution
from core.time_utils import format_jst_timestamp
from core.utils import help_link
from services.line_service import get_bot_info, push_safety_check, push_text
from services.sheets_service import (
    get_latest_responses,
    get_service_account_email,
    get_service_account_summary,
    get_spreadsheet_id,
    get_spreadsheet_titles,
    get_system_mode,
    append_sent_message,
    load_patients,
    load_pending_users,
    load_responses,
    load_sent_messages,
    save_patients,
    save_pending_users,
    set_latest_response_handled,
    set_response_handled,
    set_system_mode,
    validate_service_account_json_file,
)


def register_admin_routes(app):

    def safe_call(func, default):
        try:
            return func()
        except Exception as e:
            print("[ERROR]", e)
            return default

    def active_admin_path(path):
        return f"{path}?active_institution_id={get_current_institution_id()}"

    def default_message(key):
        settings = load_settings()
        institution = get_current_institution() or {}
        return institution.get("messages", {}).get(key) or settings.get("messages", {}).get(key, "")

    def individual_templates():
        settings = load_settings()
        institution = get_current_institution() or {}
        templates = institution.get("messages", {}).get("individual_templates")
        if not isinstance(templates, list):
            templates = settings.get("messages", {}).get("individual_templates", [])
        fallback = default_message("individual_default")
        templates = [(text or "").strip() for text in templates[:3]]
        while len(templates) < 3:
            templates.append(fallback if not templates else "")
        if not any(templates):
            templates[0] = fallback
        return templates

    def is_handled(response):
        return str(response.get("handled", "")).upper() in ["TRUE", "済", "DONE", "1"]

    def response_row_class(code, handled, severe_codes):
        if code in severe_codes and not handled:
            return "severe"
        if code and not handled:
            return "yellow"
        return "safe-row"

    def with_jst_timestamps(rows):
        formatted = []
        for row in rows:
            item = dict(row)
            item["raw_timestamp"] = item.get("timestamp", "")
            item["timestamp"] = format_jst_timestamp(item.get("timestamp", ""))
            formatted.append(item)
        return formatted

    def remove_linked_pending_users(patients=None, pending_users=None, extra_line_user_ids=None):
        patients = patients if patients is not None else load_patients()
        pending_users = pending_users if pending_users is not None else load_pending_users()
        linked_line_ids = {
            p.get("line_user_id", "").strip()
            for p in patients
            if p.get("line_user_id", "").strip()
        }
        linked_line_ids.update(x.strip() for x in (extra_line_user_ids or []) if x and x.strip())
        filtered = [
            row for row in pending_users
            if row.get("line_user_id", "").strip() not in linked_line_ids
        ]
        if len(filtered) != len(pending_users):
            save_pending_users(filtered)
        return filtered

    @app.route("/admin/dashboard")
    def dashboard():
        auth = require_login()
        if auth:
            return auth

        patients = safe_call(load_patients, [])
        pending_users = safe_call(load_pending_users, [])
        responses = safe_call(load_responses, [])
        latest = safe_call(get_latest_responses, {})
        current_mode = safe_call(get_system_mode, "NORMAL")
        severe_codes = set(load_settings().get("alerts", {}).get("severe_codes", []))

        linked_patients = [p for p in patients if p.get("line_user_id")]
        responded_ids = set(latest.keys())
        severe_unhandled = [
            r for r in latest.values()
            if r.get("code", "") in severe_codes and not is_handled(r)
        ]
        attention_unhandled = [
            r for r in latest.values()
            if r.get("code", "") and r.get("code", "") != "SAFE" and not is_handled(r)
        ]

        recent_responses = sorted(
            responses,
            key=lambda r: r.get("timestamp", ""),
            reverse=True
        )[:20]
        recent_responses = with_jst_timestamps(recent_responses)

        latest_rows = []
        for patient in patients:
            response = latest.get(patient.get("patient_id", ""), {})
            code = response.get("code", "")
            handled = is_handled(response)
            raw_timestamp = response.get("timestamp", "")
            latest_rows.append({
                "patient_id": patient.get("patient_id", ""),
                "name": patient.get("name", ""),
                "phone": patient.get("phone", ""),
                "timestamp": format_jst_timestamp(raw_timestamp or "未回答"),
                "raw_timestamp": raw_timestamp,
                "code": code or "NO_RESPONSE",
                "label": response.get("label", "未回答"),
                "handled": handled,
                "row_class": response_row_class(code, handled, severe_codes),
            })
        latest_rows = sorted(
            latest_rows,
            key=lambda r: (bool(r.get("raw_timestamp")), r.get("raw_timestamp", "")),
            reverse=True
        )
        severe_rows = [
            row for row in latest_rows
            if row.get("code") in severe_codes and not row.get("handled")
        ]

        return render_template(
            "dashboard.html",
            title="ダッシュボード",
            institution_id=get_current_institution_id(),
            institution=get_current_institution(),
            current_mode=current_mode,
            total_patients=len(patients),
            linked_count=len(linked_patients),
            responded_count=len(responded_ids),
            unresponded_count=max(len(patients) - len(responded_ids), 0),
            pending_count=len(pending_users),
            severe_count=len(severe_unhandled),
            attention_count=len(attention_unhandled),
            latest_rows=latest_rows,
            severe_rows=severe_rows,
            recent_responses=recent_responses,
        )

    @app.route("/admin/dashboard/status")
    def dashboard_status():
        auth = require_login()
        if auth:
            return auth

        responses = safe_call(load_responses, [])
        latest_timestamp = ""
        if responses:
            latest_timestamp = max(r.get("timestamp", "") for r in responses)

        return jsonify({
            "response_count": len(responses),
            "latest_timestamp": latest_timestamp,
        })

    @app.route("/admin/settings")
    def admin_settings():
        auth = require_login()
        if auth:
            return auth

        return render_template(
            "settings.html",
            title="設定",
            institution_id=get_current_institution_id(),
            institution=get_current_institution(),
            current_mode=safe_call(get_system_mode, "NORMAL"),
            service_account_email=safe_call(get_service_account_email, ""),
            message="",
            error_message="",
            help_link=help_link
        )

    @app.route("/admin/settings/storage")
    def settings_storage_status():
        auth = require_system_admin()
        if auth:
            return auth

        status = get_settings_storage_status()
        settings = load_settings()
        lines = [
            "設定保存先診断",
            f"設定保存先: {status['settings_path']}",
            f"標準設定ファイル: {status['default_settings_path']}",
            f"永続ディスク候補: {status['persistent_data_dir']}",
            f"永続ディスク候補が存在: {'はい' if status['persistent_data_dir_exists'] else 'いいえ'}",
            f"永続ディスクを使用中: {'はい' if status['uses_persistent_path'] else 'いいえ'}",
            f"設定ファイルが存在: {'はい' if status['settings_exists'] else 'いいえ'}",
            f"バックアップが存在: {'はい' if status['backup_exists'] else 'いいえ'}",
            f"登録施設数: {len(settings.get('institutions', {}))}",
            f"登録施設ID: {', '.join(settings.get('institutions', {}).keys())}",
        ]
        if not status["uses_persistent_path"]:
            lines.extend([
                "",
                "注意: 永続ディスクを使用していません。",
                "RenderのEnvironmentに SETTINGS_PATH=/var/data/settings.json を設定し、Diskの mountPath が /var/data になっているか確認してください。",
            ])

        return render_template(
            "setup_result.html",
            title="設定保存先診断",
            success=status["uses_persistent_path"],
            result_text="\n".join(lines),
            back_url="/admin/settings",
            settings=settings,
        )

    @app.route("/admin/google/status")
    def google_status():
        auth = require_login()
        if auth:
            return auth

        summary = safe_call(get_service_account_summary, {})
        try:
            spreadsheet_id = get_spreadsheet_id()
            email = get_service_account_email()
            titles = get_spreadsheet_titles()
            required = ["patients", "pending_users", "responses", "sent_messages", "system_mode"]
            missing = [name for name in required if name not in titles]

            lines = [
                "Google Sheets接続診断",
                f"スプレッドシートID: {spreadsheet_id}",
                f"サービスアカウント: {email if email else '未取得'}",
                f"認証JSONの使用元: {summary.get('source', '未取得')}",
                f"認証JSONの保存先: {summary.get('source_path', '') or '環境変数または未設定'}",
                f"Google Cloudプロジェクト: {summary.get('project_id', '未取得') or '未取得'}",
                f"秘密鍵ID: {summary.get('private_key_id', '未取得') or '未取得'}",
                f"取得できたシート: {', '.join(titles) if titles else 'なし'}",
            ]
            if missing:
                lines.append(f"不足しているシート: {', '.join(missing)}")
                lines.append("「Googleシート初期化」を実行してください。")
                success = False
            else:
                lines.append("必要なシートは揃っています。")
                success = True

            return render_template(
                "setup_result.html",
                title="Google接続診断",
                success=success,
                result_text="\n".join(lines),
                back_url="/admin/settings",
                settings=load_settings(),
            )
        except Exception as e:
            spreadsheet_id = safe_call(get_spreadsheet_id, "")
            spreadsheet_url = (
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                if spreadsheet_id else "未設定"
            )
            lines = [
                "Google Sheets接続診断",
                f"スプレッドシートID: {spreadsheet_id or '未設定'}",
                f"設定中のスプレッドシートURL: {spreadsheet_url}",
                f"認証JSONの使用元: {summary.get('source', '未取得')}",
                f"認証JSONの保存先: {summary.get('source_path', '') or '環境変数または未設定'}",
                f"サービスアカウント: {summary.get('client_email', '未取得') or '未取得'}",
                f"Google Cloudプロジェクト: {summary.get('project_id', '未取得') or '未取得'}",
                f"秘密鍵ID: {summary.get('private_key_id', '未取得') or '未取得'}",
                f"Google Sheetsを読み込めませんでした: {e}",
            ]
            return render_template(
                "setup_result.html",
                title="Google接続診断",
                success=False,
                result_text="\n".join(lines),
                back_url="/admin/settings",
                settings=load_settings(),
            )

    @app.route("/admin/settings/save", methods=["POST"])
    def admin_settings_save():
        auth = require_login()
        if auth:
            return auth

        institution_id = get_current_institution_id()
        s = load_settings()
        try:
            inst = s["institutions"][institution_id]

            inst["name"] = request.form.get("hospital_name", "").strip()
            inst["department"] = request.form.get("department", "").strip()
            inst["phone"] = request.form.get("hospital_phone", "").strip()
            inst["password"] = request.form.get("password", "").strip() or inst.get("password", "admin")
            old_line_token = inst["line"].get("channel_access_token", "").strip()
            new_line_token = request.form.get("line_token", "").strip()
            manual_bot_user_id = request.form.get("line_bot_user_id", "").strip()
            inst["line"]["channel_access_token"] = new_line_token
            if manual_bot_user_id:
                inst["line"]["bot_user_id"] = manual_bot_user_id
            elif new_line_token != old_line_token:
                inst["line"]["bot_user_id"] = ""
            global_messages = s.get("messages", {})
            inst_messages = inst.setdefault("messages", {})
            inst_messages["broadcast_default"] = (
                request.form.get("broadcast_default", "").strip()
                or global_messages.get("broadcast_default", "")
            )
            inst_messages["remind_default"] = (
                request.form.get("remind_default", "").strip()
                or global_messages.get("remind_default", "")
            )
            inst_messages["individual_default"] = (
                request.form.get("individual_default", "").strip()
                or global_messages.get("individual_default", "")
            )
            inst_messages["individual_templates"] = []
            for index in range(1, 4):
                template = request.form.get(f"individual_template_{index}", "").strip()
                if not template and index == 1:
                    template = inst_messages["individual_default"]
                inst_messages["individual_templates"].append(template)
            default_options = s.get("safety_reply_options", [])
            inst["safety_reply_options"] = []
            for index in range(5):
                fallback = default_options[index] if index < len(default_options) else {}
                code = request.form.get(f"safety_code_{index + 1}", "").strip().upper()
                inst["safety_reply_options"].append({
                    "label": request.form.get(f"safety_label_{index + 1}", "").strip() or fallback.get("label", ""),
                    "code": code or fallback.get("code", ""),
                    "text": str(index + 1),
                })
            inst["google"]["spreadsheet_id"] = request.form.get("spreadsheet_id", "").strip()
            inst["admins"]["line_user_ids"] = [x.strip() for x in request.form.get("admin_ids", "").split(",") if x.strip()]

            uploaded = request.files.get("service_account_file")
            if uploaded and uploaded.filename:
                if not uploaded.filename.lower().endswith(".json"):
                    raise ValueError("Googleサービスアカウントファイルは .json を選択してください。")
                settings_dir = os.path.dirname(SETTINGS_PATH) or "."
                os.makedirs(settings_dir, exist_ok=True)
                path = os.path.join(settings_dir, f"service_account_{institution_id}.json")
                upload_path = f"{path}.upload"
                uploaded.save(upload_path)
                validate_service_account_json_file(upload_path)
                os.replace(upload_path, path)
                inst["google"]["service_account_file"] = path

            save_settings(s)
            s = load_settings()
            message = "設定を保存しました。"
            error_message = ""
        except Exception as e:
            message = ""
            error_message = f"保存エラー: {e}"

        return render_template(
            "settings.html",
            title="設定",
            institution_id=get_current_institution_id(),
            institution=s.get("institutions", {}).get(get_current_institution_id(), get_current_institution()),
            current_mode=safe_call(get_system_mode, "NORMAL"),
            service_account_email=safe_call(get_service_account_email, ""),
            message=message,
            error_message=error_message,
            help_link=help_link
        )

    @app.route("/admin/line/status")
    def line_status():
        auth = require_login()
        if auth:
            return auth

        institution_id = get_current_institution_id()
        s = load_settings()
        inst = s.get("institutions", {}).get(institution_id)
        try:
            ok, result = get_bot_info()
            if not ok:
                raise ValueError(result)

            bot_user_id = result.get("userId", "")
            if bot_user_id:
                inst.setdefault("line", {})["bot_user_id"] = bot_user_id
                save_settings(s)

            lines = [
                "LINE接続診断",
                f"施設ID: {institution_id}",
                f"Bot userId: {bot_user_id or '未取得'}",
                f"表示名: {result.get('displayName', '未取得')}",
                "Webhook URL: https://medsafety-link.onrender.com/callback",
                "このBot userIdを保存しました。患者さんからのWebhookを、この施設の登録待ちユーザーへ保存します。",
            ]
            return render_template(
                "setup_result.html",
                title="LINE接続診断",
                success=True,
                result_text="\n".join(lines),
                back_url="/admin/settings",
                settings=load_settings(),
            )
        except Exception as e:
            token_set = bool(inst.get("line", {}).get("channel_access_token", "").strip()) if inst else False
            return render_template(
                "setup_result.html",
                title="LINE接続診断",
                success=False,
                result_text=(
                    "LINE接続診断に失敗しました。\n"
                    f"施設ID: {institution_id}\n"
                    f"チャネルアクセストークン: {'設定済み' if token_set else '未設定'}\n"
                    f"エラー: {e}\n"
                    "設定画面で、この施設用のLINEチャネルアクセストークンを入力して保存してください。"
                ),
                back_url="/admin/settings",
                settings=load_settings(),
            )

    @app.route("/admin/webhook/status")
    def webhook_status():
        auth = require_login()
        if auth:
            return auth

        settings = load_settings()
        recent = settings.get("webhook_status", {}).get("recent", [])
        lines = ["Webhook受信診断", f"記録件数: {len(recent)}"]
        if not recent:
            lines.append("まだWebhook受信記録がありません。LINEから公式アカウントへ「テスト」と送ってから再確認してください。")
        for idx, row in enumerate(recent[:10], start=1):
            lines.extend([
                "",
                f"#{idx}",
                f"時刻: {row.get('timestamp', '')}",
                f"destination: {row.get('destination', '')}",
                f"イベント: {row.get('event_type', '')}/{row.get('message_type', '')}",
                f"LINE user_id: {row.get('line_user_id', '')}",
                f"本文: {row.get('text', '')}",
                f"destination判定施設: {row.get('destination_institution_id', '') or '未判定'}",
                f"保存先/一致施設: {row.get('matched_institution_id', '') or '未判定'}",
                f"患者ID: {row.get('patient_id', '') or '未登録'}",
                f"処理: {row.get('action', '')}",
                f"返信結果: {row.get('reply_result', '') or 'なし'}",
                f"エラー: {row.get('error', '') or 'なし'}",
            ])

        return render_template(
            "setup_result.html",
            title="Webhook受信診断",
            success=True,
            result_text="\n".join(lines),
            back_url="/admin/settings",
            settings=settings,
        )

    @app.route("/admin/institutions", methods=["GET", "POST"])
    def institutions():
        auth = require_system_admin()
        if auth:
            return auth

        s = load_settings()
        message = ""
        error_message = ""

        if request.method == "POST":
            action = request.form.get("action", "").strip()
            try:
                if action == "create":
                    institution_id = request.form.get("institution_id", "").strip()
                    if not re.fullmatch(r"[A-Za-z0-9_-]{3,40}", institution_id or ""):
                        raise ValueError("施設IDは3〜40文字の半角英数字、ハイフン、アンダースコアで入力してください。")
                    if institution_id in s.get("institutions", {}):
                        raise ValueError("この施設IDはすでに登録されています。")

                    default_settings = load_settings()
                    s.setdefault("institutions", {})[institution_id] = {
                        "name": request.form.get("name", "").strip() or institution_id,
                        "department": request.form.get("department", "").strip(),
                        "phone": "",
                        "password": request.form.get("password", "").strip() or "admin",
                        "line": {"channel_access_token": "", "bot_user_id": ""},
                        "google": {"service_account_file": "./service_account.json", "spreadsheet_id": ""},
                        "admins": {"line_user_ids": []},
                        "messages": copy.deepcopy(default_settings.get("messages", {})),
                        "safety_reply_options": copy.deepcopy(default_settings.get("safety_reply_options", []))
                    }
                    message = f"施設「{institution_id}」を追加しました。設定する場合は「この施設を操作」を押してください。"

                elif action == "update":
                    institution_id = request.form.get("institution_id", "").strip()
                    inst = s.get("institutions", {}).get(institution_id)
                    if not inst:
                        raise ValueError("施設が見つかりません。")
                    inst["name"] = request.form.get("name", "").strip() or inst.get("name", institution_id)
                    inst["department"] = request.form.get("department", "").strip()
                    password = request.form.get("password", "").strip()
                    if password:
                        inst["password"] = password
                    message = "施設情報を更新しました。"

                elif action == "delete":
                    institution_id = request.form.get("institution_id", "").strip()
                    institutions = s.get("institutions", {})
                    if institution_id not in institutions:
                        raise ValueError("施設が見つかりません。")
                    if len(institutions) <= 1:
                        raise ValueError("最後の1施設は削除できません。")
                    if institution_id == get_current_institution_id():
                        raise ValueError("現在操作中の施設は削除できません。別の施設を操作対象に切り替えてから削除してください。")

                    deleted_name = institutions.get(institution_id, {}).get("name", institution_id)
                    del institutions[institution_id]

                    admin_ids = s.setdefault("system_admins", {}).setdefault("institution_ids", [])
                    s["system_admins"]["institution_ids"] = [x for x in admin_ids if x != institution_id]
                    if s.get("default_institution_id") == institution_id:
                        s["default_institution_id"] = next(iter(institutions))
                    if session.get("institution_id") == institution_id:
                        session["institution_id"] = s.get("default_institution_id")

                    message = f"施設「{deleted_name}」を削除しました。"

                elif action == "switch":
                    institution_id = request.form.get("institution_id", "").strip()
                    if institution_id not in s.get("institutions", {}):
                        raise ValueError("施設が見つかりません。")
                    session["institution_id"] = institution_id
                    response = make_response(redirect(f"/admin/dashboard?active_institution_id={institution_id}"))
                    response.set_cookie(
                        "last_operated_institution_id",
                        institution_id,
                        max_age=60 * 60 * 24 * 180,
                        httponly=True,
                        samesite="Lax",
                        secure=request.is_secure,
                    )
                    return response

                else:
                    raise ValueError("不明な操作です。")

                save_settings(s)
                s = load_settings()
                if action == "create" and institution_id not in s.get("institutions", {}):
                    raise RuntimeError("施設追加後の保存確認に失敗しました。設定保存先を確認してください。")
            except Exception as e:
                error_message = str(e)

        response = make_response(
            render_template(
                "institutions.html",
                title="施設ID管理",
                institutions=s.get("institutions", {}),
                current_institution_id=get_current_institution_id(),
                message=message,
                error_message=error_message,
            )
        )
        return response

    @app.route("/admin/register", methods=["GET", "POST"])
    def register_patients():
        auth = require_login()
        if auth:
            return auth

        message = ""
        error_message = ""
        if request.method == "POST":
            try:
                patient_id = request.form.get("patient_id", "").strip()
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                line_user_id = request.form.get("line_user_id", "").strip()
                if not patient_id or not name:
                    raise ValueError("患者IDと氏名は必須です。")
                patients = load_patients()
                existing = next((p for p in patients if p.get("patient_id") == patient_id), None)
                if existing:
                    existing.update({"name": name, "phone": phone, "line_user_id": line_user_id})
                    message = "患者情報を更新しました。"
                else:
                    patients.append({"patient_id": patient_id, "name": name, "phone": phone, "line_user_id": line_user_id})
                    message = "患者を登録しました。"
                save_patients(patients)
                if line_user_id:
                    remove_linked_pending_users(patients=patients, extra_line_user_ids=[line_user_id])
            except Exception as e:
                error_message = f"保存エラー: {e}"

        patients = safe_call(load_patients, [])
        pending_users = with_jst_timestamps(safe_call(lambda: remove_linked_pending_users(patients=patients), []))
        unlinked_patients = [p for p in patients if not p.get("line_user_id")]
        return render_template("register.html", title="患者登録", patients=patients, pending_users=pending_users, unlinked_patients=unlinked_patients, message=message, error_message=error_message)

    @app.route("/admin/link", methods=["POST"])
    def link_patient():
        auth = require_login()
        if auth:
            return auth

        line_user_id = request.form.get("line_user_id", "").strip()
        patient_id = request.form.get("patient_id", "").strip()
        patients = load_patients()
        for patient in patients:
            if patient.get("patient_id") == patient_id:
                patient["line_user_id"] = line_user_id
        save_patients(patients)
        remove_linked_pending_users(patients=patients, extra_line_user_ids=[line_user_id])
        return redirect(active_admin_path("/admin/register"))

    @app.route("/admin/responders")
    def responders():
        auth = require_login()
        if auth:
            return auth

        patients = safe_call(load_patients, [])
        latest = safe_call(get_latest_responses, {})
        severe = set(load_settings().get("alerts", {}).get("severe_codes", []))
        rows = []
        for patient in patients:
            response = latest.get(patient.get("patient_id", ""), {})
            code = response.get("code", "")
            handled = is_handled(response)
            row_class = response_row_class(code, handled, severe)
            rows.append({
                "patient_id": patient.get("patient_id", ""),
                "name": patient.get("name", ""),
                "phone": patient.get("phone", ""),
                "line_user_id": patient.get("line_user_id", ""),
                "timestamp": format_jst_timestamp(response.get("timestamp", "未回答")),
                "answer_code": code or "NO_RESPONSE",
                "answer_label": response.get("label", "未回答"),
                "is_handled": handled,
                "row_class": row_class,
            })
        return render_template(
            "responders.html",
            title="患者一覧",
            responders=rows,
            default_message=default_message("individual_default"),
            individual_templates=individual_templates(),
            safety_message=default_message("broadcast_default"),
        )

    @app.route("/admin/responses")
    def responses_history():
        auth = require_login()
        if auth:
            return auth

        responses = safe_call(load_responses, [])
        responses = sorted(responses, key=lambda r: r.get("timestamp", ""), reverse=True)
        responses = with_jst_timestamps(responses)
        sent_messages = safe_call(load_sent_messages, [])
        sent_messages = sorted(sent_messages, key=lambda r: r.get("timestamp", ""), reverse=True)
        sent_messages = with_jst_timestamps(sent_messages)
        return render_template(
            "responses.html",
            title="回答履歴",
            responses=responses[:200],
            sent_messages=sent_messages[:200],
            sent_total_count=len(sent_messages),
            total_count=len(responses),
            default_message=default_message("individual_default"),
            individual_templates=individual_templates(),
        )

    @app.route("/admin/responses/handle", methods=["POST"])
    def handle_response_history():
        auth = require_login()
        if auth:
            return auth
        timestamp = request.form.get("timestamp", "").strip()
        patient_id = request.form.get("patient_id", "").strip()
        line_user_id = request.form.get("line_user_id", "").strip()
        handled = request.form.get("handled", "") == "true"
        set_response_handled(timestamp, patient_id, handled, line_user_id)
        return redirect(active_admin_path("/admin/responses"))

    @app.route("/admin/responders/message", methods=["POST"])
    def responder_message():
        auth = require_login()
        if auth:
            return auth

        patient_id = request.form.get("patient_id", "").strip()
        message = request.form.get("message", "").strip()
        send_type = request.form.get("send_type", "text").strip()
        redirect_to = request.form.get("redirect_to", "/admin/responders").strip()
        if redirect_to not in ["/admin/responders", "/admin/responses"]:
            redirect_to = "/admin/responders"

        if not message:
            return redirect(active_admin_path(redirect_to))

        patients = load_patients()
        patient = next((p for p in patients if p.get("patient_id") == patient_id), None)
        if not patient or not patient.get("line_user_id"):
            return redirect(active_admin_path(redirect_to))

        if send_type == "safety":
            ok, detail = push_safety_check(patient.get("line_user_id"), message)
            append_sent_message(patient, "個別送信（安否確認）", message, ok, detail)
        else:
            ok, detail = push_text(patient.get("line_user_id"), message)
            append_sent_message(patient, "個別送信", message, ok, detail)

        return redirect(active_admin_path(redirect_to))

    @app.route("/admin/responders/handle", methods=["POST"])
    def handle_responder():
        auth = require_login()
        if auth:
            return auth
        set_latest_response_handled(request.form.get("patient_id", "").strip(), True)
        return redirect(active_admin_path("/admin/responders"))

    @app.route("/admin/responders/unhandle", methods=["POST"])
    def unhandle_responder():
        auth = require_login()
        if auth:
            return auth
        set_latest_response_handled(request.form.get("patient_id", "").strip(), False)
        return redirect(active_admin_path("/admin/responders"))

    @app.route("/admin/broadcast")
    def broadcast():
        auth = require_login()
        if auth:
            return auth
        return render_template("broadcast.html", title="一斉送信", default_message=default_message("broadcast_default"))

    @app.route("/admin/broadcast/send", methods=["POST"])
    def broadcast_send():
        auth = require_login()
        if auth:
            return auth
        message = request.form.get("message", "").strip()
        return render_template("broadcast_result.html", title="一斉送信結果", **send_to_patients(load_patients(), message, with_safety_buttons=True, send_type="一斉送信"))

    @app.route("/admin/remind")
    def remind():
        auth = require_login()
        if auth:
            return auth
        return render_template("remind.html", title="未回答再送", default_message=default_message("remind_default"))

    @app.route("/admin/remind/send", methods=["POST"])
    def remind_send():
        auth = require_login()
        if auth:
            return auth
        message = request.form.get("message", "").strip()
        latest = get_latest_responses()
        targets = [p for p in load_patients() if p.get("line_user_id") and p.get("patient_id") not in latest]
        return render_template("broadcast_result.html", title="再送結果", **send_to_patients(targets, message, with_safety_buttons=True, send_type="未回答再送"))

    @app.route("/admin/mode", methods=["GET", "POST"])
    def mode():
        auth = require_login()
        if auth:
            return auth
        if request.method == "POST":
            set_system_mode(request.form.get("mode", "NORMAL"))
            return redirect(active_admin_path("/admin/mode"))
        return render_template("mode.html", title="モード切替", current_mode=safe_call(get_system_mode, "NORMAL"))

    @app.route("/admin/help/<topic>")
    def help_page(topic):
        auth = require_login()
        if auth:
            return auth
        body = {
            "settings": "LINEチャネルアクセストークン、GoogleスプレッドシートID、管理者LINE IDを設定します。",
            "register": "未登録ユーザーのLINE user_idを患者マスタへ紐付けます。",
            "responders": "最新回答、緊急度、対応状況を確認します。",
            "google_setup": """
                <h3>Google Sheets連携手順</h3>
                <p>
                  Google Cloud Console:
                  <a href="https://console.cloud.google.com/" target="_blank" rel="noopener">https://console.cloud.google.com/</a>
                </p>
                <p>
                  サービスアカウント画面:
                  <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank" rel="noopener">https://console.cloud.google.com/iam-admin/serviceaccounts</a>
                </p>
                <ol>
                  <li>Google Cloudでサービスアカウントを作成し、JSONキーをダウンロードします。</li>
                  <li>MedSafety Linkの「設定」または「初期セットアップ」でJSONファイルをアップロードします。</li>
                  <li>画面に表示される「スプレッドシート共有先メールアドレス」をコピーします。</li>
                  <li>Googleスプレッドシートを開き、右上の「共有」を押します。</li>
                  <li>コピーしたメールアドレスを貼り付け、権限を「編集者」にして共有します。</li>
                  <li>スプレッドシートURLの /d/ と /edit の間の文字列をコピーします。</li>
                  <li>MedSafety Linkの「スプレッドシートID」に貼り付けて保存します。</li>
                  <li>「Google接続テスト」を押します。</li>
                  <li>接続成功後、「Googleシート初期化」を押します。</li>
                </ol>
                <p><strong>403エラーが出る場合:</strong> 共有先メールアドレスがスプレッドシートに「編集者」として追加されているか確認してください。</p>
                <p><strong>404エラーが出る場合:</strong> スプレッドシートIDが正しいか確認してください。</p>
            """,
        }.get(topic, "ヘルプは準備中です。")
        return render_template("help.html", title="ヘルプ", body=body)

    def send_to_patients(patients, message, with_safety_buttons=False, send_type="送信"):
        results = []
        success = 0
        fail = 0
        for patient in patients:
            if not patient.get("line_user_id"):
                continue
            if with_safety_buttons:
                ok, detail = push_safety_check(patient.get("line_user_id"), message)
            else:
                ok, detail = push_text(patient.get("line_user_id"), message)
            append_sent_message(patient, send_type, message, ok, detail)
            success += 1 if ok else 0
            fail += 0 if ok else 1
            results.append({"patient_id": patient.get("patient_id", ""), "name": patient.get("name", ""), "ok": ok, "detail": detail})
        return {"success": success, "fail": fail, "results": results}
