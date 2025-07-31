"""
Flask API Template Application Factory

This module implements the application factory pattern for creating Flask app instances
with different configurations for different environments.
"""

import logging
from flask import Flask
from app.config import config
from app.extensions import init_extensions
from app.middleware import auth_middleware, logging_middleware, performance_middleware
from app.utils.logging_config import configure_logging
from app.utils.error_handlers import register_error_handlers, setup_error_monitoring

logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory function that creates and configures Flask app instance.
    
    Args:
        config_name (str): Configuration name (development, testing, acceptance, production)
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize middleware
    init_middleware(app)
    
    # Register error handlers and setup monitoring
    register_error_handlers(app)
    setup_error_monitoring(app)
    
    # Register blueprints (will be added in later tasks)
    register_blueprints(app)
    
    logger.info(f"Flask app created with config: {config_name}")
    
    return app


def init_middleware(app):
    """
    Initialize application middleware.
    
    Args:
        app (Flask): Flask application instance
    """
    # Initialize logging middleware first (to capture all requests)
    logging_middleware.init_app(app)
    
    # Initialize performance middleware
    performance_middleware.init_app(app)
    
    # Initialize authentication middleware
    auth_middleware.init_app(app)
    
    logger.info("All middleware initialized")


def register_blueprints(app):
    """
    Register application blueprints and API namespaces.
    
    Args:
        app (Flask): Flask application instance
    """
    from app.controllers.auth_controller import auth_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.health_controller import health_bp
    from app.extensions import api
    from app.api.auth_namespace import auth_ns
    from app.api.user_namespace import user_ns
    from app.api.health_namespace import health_ns
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    logger.info("Authentication blueprint registered")
    
    # Register user management blueprint
    app.register_blueprint(user_bp)
    logger.info("User management blueprint registered")
    
    # Register health check blueprint
    app.register_blueprint(health_bp)
    logger.info("Health check blueprint registered")
    
    # Register API namespaces for documentation
    api.add_namespace(auth_ns)
    logger.info("Authentication API namespace registered")
    
    api.add_namespace(user_ns)
    logger.info("User management API namespace registered")
    
    api.add_namespace(health_ns)
    logger.info("Health check API namespace registered")
    
    logger.info("All blueprints and API namespaces registered successfully")