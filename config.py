import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"

load_dotenv(PROJECT_ROOT / ".env")

_DEFAULTS = {
    "API_URL": "https://b2b.itresume.ru/api/statistics",
    "API_CLIENT": "Skillfactory",
    "API_CLIENT_KEY": "M2MGWS",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "grader_stats",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "your_password_here",
    "START_DATE": "2023-05-31 00:00:00.000000",
    "END_DATE": "2023-05-31 23:59:59.999999",
}


def _env(name):
    value = os.getenv(name, _DEFAULTS.get(name, "")).strip()
    if not value:
        raise RuntimeError(
            f"Не задана обязательная переменная окружения: {name}. "
            "Скопируйте .env.example в .env и заполните значения."
        )
    return value


def _env_optional(name, default=""):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip()


API_URL = _env("API_URL")
API_CLIENT = _env("API_CLIENT")
API_CLIENT_KEY = _env("API_CLIENT_KEY")

POSTGRES_HOST = _env("POSTGRES_HOST")
POSTGRES_PORT = _env("POSTGRES_PORT")
POSTGRES_DB = _env("POSTGRES_DB")
POSTGRES_USER = _env("POSTGRES_USER")
POSTGRES_PASSWORD = _env("POSTGRES_PASSWORD")

START_DATE = _env("START_DATE")
END_DATE = _env("END_DATE")

GOOGLE_CREDENTIALS_PATH = _env_optional("GOOGLE_CREDENTIALS_PATH")
GOOGLE_SHEET_ID = _env_optional("GOOGLE_SHEET_ID")
GOOGLE_WORKSHEET_NAME = _env_optional("GOOGLE_WORKSHEET_NAME", "daily_stats")
GOOGLE_SHEETS_ENABLED = _env_optional("GOOGLE_SHEETS_ENABLED")

SMTP_SERVER = _env_optional("SMTP_SERVER", "smtp.mail.ru")
SMTP_PORT = _env_optional("SMTP_PORT", "465")
SMTP_USER = _env_optional("SMTP_USER")
SMTP_PASSWORD = _env_optional("SMTP_PASSWORD")
EMAIL_TO = _env_optional("EMAIL_TO")
EMAIL_ENABLED = _env_optional("EMAIL_ENABLED")


def get_dsn():
    return (
        f"host={POSTGRES_HOST} "
        f"port={POSTGRES_PORT} "
        f"dbname={POSTGRES_DB} "
        f"user={POSTGRES_USER} "
        f"password={POSTGRES_PASSWORD}"
    )


DB_DSN = get_dsn()
