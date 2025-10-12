"""Logging configuration for the application."""

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        # Base log data
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra context from record
        for attr in [
            'user_id',
            'run_id',
            'group_id',
            'request_id',
            'path',
            'method',
            'status_code',
            'duration_ms',
        ]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        return json.dumps(log_data)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured log messages for development."""

    def format(self, record: logging.LogRecord) -> str:
        # Base log data
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra context from record
        for attr in [
            'user_id',
            'run_id',
            'group_id',
            'request_id',
            'path',
            'method',
            'status_code',
            'duration_ms',
        ]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        # Format as key=value pairs for easy parsing
        parts = []
        for key, value in log_data.items():
            if isinstance(value, str) and (' ' in value or '=' in value):
                parts.append(f'{key}="{value}"')
            else:
                parts.append(f'{key}={value}')

        return ' '.join(parts)


def setup_logging(level: str = 'INFO') -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    env = os.getenv('ENV', 'development')
    log_format = os.getenv('LOG_FORMAT', 'structured')
    log_file = os.getenv('LOG_FILE', '')

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Choose formatter based on environment and configuration
    if log_format == 'json' or env == 'production':
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if LOG_FILE is set)
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding structured logging context."""

    def __init__(self, logger: logging.Logger, **kwargs: Any):
        self.logger = logger
        self.context = kwargs
        self.old_factory = None

    def __enter__(self) -> 'LogContext':
        old_factory = logging.getLogRecordFactory()
        self.old_factory = old_factory

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)
