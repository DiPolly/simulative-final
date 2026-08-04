from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import config

LOGGER_NAME = "grader_etl"
_LOG_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.log$")
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"


def cleanup_old_logs(
    logs_dir: Path | None = None,
    keep_days: int = 3,
) -> list[Path]:
    directory = logs_dir if logs_dir is not None else config.LOGS_DIR
    if not directory.is_dir():
        return []

    cutoff = date.today() - timedelta(days=keep_days)
    deleted: list[Path] = []

    for path in directory.iterdir():
        if not path.is_file() or path.suffix != ".log":
            continue

        match = _LOG_FILENAME_RE.match(path.name)
        if match:
            try:
                file_date = date.fromisoformat(match.group(1))
            except ValueError:
                file_date = datetime.fromtimestamp(path.stat().st_mtime).date()
        else:
            file_date = datetime.fromtimestamp(path.stat().st_mtime).date()

        if file_date < cutoff:
            path.unlink(missing_ok=True)
            deleted.append(path)

    return deleted


def setup_logging(logs_dir: Path | None = None) -> Path:
    directory = logs_dir if logs_dir is not None else config.LOGS_DIR
    directory.mkdir(parents=True, exist_ok=True)

    log_path = directory / f"{date.today().isoformat()}.log"
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    resolved = str(log_path.resolve())

    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None) == resolved
        for handler in logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    has_stream_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return log_path
