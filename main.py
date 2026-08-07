import argparse
import logging
import sys

import config
from aggregate import build_daily_stats
from api_client import fetch_statistics
from db import clear_table, ensure_table, get_connection, insert_records
from email_notify import send_success_email
from logging_setup import LOGGER_NAME, cleanup_old_logs, setup_logging
from sheets_export import upload_daily_stats
from transform import parse_and_validate


def _parse_args():
    parser = argparse.ArgumentParser(
        description="ETL статистики грейдера → PostgreSQL",
    )
    parser.add_argument(
        "--start",
        default=config.START_DATE,
        help="Начало периода (по умолчанию START_DATE из .env)",
    )
    parser.add_argument(
        "--end",
        default=config.END_DATE,
        help="Конец периода (по умолчанию END_DATE из .env)",
    )
    return parser.parse_args()


def _log_config_summary(logger, start, end):
    logger.info("Сводка конфигурации (без паролей):")
    logger.info("  API URL:    %s", config.API_URL)
    logger.info("  DB host:    %s", config.POSTGRES_HOST)
    logger.info("  DB name:    %s", config.POSTGRES_DB)
    logger.info("  DB user:    %s", config.POSTGRES_USER)
    logger.info("  START_DATE: %s", start)
    logger.info("  END_DATE:   %s", end)
    logger.info("  LOGS_DIR:   %s", config.LOGS_DIR)


def main():
    logger = logging.getLogger(LOGGER_NAME)
    conn = None
    try:
        deleted = cleanup_old_logs()
        log_path = setup_logging()
        args = _parse_args()

        logger.info("Скрипт запущен")
        logger.info("Логирование инициализировано: %s", log_path)
        if deleted:
            logger.info(
                "Удалены устаревшие логи (%d): %s",
                len(deleted),
                ", ".join(p.name for p in deleted),
            )
        else:
            logger.info("Устаревших логов для удаления нет")

        _log_config_summary(logger, args.start, args.end)

        logger.info("Подключение к PostgreSQL…")
        conn = get_connection()
        ensure_table(conn)

        raw_records = fetch_statistics(args.start, args.end)
        valid_records = parse_and_validate(raw_records)
        skipped = len(raw_records) - len(valid_records)

        logger.info("Заполнение БД началось")
        clear_table(conn)
        inserted = insert_records(conn, valid_records)
        logger.info("Заполнение БД завершилось: %d строк", inserted)

        logger.info(
            "Итог: скачано=%d, валидных=%d, вставлено=%d, пропущено=%d",
            len(raw_records),
            len(valid_records),
            inserted,
            skipped,
        )

        stats = build_daily_stats(
            valid_records,
            downloaded=len(raw_records),
            inserted=inserted,
            skipped=skipped,
            period_start=args.start,
            period_end=args.end,
        )
        logger.info(
            "Метрики: report_date=%s, total=%s, success_rate=%s%%, "
            "users=%s, run=%s, submit=%s",
            stats.get("report_date"),
            stats.get("total_attempts"),
            stats.get("success_rate_pct"),
            stats.get("unique_users"),
            stats.get("run_attempts"),
            stats.get("submit_attempts"),
        )
        upload_daily_stats(stats)
        send_success_email(stats)

        logger.info("Скрипт успешно завершён")
        return 0
    except Exception:
        logger.exception("Непредвиденная ошибка при выполнении ETL")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
