"""
Testing environment configuration.
"""

import os
from .base import BaseConfig


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    DEBUG = False
    TESTING = True
    
    # Database configuration - use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'
    
    # Disable CSRF protection in testing
    WTF_CSRF_ENABLED = False
    
    # JWT configuration for testing
    JWT_ACCESS_TOKEN_EXPIRES = False  # Tokens don't expire in tests
    
    # Logging configuration
    LOG_LEVEL = 'WARNING'
    
    @staticmethod
    def init_app(app):
        """Initialize application for testing environment."""
        BaseConfig.init_app(app)
        
        # Testing specific initialization
        import logging
        logging.disable(logging.CRITICAL)