import logging
from pathlib import Path

import config
from aggregate import stats_as_rows
from logging_setup import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)


def _flag_is_false(value):
    return value.strip().lower() in ("false", "0", "no", "off")


def _flag_is_true(value):
    return value.strip().lower() in ("true", "1", "yes", "on")


def is_sheets_configured():
    path = config.GOOGLE_CREDENTIALS_PATH.strip()
    sheet_id = config.GOOGLE_SHEET_ID.strip()
    flag = config.GOOGLE_SHEETS_ENABLED.strip()

    if _flag_is_false(flag):
        return False
    if _flag_is_true(flag):
        return bool(path and sheet_id)
    return bool(path and sheet_id)


def upload_daily_stats(stats):
    if not is_sheets_configured():
        logger.warning(
            "Google Sheets пропущен: не заданы GOOGLE_CREDENTIALS_PATH / "
            "GOOGLE_SHEET_ID (или GOOGLE_SHEETS_ENABLED=false)"
        )
        return

    try:
        _upload(stats)
    except Exception:
        logger.exception(
            "Ошибка выгрузки в Google Sheets (БД уже загружена, ETL не прерывается)"
        )


def _upload(stats):
    import gspread
    from google.oauth2.service_account import Credentials

    creds_path = Path(config.GOOGLE_CREDENTIALS_PATH).expanduser()
    if not creds_path.is_file():
        logger.warning(
            "Google Sheets пропущен: файл credentials не найден: %s",
            creds_path,
        )
        return

    credentials = Credentials.from_service_account_file(
        str(creds_path),
        scopes=_SCOPES,
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)

    worksheet_name = config.GOOGLE_WORKSHEET_NAME or "daily_stats"
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=max(20, len(stats)),
        )
        logger.info("Создан лист Google Sheets: %s", worksheet_name)

    headers, data_rows = stats_as_rows(stats)
    first_row = worksheet.row_values(1)

    if not first_row:
        worksheet.append_rows([headers] + data_rows, value_input_option="USER_ENTERED")
    else:
        if first_row != headers:
            worksheet.update(
                [headers],
                "A1",
                value_input_option="USER_ENTERED",
            )
            logger.info(
                "Обновлён заголовок листа Google Sheets: %s",
                worksheet_name,
            )
        worksheet.append_rows(data_rows, value_input_option="USER_ENTERED")

    logger.info(
        "Статистика выгружена в Google Sheets (лист=%s, report_date=%s)",
        worksheet_name,
        stats.get("report_date"),
    )
