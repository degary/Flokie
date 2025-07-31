"""
Acceptance environment configuration.
"""

import os
from .base import BaseConfig


class AcceptanceConfig(BaseConfig):
    """Acceptance environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('ACC_DATABASE_URL') or \
        'sqlite:///acc_app.db'
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'acc-secret-key-change-in-production'
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    
    # CORS configuration - more restrictive
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application for acceptance environment."""
        BaseConfig.init_app(app)
        
        # Acceptance specific initialization
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )