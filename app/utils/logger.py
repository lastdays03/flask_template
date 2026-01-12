"""Logging configuration."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logging(app):
    """Set up application logging."""

    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # File handler for all logs
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)

    # File handler for errors
    error_handler = RotatingFileHandler(
        "logs/error.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)

    # Stream handler (stdout) for Docker logs
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(json_formatter)

    # Sensitive Data Filter
    class SensitiveDataFilter(logging.Filter):
        """Filter to mask sensitive data."""

        def filter(self, record):
            msg = record.msg
            if isinstance(msg, dict):
                for key in ["password", "token", "secret", "access_token", "refresh_token"]:
                    if key in msg:
                        msg[key] = "***MASKED***"
            return True

    sensitive_filter = SensitiveDataFilter()

    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(stream_handler)
    
    app.logger.addFilter(sensitive_filter)
    file_handler.addFilter(sensitive_filter)
    stream_handler.addFilter(sensitive_filter)

    app.logger.setLevel(logging.INFO)

    # Log startup
    app.logger.info("Flask application started")
