"""
Development environment configuration.
"""

import os

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DEV_DATABASE_URL") or "sqlite:///dev_app.db"
    )

    # Logging configuration
    LOG_LEVEL = "DEBUG"

    # Development specific settings
    FLASK_ENV = "development"

    @staticmethod
    def init_app(app):
        """Initialize application for development environment."""
        BaseConfig.init_app(app)

        # Development specific initialization
        import logging

        logging.basicConfig(level=logging.DEBUG)
