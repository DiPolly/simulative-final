import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

API_URL = os.getenv("API_URL", "https://b2b.itresume.ru/api/statistics")
API_CLIENT = os.getenv("API_CLIENT", "Skillfactory")
API_CLIENT_KEY = os.getenv("API_CLIENT_KEY", "M2MGWS")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "grader_stats")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

START_DATE = os.getenv("START_DATE", "2023-05-31 00:00:00.000000")
END_DATE = os.getenv("END_DATE", "2023-05-31 23:59:59.999999")

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/google_service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_WORKSHEET_NAME = os.getenv("GOOGLE_WORKSHEET_NAME", "daily_stats")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.mail.ru")
SMTP_PORT = os.getenv("SMTP_PORT", "465")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

LOGS_DIR = Path(__file__).resolve().parent / "logs"
