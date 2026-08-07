import logging

import config
from aggregate import build_daily_stats
from api_client import fetch_statistics
from db import clear_table, ensure_table, get_connection, insert_records
from email_notify import send_success_email
from logging_setup import cleanup_old_logs, setup_logging
from sheets_export import upload_daily_stats
from transform import parse_and_validate


def main():
    cleanup_old_logs()
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
