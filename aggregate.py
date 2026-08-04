from __future__ import annotations

from collections import Counter, OrderedDict
from datetime import date, datetime
from typing import Any, Dict, List, Tuple


def _date_part(value: str) -> str:
    text = (value or "").strip()
    if len(text) >= 10:
        return text[:10]
    return text


def _report_date(records: list[dict[str, Any]], period_start: str) -> str:
    from_period = _date_part(period_start)
    if from_period:
        try:
            date.fromisoformat(from_period)
            return from_period
        except ValueError:
            pass

    counts: Counter[str] = Counter()
    for record in records:
        created = record.get("created_at")
        if isinstance(created, datetime):
            counts[created.date().isoformat()] += 1
        elif isinstance(created, date):
            counts[created.isoformat()] += 1
        elif isinstance(created, str) and len(created) >= 10:
            counts[created[:10]] += 1

    if counts:
        return counts.most_common(1)[0][0]
    return date.today().isoformat()


def build_daily_stats(
    records: list[dict[str, Any]],
    *,
    downloaded: int,
    inserted: int,
    skipped: int,
    period_start: str,
    period_end: str,
) -> Dict[str, Any]:
    total_attempts = len(records)
    successful = 0
    failed = 0
    null_correct = 0
    run_attempts = 0
    submit_attempts = 0
    other_attempt_types = 0
    users: set[str] = set()

    for record in records:
        is_correct = record.get("is_correct")
        if is_correct is True:
            successful += 1
        elif is_correct is False:
            failed += 1
        else:
            null_correct += 1

        attempt_type = record.get("attempt_type")
        if attempt_type == "run":
            run_attempts += 1
        elif attempt_type == "submit":
            submit_attempts += 1
        else:
            other_attempt_types += 1

        user_id = record.get("user_id")
        if user_id is not None and user_id != "":
            users.add(str(user_id))

    if total_attempts:
        success_rate_pct = round(successful / total_attempts * 100, 2)
    else:
        success_rate_pct = 0.0

    return OrderedDict(
        [
            ("report_date", _report_date(records, period_start)),
            ("period_start", period_start),
            ("period_end", period_end),
            ("total_attempts", total_attempts),
            ("successful_attempts", successful),
            ("failed_attempts", failed),
            ("null_correct_attempts", null_correct),
            ("success_rate_pct", success_rate_pct),
            ("unique_users", len(users)),
            ("run_attempts", run_attempts),
            ("submit_attempts", submit_attempts),
            ("other_attempt_types", other_attempt_types),
            ("downloaded", downloaded),
            ("inserted", inserted),
            ("skipped", skipped),
            ("generated_at", datetime.now().isoformat(timespec="seconds")),
        ]
    )


def stats_as_rows(stats: dict) -> Tuple[List[str], List[List[Any]]]:
    headers = list(stats.keys())
    row = [stats[key] for key in headers]
    return headers, [row]
