from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from core.config_manager import load_settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

PATIENTS_RANGE = "patients!A:D"
PENDING_RANGE = "pending_users!A:D"
RESPONSES_RANGE = "responses!A:G"
SYSTEM_MODE_RANGE = "system_mode!A:A"


def get_sheets_service():
    s = load_settings()
    creds = Credentials.from_service_account_file(
        s["google"]["service_account_file"],
        scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def get_spreadsheet_id():
    s = load_settings()
    return s["google"]["spreadsheet_id"]


def read_sheet(range_name):
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=get_spreadsheet_id(),
        range=range_name
    ).execute()
    return result.get("values", [])


def append_sheet(range_name, row_values):
    service = get_sheets_service()
    body = {"values": [row_values]}
    service.spreadsheets().values().append(
        spreadsheetId=get_spreadsheet_id(),
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()


def update_sheet(range_name, values):
    service = get_sheets_service()
    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=get_spreadsheet_id(),
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()


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
    from datetime import datetime
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
    return mode if mode in ["NORMAL", "DISASTER"] else "NORMAL"


def set_system_mode(mode):
    mode = str(mode).strip().upper()
    if mode not in ["NORMAL", "DISASTER"]:
        mode = "NORMAL"
    update_sheet("system_mode!A1:A2", [["mode"], [mode]])
