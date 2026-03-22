"""Centralized logging setup for Prompt-Iterator."""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        _setup(logger)
    return logger


def _setup(logger: logging.Logger) -> None:
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Always log INFO+ to stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # Attempt file logging – non-critical, skip silently if dirs not ready
    try:
        from config import LOGS_DIR, ensure_data_dirs
        ensure_data_dirs()
        log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass
