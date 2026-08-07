import ast
import json
import logging
import re
from datetime import datetime

from logging_setup import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_CREATED_AT_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
)


def _parse_passback_params(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("passback_params пуст или не строка")

    text = raw.strip()
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        normalized = text
        if normalized.startswith("'") and normalized.endswith("'"):
            normalized = normalized[1:-1]
        normalized = re.sub(r"(?<!\\)'", '"', normalized)
        try:
            value = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise ValueError(f"не удалось разобрать passback_params: {exc}") from exc

    if not isinstance(value, dict):
        raise ValueError(
            f"passback_params должен быть dict, получено {type(value).__name__}"
        )
    return value


def _normalize_is_correct(raw):
    if raw is None or isinstance(raw, bool):
        return raw
    if raw == 0 or raw == 1:
        return bool(raw)
    raise ValueError("is_correct должен быть bool, 0/1 или None")


def _parse_created_at(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("created_at пуст или не строка")
    text = raw.strip()
    for fmt in _CREATED_AT_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"не удалось разобрать created_at: {text!r}")


def _non_empty_str(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} должен быть непустой строкой")
    return value


def _validate_record(raw, _index):
    if not isinstance(raw, dict):
        raise ValueError(f"запись не dict (тип {type(raw).__name__})")

    user_id = _non_empty_str(raw.get("lti_user_id"), "lti_user_id")

    passback = _parse_passback_params(raw.get("passback_params"))

    oauth_raw = passback.get("oauth_consumer_key", "")
    if oauth_raw is None:
        oauth_consumer_key = ""
    elif isinstance(oauth_raw, str):
        oauth_consumer_key = oauth_raw
    else:
        raise ValueError("oauth_consumer_key должен быть строкой")

    lis_result_sourcedid = _non_empty_str(
        passback.get("lis_result_sourcedid"), "lis_result_sourcedid"
    )
    lis_outcome_service_url = _non_empty_str(
        passback.get("lis_outcome_service_url"), "lis_outcome_service_url"
    )

    is_correct = _normalize_is_correct(raw.get("is_correct"))

    attempt_type = _non_empty_str(raw.get("attempt_type"), "attempt_type")
    created_at = _parse_created_at(raw.get("created_at"))

    return {
        "user_id": user_id,
        "oauth_consumer_key": oauth_consumer_key,
        "lis_result_sourcedid": lis_result_sourcedid,
        "lis_outcome_service_url": lis_outcome_service_url,
        "is_correct": is_correct,
        "attempt_type": attempt_type,
        "created_at": created_at,
    }


def parse_and_validate(raw_records):
    accepted = []
    skipped = 0

    for index, raw in enumerate(raw_records):
        user_id_hint = None
        try:
            if isinstance(raw, dict):
                maybe_uid = raw.get("lti_user_id")
                if isinstance(maybe_uid, str) and maybe_uid:
                    user_id_hint = maybe_uid
            record = _validate_record(raw, index)
        except Exception as exc:
            skipped += 1
            if user_id_hint:
                logger.warning(
                    "Пропущена запись [%d], user_id=%s: %s",
                    index,
                    user_id_hint,
                    exc,
                )
            else:
                logger.warning("Пропущена запись [%d]: %s", index, exc)
            continue
        accepted.append(record)

    logger.info(
        "Валидация завершена: принято %d, пропущено %d",
        len(accepted),
        skipped,
    )
    return accepted
