"""Клиент API статистики грейдера (GET /api/statistics)."""

from __future__ import annotations

import logging
from typing import Any

import requests

import config
from logging_setup import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_REQUEST_TIMEOUT = 120


def fetch_statistics(start: str, end: str) -> list[Any]:
    """
    Скачать статистику за период [start, end] (формат дат как в API).

    Возвращает список словарей. При HTTP/JSON-ошибках логирует ERROR и бросает исключение.
    """
    logger.info("Скачивание статистики началось: start=%s, end=%s", start, end)

    params = {
        "client": config.API_CLIENT,
        "client_key": config.API_CLIENT_KEY,
        "start": start,
        "end": end,
    }

    try:
        response = requests.get(config.API_URL, params=params, timeout=_REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        logger.error("Ошибка сети при запросе к API: %s", exc)
        raise

    if not response.ok:
        logger.error(
            "Ошибка HTTP при скачивании статистики: status_code=%s, body=%s",
            response.status_code,
            response.text[:500],
        )
        raise RuntimeError(
            f"API вернул ошибку HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Ответ API не является JSON: %s", exc)
        raise RuntimeError("Ответ API не является валидным JSON") from exc

    if not isinstance(data, list):
        logger.error(
            "Неожиданный тип ответа API: ожидался list, получено %s",
            type(data).__name__,
        )
        raise RuntimeError(
            f"Ожидался список записей, получено: {type(data).__name__}"
        )

    logger.info("Скачивание статистики завершилось: %d записей", len(data))
    return data
