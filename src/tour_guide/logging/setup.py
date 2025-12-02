"""Logging setup with rotation."""

import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional

from tour_guide.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "poi"):
            log_data["poi"] = record.poi
        if hasattr(record, "execution_time"):
            log_data["execution_time"] = record.execution_time

        return json.dumps(log_data)


_initialized = False


def setup_logging(log_dir: Optional[Path] = None, console: bool = True) -> None:
    """Setup logging with rotation."""
    global _initialized

    if _initialized:
        return

    settings = get_settings()
    log_dir = log_dir or Path("logs")
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger("tour_guide")
    root_logger.setLevel(getattr(logging, settings.logging.level))

    # File handler with rotation
    log_file = log_dir / f"tour_guide_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=settings.logging.max_bytes,
        backupCount=settings.logging.backup_count,
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a component."""
    setup_logging()
    return logging.getLogger(f"tour_guide.{name}")


def reset_logging():
    """Reset logging (for testing)."""
    global _initialized
    logger = logging.getLogger("tour_guide")
    logger.handlers.clear()
    _initialized = False
