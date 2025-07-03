import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, base64, os

def get_worksheet(pagina):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_BASE64"]).decode()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1-J2mqcgSaq3-2CFVwXHzOvUGvKdYr31v7UT8da3r_OU/edit")
    return sheet.worksheet(pagina)
