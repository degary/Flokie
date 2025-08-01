"""
Logging configuration utilities for structured logging setup.

This module provides utilities for configuring structured logging with JSON format
support and proper log level management.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime

from flask import g, has_request_context, request


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """

    def format(self, record):
        """
        Format log record as JSON.

        Args:
            record: LogRecord instance

        Returns:
            str: JSON formatted log message
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if has_request_context():
            log_data.update(
                {
                    "request_id": getattr(g, "request_id", None),
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                }
            )

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


def configure_logging(app):
    """
    Configure application logging based on configuration.

    Args:
        app (Flask): Flask application instance
    """
    # Skip logging configuration in Flask reloader process to avoid duplicate logs
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return

    # Get logging configuration
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper())
    log_format = app.config.get("LOG_FORMAT")
    use_json_format = app.config.get("LOG_JSON_FORMAT", False)
    log_file = app.config.get("LOG_FILE")
    max_bytes = app.config.get("LOG_MAX_BYTES", 10485760)
    backup_count = app.config.get("LOG_BACKUP_COUNT", 5)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set root logger level
    root_logger.setLevel(log_level)

    # Create formatter
    if use_json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure Flask's logger
    app.logger.setLevel(log_level)

    # Configure werkzeug logger (Flask's built-in server)
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)  # Reduce werkzeug noise

    # Configure SQLAlchemy logger
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    if app.config.get("SQLALCHEMY_ECHO", False):
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)

    app.logger.info(f"Logging configured - Level: {log_level}, JSON: {use_json_format}")


def get_logger(name):
    """
    Get a logger instance with the specified name.

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class RequestContextFilter(logging.Filter):
    """
    Logging filter to add request context to log records.
    """

    def filter(self, record):
        """
        Add request context to log record.

        Args:
            record: LogRecord instance

        Returns:
            bool: True to include the record
        """
        if has_request_context():
            record.request_id = getattr(g, "request_id", "unknown")
            record.method = request.method
            record.path = request.path
            record.remote_addr = request.remote_addr
        else:
            record.request_id = None
            record.method = None
            record.path = None
            record.remote_addr = None

        return True
