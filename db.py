import logging

import psycopg2

import config


def get_connection():
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def ensure_table(conn):
    with conn.cursor() as cur:
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


def clear_table(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE attempts")
    conn.commit()


def insert_records(conn, records):
    if not records:
        return

    sql = """
        INSERT INTO attempts (
            user_id,
            oauth_consumer_key,
            lis_result_sourcedid,
            lis_outcome_service_url,
            is_correct,
            attempt_type,
            created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    rows = [
        (
            r["user_id"],
            r["oauth_consumer_key"],
            r["lis_result_sourcedid"],
            r["lis_outcome_service_url"],
            r["is_correct"],
            r["attempt_type"],
            r["created_at"],
        )
        for r in records
    ]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
