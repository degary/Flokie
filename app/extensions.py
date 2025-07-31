"""
Flask extensions initialization module.

This module handles the initialization of Flask extensions used throughout the application.
Extensions are initialized here to avoid circular imports.
"""

import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restx import Api

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
api = Api()

# Logger for extensions
logger = logging.getLogger(__name__)


def init_extensions(app):
    """
    Initialize Flask extensions with the application instance.
    
    Args:
        app (Flask): Flask application instance
    """
    logger.info("Initializing Flask extensions...")
    
    # Initialize database
    db.init_app(app)
    logger.info("SQLAlchemy initialized")
    
    # Initialize database migrations
    migrate.init_app(app, db)
    logger.info("Flask-Migrate initialized")
    
    # Initialize JWT manager
    jwt.init_app(app)
    logger.info("Flask-JWT-Extended initialized")
    
    # Initialize CORS
    cors_origins = app.config.get('CORS_ORIGINS', ['*'])
    cors.init_app(
        app, 
        origins=cors_origins,
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
        supports_credentials=True
    )
    logger.info(f"Flask-CORS initialized with origins: {cors_origins}")
    
    # Initialize Flask-RESTX API documentation
    api.init_app(
        app,
        version='1.0',
        title='Flask API Template',
        description='A comprehensive Flask API template with authentication, user management, and documentation',
        doc='/docs/',
        prefix='/api/v1',
        authorizations={
            'Bearer': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
            }
        },
        security='Bearer'
    )
    logger.info("Flask-RESTX API documentation initialized")
    
    # Configure JWT callbacks
    configure_jwt_callbacks(app)
    
    # Configure database event listeners
    configure_database_events(app)
    
    logger.info("All Flask extensions initialized successfully")


def configure_jwt_callbacks(app):
    """
    Configure JWT callbacks for token handling.
    
    Args:
        app (Flask): Flask application instance
    """
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"[WARNING] Expired token access attempt from user: {jwt_payload.get('sub', 'unknown')}")
        return {
            'error': 'token_expired',
            'message': 'The token has expired',
            'code': 'TOKEN_EXPIRED'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning(f"[WARNING] Invalid token access attempt: {error}")
        return {
            'error': 'invalid_token',
            'message': 'The token is invalid',
            'code': 'INVALID_TOKEN'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.info(f"[INFO] Unauthorized access attempt: {error}")
        return {
            'error': 'authorization_required',
            'message': 'Request does not contain an access token',
            'code': 'MISSING_TOKEN'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        logger.warning(f"[WARNING] Revoked token access attempt from user: {jwt_payload.get('sub', 'unknown')}")
        return {
            'error': 'token_revoked',
            'message': 'The token has been revoked',
            'code': 'TOKEN_REVOKED'
        }, 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        logger.info(f"[INFO] Fresh token required for user: {jwt_payload.get('sub', 'unknown')}")
        return {
            'error': 'fresh_token_required',
            'message': 'The token is not fresh',
            'code': 'FRESH_TOKEN_REQUIRED'
        }, 401
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """
        Define how to get user identity from user object.
        
        Args:
            user: User object or user ID
            
        Returns:
            User identity (typically user ID)
        """
        if hasattr(user, 'id'):
            return user.id
        return user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """
        Define how to load user from JWT payload.
        
        Args:
            _jwt_header: JWT header
            jwt_data: JWT payload data
            
        Returns:
            User object or None
        """
        from app.models.user import User
        
        identity = jwt_data["sub"]
        logger.debug(f"Looking up user with identity: {identity}")
        
        try:
            # Identity should be the user ID
            user = User.get_by_id(int(identity))
            if user and user.is_active and not user.is_account_locked():
                return user
            else:
                logger.warning(f"User lookup failed for identity {identity}: user inactive or locked")
                return None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user identity in JWT: {identity}, error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error looking up user with identity {identity}: {e}")
            return None


def configure_database_events(app):
    """
    Configure SQLAlchemy database event listeners.
    
    Args:
        app (Flask): Flask application instance
    """
    from sqlalchemy import event
    
    # Use app context to access the engine
    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Enable foreign key constraints for SQLite."""
            if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
                logger.debug("SQLite foreign key constraints enabled")
        
        @event.listens_for(db.engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log SQL queries in debug mode."""
            if app.debug and app.config.get('LOG_LEVEL') == 'DEBUG':
                logger.debug(f"SQL Query: {statement}")
                if parameters:
                    logger.debug(f"Parameters: {parameters}")
    
    logger.info("Database event listeners configured")


def get_db():
    """
    Get database instance for dependency injection.
    
    Returns:
        SQLAlchemy: Database instance
    """
    return db


def get_jwt():
    """
    Get JWT manager instance for dependency injection.
    
    Returns:
        JWTManager: JWT manager instance
    """
    return jwt