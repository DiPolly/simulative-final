import logging

import psycopg2
from psycopg2.extras import execute_batch

import config
from logging_setup import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attempts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    oauth_consumer_key TEXT,
    lis_result_sourcedid TEXT NOT NULL,
    lis_outcome_service_url TEXT NOT NULL,
    is_correct BOOLEAN NULL,
    attempt_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
"""

_INSERT_SQL = """
INSERT INTO attempts (
    user_id,
    oauth_consumer_key,
    lis_result_sourcedid,
    lis_outcome_service_url,
    is_correct,
    attempt_type,
    created_at
) VALUES (
    %(user_id)s,
    %(oauth_consumer_key)s,
    %(lis_result_sourcedid)s,
    %(lis_outcome_service_url)s,
    %(is_correct)s,
    %(attempt_type)s,
    %(created_at)s
);
"""


def get_connection():
    return psycopg2.connect(config.get_dsn())


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(_CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Таблица attempts готова (CREATE TABLE IF NOT EXISTS)")


def clear_table(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE attempts RESTART IDENTITY;")
    conn.commit()
    logger.info("Таблица attempts очищена (TRUNCATE)")


def insert_records(conn, records):
    if not records:
        logger.info("Нет записей для вставки")
        return 0

    try:
        with conn.cursor() as cur:
            execute_batch(cur, _INSERT_SQL, records, page_size=500)
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Ошибка при вставке записей в PostgreSQL")
        raise

    return len(records)
