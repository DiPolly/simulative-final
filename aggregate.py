from datetime import datetime


def build_daily_stats(records, start, end):
    total = len(records)
    success = 0
    users = set()
    runs = 0
    submits = 0

    for row in records:
        if row["is_correct"] is True:
            success += 1
        users.add(row["user_id"])
        if row["attempt_type"] == "run":
            runs += 1
        elif row["attempt_type"] == "submit":
            submits += 1

    rate = round(success / total * 100, 2) if total else 0

    return {
        "report_date": start[:10],
        "period_start": start,
        "period_end": end,
        "total_attempts": total,
        "successful_attempts": success,
        "success_rate_pct": rate,
        "unique_users": len(users),
        "run_attempts": runs,
        "submit_attempts": submits,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
