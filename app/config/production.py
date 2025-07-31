"""
Production environment configuration.
"""

import os
from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///prod_app.db'
    
    # Security settings - should be set via environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-secret-key-must-be-changed'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    
    # Logging configuration
    LOG_LEVEL = 'WARNING'
    
    # CORS configuration - restrictive
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # SSL settings
    SSL_REDIRECT = True
    
    # Error handling configuration - restrictive for production
    ERROR_INCLUDE_MESSAGE = True
    ERROR_INCLUDE_DETAILS = False
    ERROR_INCLUDE_TRACEBACK = False
    SLOW_REQUEST_THRESHOLD = 0.5  # seconds - stricter in production
    ERROR_MONITORING_ENABLED = True
    
    @staticmethod
    def init_app(app):
        """Initialize application for production environment."""
        BaseConfig.init_app(app)
        
        # Validate production configuration
        ProductionConfig._validate_production_config(app)
        
        # Production specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configure file logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/flask_api.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.WARNING)
        app.logger.info('Flask API Template startup')
    
    @staticmethod
    def _validate_production_config(app):
        """Validate production configuration and warn about insecure defaults."""
        import warnings
        
        if app.config['SECRET_KEY'] == 'prod-secret-key-must-be-changed':
            warnings.warn(
                "Using default SECRET_KEY in production! Set SECRET_KEY environment variable.",
                UserWarning
            )
        
        if not os.environ.get('JWT_SECRET_KEY'):
            warnings.warn(
                "Using default JWT_SECRET_KEY in production! Set JWT_SECRET_KEY environment variable.",
                UserWarning
            )
        
        if app.config['CORS_ORIGINS'] == ['https://yourdomain.com']:
            warnings.warn(
                "Using default CORS_ORIGINS in production! Set CORS_ORIGINS environment variable.",
                UserWarning
            )