import logging
import smtplib
import ssl
from email.message import EmailMessage

import config
from logging_setup import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def _flag_is_false(value):
    return value.strip().lower() in ("false", "0", "no", "off")


def is_email_configured():
    if _flag_is_false(config.EMAIL_ENABLED):
        return False
    return bool(
        config.SMTP_USER.strip()
        and config.SMTP_PASSWORD.strip()
        and config.EMAIL_TO.strip()
    )


def _build_body(stats):
    lines = [
        "ETL грейдера успешно завершён.",
        "",
        "Сводка метрик:",
    ]
    labels = {
        "report_date": "Дата отчёта",
        "period_start": "Начало периода",
        "period_end": "Конец периода",
        "total_attempts": "Всего попыток",
        "successful_attempts": "Успешные попытки",
        "failed_attempts": "Неуспешные попытки",
        "null_correct_attempts": "Попытки без is_correct (часто run)",
        "success_rate_pct": "Доля успеха, %",
        "unique_users": "Уникальных пользователей",
        "run_attempts": "Попытки run",
        "submit_attempts": "Попытки submit",
        "other_attempt_types": "Прочие типы попыток",
        "downloaded": "Скачано из API",
        "inserted": "Вставлено в БД",
        "skipped": "Пропущено при валидации",
        "generated_at": "Сформировано",
    }
    for key, value in stats.items():
        label = labels.get(key, key)
        lines.append(f"  {label}: {value}")
    lines.append("")
    lines.append("Это автоматическое письмо, пароли и ключи в нём не передаются.")
    return "\n".join(lines)


def send_success_email(stats):
    if not is_email_configured():
        logger.warning(
            "Email-уведомление пропущено: не заданы SMTP_USER / SMTP_PASSWORD / "
            "EMAIL_TO (или EMAIL_ENABLED=false)"
        )
        return

    report_date = stats.get("report_date", "")
    msg = EmailMessage()
    msg["Subject"] = f"ETL грейдера: отчёт за {report_date}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.EMAIL_TO
    msg.set_content(_build_body(stats))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            config.SMTP_SERVER,
            int(config.SMTP_PORT),
            context=context,
        ) as server:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(
            "Email-уведомление отправлено на %s (report_date=%s)",
            config.EMAIL_TO,
            report_date,
        )
    except Exception:
        logger.exception(
            "Ошибка отправки email (БД уже загружена, ETL не прерывается)"
        )
