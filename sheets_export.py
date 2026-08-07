import logging
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

import config


def upload_daily_stats(stats):
    if not config.GOOGLE_SHEET_ID or not config.GOOGLE_CREDENTIALS_PATH:
        logging.warning("Google Sheets пропущен: нет настроек")
        return

    creds_path = Path(config.GOOGLE_CREDENTIALS_PATH)
    if not creds_path.is_file():
        logging.warning("Google Sheets пропущен: нет файла ключа")
        return

    try:
        creds = Credentials.from_service_account_file(
            str(creds_path),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)

        sheet_name = config.GOOGLE_WORKSHEET_NAME or "daily_stats"
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

        headers = list(stats.keys())
        values = list(stats.values())

        if not worksheet.row_values(1):
            worksheet.append_row(headers)
        worksheet.append_row(values)

        logging.info("Данные записаны в Google Sheets")
    except Exception as e:
        logging.error("Ошибка Google Sheets: %s", e)
