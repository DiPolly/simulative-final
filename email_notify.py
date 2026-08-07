import logging
import smtplib
import ssl
from email.message import EmailMessage

import config


def send_success_email(stats):
    if not config.SMTP_USER or not config.SMTP_PASSWORD or not config.EMAIL_TO:
        logging.warning("Письмо пропущено: нет настроек почты")
        return

    text = "Скрипт отработал.\n\n"
    for key, value in stats.items():
        text += f"{key}: {value}\n"

    msg = EmailMessage()
    msg["Subject"] = f"Отчёт грейдера за {stats.get('report_date', '')}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.EMAIL_TO
    msg.set_content(text)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_SERVER, int(config.SMTP_PORT), context=context) as server:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        logging.info("Письмо отправлено")
    except Exception as e:
        logging.error("Ошибка отправки письма: %s", e)
