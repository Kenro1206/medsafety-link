import os
import json
from datetime import datetime
from urllib.parse import quote

from core.config_manager import load_settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

PATIENTS_RANGE = "patients!A:D"
PENDING_RANGE = "pending_users!A:D"
RESPONSES_RANGE = "responses!A:G"
SYSTEM_MODE_RANGE = "system_mode!A:A"


def get_credentials():
    from google.oauth2.service_account import Credentials

    json_str = os.getenv("GOOGLE_SERVICE_JSON", "").strip()

    if json_str:
        info = json.loads(json_str)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    s = load_settings()
    service_account_file = s.get("google", {}).get("service_account_file", "").strip()

    if not service_account_file:
        raise ValueError("Google認証情報が未設定です。GOOGLE_SERVICE_JSON または service_account_file を設定してください。")

    return Credentials.from_service_account_file(service_account_file, scopes=SCOPES)


def get_authorized_session():
    from google.auth.transport.requests import AuthorizedSession

    creds = get_credentials()
    return AuthorizedSession(creds)


def sheets_api_request(method, path, **kwargs):
    session = get_authorized_session()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{get_spreadsheet_id()}{path}"
    response = session.request(method, url, timeout=20, **kwargs)
    if response.status_code >= 400:
        raise ValueError(f"Google Sheets API error: status={response.status_code}, body={response.text}")
    if response.text:
        return response.json()
    return {}


def get_spreadsheet_id():
    s = load_settings()
    spreadsheet_id = s.get("google", {}).get("spreadsheet_id", "").strip()

    if not spreadsheet_id:
        raise ValueError("スプレッドシートIDが未設定です。")

    return spreadsheet_id


def read_sheet(range_name):
    result = sheets_api_request("GET", f"/values/{quote(range_name, safe='')}")
    return result.get("values", [])


def append_sheet(range_name, row_values):
    body = {"values": [row_values]}
    sheets_api_request(
        "POST",
        f"/values/{quote(range_name, safe='')}:append",
        params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
        json=body
    )


def update_sheet(range_name, values):
    body = {"values": values}
    sheets_api_request(
        "PUT",
        f"/values/{quote(range_name, safe='')}",
        params={"valueInputOption": "USER_ENTERED"},
        json=body
    )


def rows_to_dicts(rows):
    if len(rows) < 2:
        return []

    headers = rows[0]
    data = []

    for row in rows[1:]:
        d = {}
        for i, h in enumerate(headers):
            d[h] = row[i] if i < len(row) else ""
        data.append(d)

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
        label
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


def get_system_mode():
    rows = read_sheet(SYSTEM_MODE_RANGE)

    if len(rows) < 2 or not rows[1]:
        return "NORMAL"

    mode = str(rows[1][0]).strip().upper()

    if mode not in ["NORMAL", "DISASTER"]:
        return "NORMAL"

    return mode


def set_system_mode(mode):
    mode = str(mode).strip().upper()

    if mode not in ["NORMAL", "DISASTER"]:
        mode = "NORMAL"

    update_sheet("system_mode!A1:A2", [["mode"], [mode]])
