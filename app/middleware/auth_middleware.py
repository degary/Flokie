"""
Authentication middleware for JWT token validation and user context setup.

This middleware handles JWT token validation, user context setup, and authentication
error handling for protected routes.
"""

import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import (
    verify_jwt_in_request, 
    get_jwt_identity, 
    get_jwt,
    jwt_required
)
from werkzeug.exceptions import Unauthorized

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """
    Authentication middleware class for handling JWT token validation.
    """
    
    def __init__(self, app=None):
        """
        Initialize authentication middleware.
        
        Args:
            app (Flask, optional): Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize middleware with Flask application.
        
        Args:
            app (Flask): Flask application instance
        """
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        logger.info("Authentication middleware initialized")
    
    def before_request(self):
        """
        Process request before route handler execution.
        Validates JWT tokens and sets up user context.
        """
        # Skip authentication for certain endpoints
        if self._should_skip_auth():
            return
        
        try:
            # Verify JWT token in request
            verify_jwt_in_request(optional=True)
            
            # Get user identity from token
            user_identity = get_jwt_identity()
            
            if user_identity:
                # Set up user context
                self._setup_user_context(user_identity)
                logger.debug(f"User context set for user: {user_identity}")
            
        except Exception as e:
            logger.warning(f"Authentication error: {str(e)}")
            # Let JWT extension handle the error response
            pass
    
    def after_request(self, response):
        """
        Process response after route handler execution.
        
        Args:
            response: Flask response object
            
        Returns:
            Flask response object
        """
        # Clear user context after request
        if hasattr(g, 'current_user'):
            delattr(g, 'current_user')
        if hasattr(g, 'current_user_id'):
            delattr(g, 'current_user_id')
        
        return response
    
    def _should_skip_auth(self):
        """
        Determine if authentication should be skipped for current request.
        
        Returns:
            bool: True if authentication should be skipped
        """
        # Skip authentication for certain endpoints
        skip_endpoints = [
            '/health',
            '/docs',
            '/swagger',
            '/openapi.json',
            '/auth/login',
            '/auth/register',
            '/auth/refresh'
        ]
        
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return True
        
        # Skip for specific endpoints
        for endpoint in skip_endpoints:
            if request.path.startswith(endpoint):
                return True
        
        return False
    
    def _setup_user_context(self, user_identity):
        """
        Set up user context in Flask's g object.
        
        Args:
            user_identity: User identity from JWT token
        """
        # Store user identity in Flask's g object
        g.current_user_id = user_identity
        
        # Get additional JWT claims
        jwt_claims = get_jwt()
        g.jwt_claims = jwt_claims
        
        # This will be enhanced when User model is available
        # For now, we just store the user ID
        g.current_user = None  # Will be populated with actual user object later


def require_auth(optional=False):
    """
    Decorator to require authentication for specific routes.
    
    Args:
        optional (bool): If True, authentication is optional
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=optional)
                
                if not optional:
                    user_identity = get_jwt_identity()
                    if not user_identity:
                        logger.warning("Missing user identity in JWT token")
                        return jsonify({
                            'error': 'authentication_required',
                            'message': 'Valid authentication token required',
                            'code': 'AUTH_REQUIRED'
                        }), 401
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Authentication decorator error: {str(e)}")
                return jsonify({
                    'error': 'authentication_failed',
                    'message': 'Authentication failed',
                    'code': 'AUTH_FAILED'
                }), 401
        
        return decorated_function
    return decorator


def require_roles(*required_roles):
    """
    Decorator to require specific roles for route access.
    
    Args:
        *required_roles: Required roles for access
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        @require_auth()
        def decorated_function(*args, **kwargs):
            try:
                jwt_claims = get_jwt()
                user_roles = jwt_claims.get('roles', [])
                
                # Check if user has any of the required roles
                if not any(role in user_roles for role in required_roles):
                    logger.warning(f"Access denied. Required roles: {required_roles}, User roles: {user_roles}")
                    return jsonify({
                        'error': 'insufficient_permissions',
                        'message': 'Insufficient permissions to access this resource',
                        'code': 'INSUFFICIENT_PERMISSIONS'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Role authorization error: {str(e)}")
                return jsonify({
                    'error': 'authorization_failed',
                    'message': 'Authorization failed',
                    'code': 'AUTH_FAILED'
                }), 403
        
        return decorated_function
    return decorator


def get_current_user():
    """
    Get current authenticated user from request context.
    
    Returns:
        User object or None if not authenticated
    """
    return getattr(g, 'current_user', None)


def get_current_user_id():
    """
    Get current authenticated user ID from request context.
    
    Returns:
        User ID or None if not authenticated
    """
    return getattr(g, 'current_user_id', None)


def is_authenticated():
    """
    Check if current request is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return get_current_user_id() is not None


# Create middleware instance
auth_middleware = AuthenticationMiddleware()