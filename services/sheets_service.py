import json
import os
from datetime import datetime
from urllib.parse import quote

from core.config_manager import load_settings
from core.institution_context import get_current_institution

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
PATIENTS_RANGE = "patients!A:D"
PENDING_RANGE = "pending_users!A:D"
RESPONSES_RANGE = "responses!A:H"
SYSTEM_MODE_RANGE = "system_mode!A:A"

REQUIRED_SHEETS = {
    "patients": [["patient_id", "name", "phone", "line_user_id"]],
    "pending_users": [["timestamp", "line_user_id", "patient_name", "display_text"]],
    "responses": [["timestamp", "patient_id", "name", "line_user_id", "event_type", "code", "label", "handled"]],
    "system_mode": [["mode"], ["NORMAL"]],
}


def _looks_like_default_service_account_path(path):
    return path in {"./service_account.json", "service_account.json"}


def _configured_service_account_file():
    institution = get_current_institution()
    if institution:
        service_account_file = institution.get("google", {}).get("service_account_file", "").strip()
        if service_account_file and (
            os.path.exists(service_account_file)
            or not _looks_like_default_service_account_path(service_account_file)
        ):
            return service_account_file

    service_account_file = load_settings().get("google", {}).get("service_account_file", "").strip()
    if service_account_file and (
        os.path.exists(service_account_file)
        or not _looks_like_default_service_account_path(service_account_file)
    ):
        return service_account_file

    return ""


def _load_service_account_info_from_env():
    json_str = os.getenv("GOOGLE_SERVICE_JSON", "").strip()
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            "Render環境変数 GOOGLE_SERVICE_JSON のJSON形式が正しくありません。"
            "設定画面でサービスアカウントJSONをアップロードするか、環境変数を削除/修正してください。"
        ) from e


def _validate_service_account_info(info):
    required = ["type", "project_id", "private_key_id", "private_key", "client_email"]
    missing = [key for key in required if not info.get(key)]
    if missing:
        raise ValueError(f"サービスアカウントJSONに必要な項目がありません: {', '.join(missing)}")
    if info.get("type") != "service_account":
        raise ValueError("アップロードされたJSONはサービスアカウントJSONではありません。")
    private_key = info.get("private_key", "")
    if "BEGIN PRIVATE KEY" not in private_key or "END PRIVATE KEY" not in private_key:
        raise ValueError("サービスアカウントJSONの private_key が正しくありません。JSONを作り直して再アップロードしてください。")
    return info


def validate_service_account_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return _validate_service_account_info(json.load(f))


def get_service_account_summary():
    service_account_file = _configured_service_account_file()
    info = None
    source = "未設定"

    if service_account_file and os.path.exists(service_account_file):
        source = "設定画面でアップロードされたJSON"
        with open(service_account_file, "r", encoding="utf-8") as f:
            info = json.load(f)
    else:
        env_info = _load_service_account_info_from_env()
        if env_info:
            source = "Render環境変数 GOOGLE_SERVICE_JSON"
            info = env_info

    if not info:
        return {"source": source, "client_email": "", "project_id": "", "private_key_id": ""}

    return {
        "source": source,
        "client_email": info.get("client_email", ""),
        "project_id": info.get("project_id", ""),
        "private_key_id": info.get("private_key_id", ""),
    }


def get_credentials():
    from google.oauth2.service_account import Credentials

    service_account_file = _configured_service_account_file()
    if not os.path.exists(service_account_file):
        env_info = _load_service_account_info_from_env()
        if env_info:
            return Credentials.from_service_account_info(_validate_service_account_info(env_info), scopes=SCOPES)
        if service_account_file:
            raise ValueError(
                "GoogleサービスアカウントJSONファイルが見つかりません。"
                "設定画面でサービスアカウントJSONを再アップロードして保存してください。"
            )
        raise ValueError("Google認証情報が未設定です。設定画面でサービスアカウントJSONをアップロードしてください。")

    validate_service_account_json_file(service_account_file)
    return Credentials.from_service_account_file(service_account_file, scopes=SCOPES)


def get_service_account_email():
    service_account_file = _configured_service_account_file()
    if service_account_file and os.path.exists(service_account_file):
        try:
            with open(service_account_file, "r", encoding="utf-8") as f:
                return json.load(f).get("client_email", "")
        except Exception:
            return ""
    try:
        env_info = _load_service_account_info_from_env()
        return env_info.get("client_email", "") if env_info else ""
    except Exception:
        return ""


def get_authorized_session():
    from google.auth.transport.requests import AuthorizedSession

    creds = get_credentials()
    return AuthorizedSession(creds)


def sheets_api_request(method, path, **kwargs):
    session = get_authorized_session()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{get_spreadsheet_id()}{path}"
    try:
        response = session.request(method, url, timeout=20, **kwargs)
    except Exception as e:
        if "invalid_grant" in str(e) or "Invalid JWT Signature" in str(e):
            raise ValueError(
                "Google認証に失敗しました。サービスアカウントJSONの秘密鍵が無効です。"
                "Google Cloudでこのサービスアカウントの新しいキーJSONを作成し、設定画面で再アップロードしてください。"
                "Renderの環境変数 GOOGLE_SERVICE_JSON を使っている場合は、古い値を削除または更新してください。"
            ) from e
        raise
    if response.status_code >= 400:
        if response.status_code == 403:
            email = get_service_account_email() or "サービスアカウントの client_email"
            if "has not been used" in response.text or "disabled" in response.text:
                raise ValueError(
                    "Google Sheets APIが有効になっていない可能性があります。"
                    "Google Cloud Consoleで、このサービスアカウントのプロジェクトの Google Sheets API を有効にしてください。"
                    f" 詳細: {response.text}"
                )
            raise ValueError(
                "Googleスプレッドシートへのアクセス権限がありません。"
                f"スプレッドシート右上の「共有」から {email} を編集者として追加してください。"
                f" すでに共有済みの場合は、設定画面のスプレッドシートIDが共有したシートのURLと一致しているか確認してください。"
                f" 詳細: {response.text}"
            )
        if response.status_code == 404:
            raise ValueError("Googleスプレッドシートが見つかりません。スプレッドシートIDが正しいか確認してください。")
        raise ValueError(f"Google Sheets API error: status={response.status_code}, body={response.text}")
    if response.text:
        return response.json()
    return {}


def get_spreadsheet_id():
    institution = get_current_institution()
    spreadsheet_id = ""
    if institution:
        spreadsheet_id = institution.get("google", {}).get("spreadsheet_id", "").strip()

    if not spreadsheet_id:
        spreadsheet_id = load_settings().get("google", {}).get("spreadsheet_id", "").strip()

    if not spreadsheet_id:
        raise ValueError("スプレッドシートIDが未設定です。")

    return spreadsheet_id


def get_spreadsheet_titles():
    spreadsheet = sheets_api_request("GET", "", params={"fields": "sheets.properties.title"})
    return [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]


def read_sheet(range_name):
    result = sheets_api_request("GET", f"/values/{quote(range_name, safe='')}")
    return result.get("values", [])


def append_sheet(range_name, row_values):
    sheets_api_request(
        "POST",
        f"/values/{quote(range_name, safe='')}:append",
        params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
        json={"values": [row_values]}
    )


def update_sheet(range_name, values):
    sheets_api_request(
        "PUT",
        f"/values/{quote(range_name, safe='')}",
        params={"valueInputOption": "USER_ENTERED"},
        json={"values": values}
    )


def rows_to_dicts(rows):
    if len(rows) < 2:
        return []
    headers = rows[0]
    data = []
    for row in rows[1:]:
        item = {}
        for i, header in enumerate(headers):
            item[header] = row[i] if i < len(row) else ""
        data.append(item)
    return data


def load_patients():
    return rows_to_dicts(read_sheet(PATIENTS_RANGE))


def save_patients(patients):
    values = [["patient_id", "name", "phone", "line_user_id"]]
    for p in patients:
        values.append([
            p.get("patient_id", ""),
            p.get("name", ""),
            p.get("phone", ""),
            p.get("line_user_id", "")
        ])
    update_sheet("patients!A1:D", values)


def load_pending_users():
    return rows_to_dicts(read_sheet(PENDING_RANGE))


def save_pending_users(rows):
    values = [["timestamp", "line_user_id", "patient_name", "display_text"]]
    for r in rows:
        values.append([
            r.get("timestamp", ""),
            r.get("line_user_id", ""),
            r.get("patient_name", ""),
            r.get("display_text", "")
        ])
    update_sheet("pending_users!A1:D", values)


def load_responses():
    return rows_to_dicts(read_sheet(RESPONSES_RANGE))


def append_response(patient, user_id, event_type, code, label):
    append_sheet(RESPONSES_RANGE, [
        datetime.now().isoformat(timespec="seconds"),
        patient.get("patient_id", ""),
        patient.get("name", ""),
        user_id,
        event_type,
        code,
        label,
        ""
    ])


def get_latest_responses():
    responses = load_responses()
    latest = {}
    for r in responses:
        pid = r.get("patient_id", "")
        ts = r.get("timestamp", "")
        if not pid:
            continue
        if pid not in latest or ts >= latest[pid].get("timestamp", ""):
            latest[pid] = r
    return latest


def set_latest_response_handled(patient_id, handled):
    rows = read_sheet(RESPONSES_RANGE)
    if len(rows) < 2:
        return False

    headers = rows[0]
    while len(headers) < 8:
        headers.append("handled")
    if "handled" not in headers:
        headers.append("handled")

    pid_index = headers.index("patient_id") if "patient_id" in headers else 1
    ts_index = headers.index("timestamp") if "timestamp" in headers else 0
    handled_index = headers.index("handled")

    best_row_index = None
    best_ts = ""
    for idx, row in enumerate(rows[1:], start=2):
        pid = row[pid_index] if pid_index < len(row) else ""
        ts = row[ts_index] if ts_index < len(row) else ""
        if pid == patient_id and (best_row_index is None or ts >= best_ts):
            best_row_index = idx
            best_ts = ts

    if best_row_index is None:
        return False

    target = rows[best_row_index - 1]
    while len(target) <= handled_index:
        target.append("")
    target[handled_index] = "TRUE" if handled else ""
    update_sheet(f"responses!A{best_row_index}:H{best_row_index}", [target[:8]])
    return True


def ensure_spreadsheet_schema():
    spreadsheet = sheets_api_request("GET", "", params={"fields": "sheets.properties.title"})
    existing_titles = {s["properties"]["title"] for s in spreadsheet.get("sheets", [])}

    requests = []
    for title in REQUIRED_SHEETS:
        if title not in existing_titles:
            requests.append({"addSheet": {"properties": {"title": title}}})

    if requests:
        sheets_api_request("POST", ":batchUpdate", json={"requests": requests})

    initialized = []
    for title, values in REQUIRED_SHEETS.items():
        rows = read_sheet(f"{title}!A1:H2")
        if not rows:
            update_sheet(f"{title}!A1", values)
            initialized.append(title)
        elif title == "responses" and rows[0] != values[0]:
            update_sheet("responses!A1:H1", values[:1])
            initialized.append(title)

    return initialized


def get_system_mode():
    rows = read_sheet(SYSTEM_MODE_RANGE)
    if len(rows) < 2 or not rows[1]:
        return "NORMAL"
    mode = str(rows[1][0]).strip().upper()
    return mode if mode in ["NORMAL", "DISASTER"] else "NORMAL"


def set_system_mode(mode):
    mode = str(mode).strip().upper()
    if mode not in ["NORMAL", "DISASTER"]:
        mode = "NORMAL"
    update_sheet("system_mode!A1:A2", [["mode"], [mode]])
