import ast
import logging
from datetime import datetime


def parse_passback(text):
    return ast.literal_eval(text)


def parse_created_at(text):
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError("неправильная дата")


def clean_one(row):
    passback = parse_passback(row["passback_params"])

    user_id = row.get("lti_user_id")
    sourcedid = passback.get("lis_result_sourcedid")
    outcome_url = passback.get("lis_outcome_service_url")
    attempt_type = row.get("attempt_type")
    created_at = row.get("created_at")

    if not user_id or not sourcedid or not outcome_url or not attempt_type or not created_at:
        raise ValueError("нет обязательных полей")

    is_correct = row.get("is_correct")
    if is_correct in (0, 1):
        is_correct = bool(is_correct)

    return {
        "user_id": user_id,
        "oauth_consumer_key": passback.get("oauth_consumer_key") or "",
        "lis_result_sourcedid": sourcedid,
        "lis_outcome_service_url": outcome_url,
        "is_correct": is_correct,
        "attempt_type": attempt_type,
        "created_at": parse_created_at(created_at),
    }


def parse_and_validate(raw_records):
    result = []
    for i, row in enumerate(raw_records):
        try:
            result.append(clean_one(row))
        except Exception as e:
            logging.warning("Пропущена запись %s: %s", i, e)
    return result
