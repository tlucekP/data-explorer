"""Centralized local logging for the data explorer app."""

from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_NAME = "data_explorer"
_IS_CONFIGURED = False


def setup_logging() -> logging.Logger:
    """Configure logger once and return app logger."""
    global _IS_CONFIGURED
    logger = logging.getLogger(_LOGGER_NAME)
    if _IS_CONFIGURED:
        return logger

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(file_handler)

    _IS_CONFIGURED = True
    return logger

