import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import config


def cleanup_old_logs():
    logs_dir = config.LOGS_DIR
    if not logs_dir.is_dir():
        return

    cutoff = date.today() - timedelta(days=3)
    for path in logs_dir.iterdir():
        if path.suffix != ".log":
            continue
        try:
            file_date = date.fromisoformat(path.stem)
        except ValueError:
            file_date = datetime.fromtimestamp(path.stat().st_mtime).date()
        if file_date < cutoff:
            path.unlink()


def setup_logging():
    config.LOGS_DIR.mkdir(exist_ok=True)
    log_path = config.LOGS_DIR / f"{date.today().isoformat()}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
