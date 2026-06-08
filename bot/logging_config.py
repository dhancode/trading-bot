"""
Logging configuration for the trading bot.
Sets up structured logging to both console and rotating file handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging with a rotating file handler and a console handler.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Root logger configured for the bot.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers when module is re-imported
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Rotating file handler (10 MB max, keep 5 backups) ---
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)          # capture everything to file
    file_handler.setFormatter(formatter)

    # --- Console handler (INFO+ only) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
