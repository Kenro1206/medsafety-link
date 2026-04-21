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


def get_system_mode():
    rows = read_sheet(SYSTEM_MODE_RANGE)
    if len(rows) < 2 or not rows[1]:
        return "NORMAL"
    mode = str(rows[1][0]).strip().upper()
    return mode if mode in ["NORMAL", "DISASTER"] else "NORMAL"
