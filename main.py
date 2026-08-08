import ast
import logging
import os
import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import gspread
import psycopg2
import requests
from google.oauth2.service_account import Credentials

import config


def setup_logging():
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)

    today = date.today()
    for name in os.listdir(logs_dir):
        if not name.endswith(".log"):
            continue
        try:
            file_date = date.fromisoformat(name.replace(".log", ""))
        except ValueError:
            continue
        if file_date < today - timedelta(days=3):
            os.remove(os.path.join(logs_dir, name))

    log_file = os.path.join(logs_dir, str(today) + ".log")
    logging.basicConfig(
        level=logging.INFO,
        filename=log_file,
        filemode="a",
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def fetch_statistics(start, end):
    logging.info("Скачивание началось")
    response = requests.get(
        config.API_URL,
        params={
            "client": config.API_CLIENT,
            "client_key": config.API_CLIENT_KEY,
            "start": start,
            "end": end,
        },
        timeout=120,
    )
    if response.status_code != 200:
        logging.error("Ошибка доступа к API, status_code=%s", response.status_code)
        response.raise_for_status()
    data = response.json()
    logging.info("Скачивание завершилось, записей: %s", len(data))
    return data


def clean_one(row):
    passback = ast.literal_eval(row["passback_params"])

    user_id = row.get("lti_user_id")
    sourcedid = passback.get("lis_result_sourcedid")
    outcome_url = passback.get("lis_outcome_service_url")
    attempt_type = row.get("attempt_type")
    created_at = row.get("created_at")

    if not user_id or not sourcedid or not outcome_url or not attempt_type or not created_at:
        raise ValueError("нет обязательных полей")

    is_correct = row.get("is_correct")
    if is_correct in (0, 1):
        is_correct = bool(is_correct)

    try:
        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

    return {
        "user_id": user_id,
        "oauth_consumer_key": passback.get("oauth_consumer_key") or "",
        "lis_result_sourcedid": sourcedid,
        "lis_outcome_service_url": outcome_url,
        "is_correct": is_correct,
        "attempt_type": attempt_type,
        "created_at": created_at,
    }


def parse_and_validate(raw_records):
    result = []
    for i, row in enumerate(raw_records):
        try:
            result.append(clean_one(row))
        except Exception as e:
            logging.warning("Пропущена запись %s: %s", i, e)
    return result


def get_connection():
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def ensure_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            oauth_consumer_key TEXT,
            lis_result_sourcedid TEXT NOT NULL,
            lis_outcome_service_url TEXT NOT NULL,
            is_correct BOOLEAN NULL,
            attempt_type TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """
    )
    conn.commit()
    cur.close()


def clear_table(conn):
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE attempts")
    conn.commit()
    cur.close()


def insert_records(conn, records):
    cur = conn.cursor()
    sql = """
        INSERT INTO attempts (
            user_id, oauth_consumer_key, lis_result_sourcedid,
            lis_outcome_service_url, is_correct, attempt_type, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    for r in records:
        cur.execute(
            sql,
            (
                r["user_id"],
                r["oauth_consumer_key"],
                r["lis_result_sourcedid"],
                r["lis_outcome_service_url"],
                r["is_correct"],
                r["attempt_type"],
                r["created_at"],
            ),
        )
    conn.commit()
    cur.close()


def build_daily_stats(records, start, end):
    total = len(records)
    success = 0
    users = set()
    runs = 0
    submits = 0

    for row in records:
        if row["is_correct"] is True:
            success += 1
        users.add(row["user_id"])
        if row["attempt_type"] == "run":
            runs += 1
        elif row["attempt_type"] == "submit":
            submits += 1

    if total > 0:
        rate = round(success / total * 100, 2)
    else:
        rate = 0

    return {
        "report_date": start[:10],
        "total_attempts": total,
        "successful_attempts": success,
        "success_rate_pct": rate,
        "unique_users": len(users),
        "run_attempts": runs,
        "submit_attempts": submits,
        "period_start": start,
        "period_end": end,
    }


def upload_daily_stats(stats):
    if not config.GOOGLE_SHEET_ID:
        logging.warning("Google Sheets пропущен: нет GOOGLE_SHEET_ID")
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

        try:
            worksheet = spreadsheet.worksheet(config.GOOGLE_WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=config.GOOGLE_WORKSHEET_NAME, rows=1000, cols=20
            )

        headers = list(stats.keys())
        values = list(stats.values())
        if not worksheet.row_values(1):
            worksheet.append_row(headers)
        worksheet.append_row(values)
        logging.info("Данные записаны в Google Sheets")
    except Exception as e:
        logging.error("Ошибка Google Sheets: %s", e)


def send_success_email(stats):
    if not config.SMTP_USER or not config.SMTP_PASSWORD or not config.EMAIL_TO:
        logging.warning("Письмо пропущено: нет настроек почты")
        return

    text = "Скрипт отработал.\n\n"
    for key, value in stats.items():
        text += f"{key}: {value}\n"

    msg = EmailMessage()
    msg["Subject"] = "Отчёт грейдера за " + str(stats.get("report_date", ""))
    msg["From"] = config.SMTP_USER
    msg["To"] = config.EMAIL_TO
    msg.set_content(text)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            config.SMTP_SERVER, int(config.SMTP_PORT), context=context
        ) as server:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        logging.info("Письмо отправлено")
    except Exception as e:
        logging.error("Ошибка отправки письма: %s", e)


def main():
    setup_logging()

    conn = get_connection()
    ensure_table(conn)

    raw = fetch_statistics(config.START_DATE, config.END_DATE)
    records = parse_and_validate(raw)

    logging.info("Заполнение базы началось")
    clear_table(conn)
    insert_records(conn, records)
    logging.info("Заполнение базы завершилось")

    stats = build_daily_stats(records, config.START_DATE, config.END_DATE)
    upload_daily_stats(stats)
    send_success_email(stats)

    conn.close()


if __name__ == "__main__":
    main()
