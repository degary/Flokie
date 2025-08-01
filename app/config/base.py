"""
Base configuration class with common settings.
"""

import os
from datetime import timedelta


class BaseConfig:
    """Base configuration class with common settings for all environments."""

    # Basic Flask configuration
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # CORS configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

    # Logging configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
    LOG_JSON_FORMAT = os.environ.get("LOG_JSON_FORMAT", "false").lower() == "true"
    LOG_FILE = os.environ.get("LOG_FILE", None)
    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", 5))

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # API configuration
    API_TITLE = "Flask API Template"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"

    # Error handling configuration
    ERROR_INCLUDE_MESSAGE = True
    ERROR_INCLUDE_DETAILS = True
    ERROR_INCLUDE_TRACEBACK = False
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    ERROR_MONITORING_ENABLED = True

    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass
