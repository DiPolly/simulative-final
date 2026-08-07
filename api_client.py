import logging

import requests

import config


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
