"""
Custom error handlers for the Flask application.

This module provides centralized error handling for various types of errors
including validation errors, authentication errors, and HTTP errors.
"""

import logging
from flask import jsonify, request, current_app
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime

from .exceptions import (
    APIException, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ConflictError, BusinessLogicError, ExternalServiceError,
    RateLimitError, DatabaseError, ConfigurationError, DuplicateResourceError
)

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Register custom error handlers with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """Handle custom API exceptions."""
        response_data, status_code = create_error_response(error)
        log_error_metrics(error, status_code)
        return jsonify(response_data), status_code
    
    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(error):
        """Handle Marshmallow validation errors."""
        logger.warning(f"Marshmallow validation error on {request.method} {request.path}: {error.messages}")
        
        return jsonify({
            'error': 'Validation failed',
            'code': 'VALIDATION_ERROR',
            'details': {'field_errors': error.messages},
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 400
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Handle database integrity constraint errors."""
        logger.error(f"Database integrity error on {request.method} {request.path}: {error}")
        
        # Try to provide more specific error messages based on the constraint
        error_message = "Database constraint violation"
        error_code = "INTEGRITY_ERROR"
        details = {}
        
        if 'UNIQUE constraint failed' in str(error) or 'duplicate key' in str(error).lower():
            if 'username' in str(error).lower():
                raise DuplicateResourceError("User", "username")
            elif 'email' in str(error).lower():
                raise DuplicateResourceError("User", "email")
            else:
                error_message = "A record with this information already exists"
                error_code = "DUPLICATE_RECORD"
        elif 'FOREIGN KEY constraint failed' in str(error):
            error_message = "Referenced record does not exist"
            error_code = "FOREIGN_KEY_ERROR"
        elif 'NOT NULL constraint failed' in str(error):
            error_message = "Required field is missing"
            error_code = "REQUIRED_FIELD_MISSING"
            # Extract field name if possible
            if 'NOT NULL constraint failed:' in str(error):
                field_info = str(error).split('NOT NULL constraint failed:')[1].strip()
                details['field'] = field_info
        
        return jsonify({
            'error': error_message,
            'code': error_code,
            'details': details if details else None,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 409
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Handle general SQLAlchemy database errors."""
        # Convert to our custom DatabaseError
        raise DatabaseError(
            message="Database operation failed",
            details={'original_error': str(error)}
        )
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        logger.warning(f"Bad request on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': 'Bad request',
            'code': 'BAD_REQUEST',
            'message': error.description if hasattr(error, 'description') else 'Invalid request',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors."""
        logger.warning(f"Unauthorized access attempt on {request.method} {request.path}")
        
        return jsonify({
            'error': 'Unauthorized',
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors."""
        logger.warning(f"Forbidden access attempt on {request.method} {request.path}")
        
        return jsonify({
            'error': 'Forbidden',
            'code': 'FORBIDDEN',
            'message': 'Insufficient permissions',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        logger.info(f"Resource not found: {request.method} {request.path}")
        
        return jsonify({
            'error': 'Not found',
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        logger.warning(f"Method not allowed: {request.method} {request.path}")
        
        return jsonify({
            'error': 'Method not allowed',
            'code': 'METHOD_NOT_ALLOWED',
            'message': f'Method {request.method} is not allowed for this endpoint',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 405
    
    @app.errorhandler(409)
    def handle_conflict(error):
        """Handle 409 Conflict errors."""
        logger.warning(f"Conflict on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': 'Conflict',
            'code': 'CONFLICT',
            'message': error.description if hasattr(error, 'description') else 'Resource conflict',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 409
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        logger.warning(f"Unprocessable entity on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': 'Unprocessable entity',
            'code': 'UNPROCESSABLE_ENTITY',
            'message': error.description if hasattr(error, 'description') else 'Request data is invalid',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 422
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        logger.warning(f"Rate limit exceeded on {request.method} {request.path}")
        
        return jsonify({
            'error': 'Rate limit exceeded',
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Please try again later.',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 500
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        logger.error(f"Service unavailable on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': 'Service unavailable',
            'code': 'SERVICE_UNAVAILABLE',
            'message': 'The service is temporarily unavailable',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle generic HTTP exceptions."""
        logger.warning(f"HTTP exception on {request.method} {request.path}: {error}")
        
        return jsonify({
            'error': error.name,
            'code': error.name.upper().replace(' ', '_'),
            'message': error.description,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'method': request.method
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle any unhandled exceptions."""
        logger.error(f"Unhandled exception on {request.method} {request.path}: {error}", exc_info=True)
        
        # Create standardized error response
        response_data, status_code = create_error_response(error, include_traceback=True)
        log_error_metrics(error, status_code)
        
        return jsonify(response_data), status_code
    
    logger.info("Custom error handlers registered")




def setup_error_monitoring(app):
    """
    Set up error monitoring and tracking capabilities.
    
    Args:
        app: Flask application instance
    """
    
    if not app.config.get('ERROR_MONITORING_ENABLED', True):
        logger.info("Error monitoring disabled by configuration")
        return
    
    # Error statistics tracking
    error_stats = {
        'total_requests': 0,
        'error_requests': 0,
        'slow_requests': 0,
        'error_types': {}
    }
    
    @app.before_request
    def track_request():
        """Track request information for error context."""
        request.start_time = datetime.utcnow()
        request.request_id = _generate_request_id()
        error_stats['total_requests'] += 1
    
    @app.after_request
    def track_response(response):
        """Track response information and log errors."""
        if hasattr(request, 'start_time'):
            duration = (datetime.utcnow() - request.start_time).total_seconds()
            
            # Log slow requests
            slow_threshold = app.config.get('SLOW_REQUEST_THRESHOLD', 1.0)
            if duration > slow_threshold:
                error_stats['slow_requests'] += 1
                logger.warning(
                    f"Slow request [{request.request_id}]: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )
            
            # Track error responses
            if response.status_code >= 400:
                error_stats['error_requests'] += 1
                error_type = f"{response.status_code // 100}xx"
                error_stats['error_types'][error_type] = error_stats['error_types'].get(error_type, 0) + 1
                
                log_level = 'error' if response.status_code >= 500 else 'warning'
                log_method = getattr(logger, log_level)
                log_method(
                    f"Error response [{request.request_id}]: {request.method} {request.path} "
                    f"- Status: {response.status_code} - Duration: {duration:.2f}s"
                )
        
        return response
    
    # Add error statistics endpoint for monitoring
    @app.route('/internal/error-stats')
    def error_statistics():
        """Internal endpoint for error statistics (for monitoring systems)."""
        if not app.config.get('DEBUG', False):
            # Only available in debug mode or with proper authentication
            from flask import abort
            abort(404)
        
        return {
            'error_stats': error_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    logger.info("Error monitoring setup completed")


def get_error_context():
    """
    Get contextual information for error reporting.
    
    Returns:
        Dictionary containing error context information
    """
    context = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method if request else None,
        'path': request.path if request else None,
        'remote_addr': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
    }
    
    # Add user context if available
    if hasattr(request, 'current_user') and request.current_user:
        context['user_id'] = getattr(request.current_user, 'id', None)
        context['username'] = getattr(request.current_user, 'username', None)
    
    # Add request ID if available
    if hasattr(request, 'request_id'):
        context['request_id'] = request.request_id
    
    return context


def _generate_request_id():
    """Generate a unique request ID for tracking."""
    import uuid
    return str(uuid.uuid4())[:8]


def create_error_response(error, include_traceback=None):
    """
    Create a standardized error response based on configuration.
    
    Args:
        error: Exception instance
        include_traceback: Whether to include traceback in response (overrides config)
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    if isinstance(error, APIException):
        response_data = error.to_dict()
        status_code = error.status_code
    else:
        # Handle non-API exceptions
        is_production = current_app.config.get('ENV') == 'production'
        include_message = current_app.config.get('ERROR_INCLUDE_MESSAGE', True)
        
        message = 'An unexpected error occurred'
        if include_message and not is_production:
            message = str(error)
        
        response_data = {
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        status_code = 500
    
    # Add context information
    context = get_error_context()
    response_data.update(context)
    
    # Add details based on configuration
    include_details = current_app.config.get('ERROR_INCLUDE_DETAILS', True)
    if not include_details and 'details' in response_data:
        del response_data['details']
    
    # Add traceback based on configuration
    if include_traceback is None:
        include_traceback = current_app.config.get('ERROR_INCLUDE_TRACEBACK', False)
    
    if include_traceback and not current_app.config.get('ENV') == 'production':
        import traceback
        response_data['traceback'] = traceback.format_exc()
    
    return response_data, status_code


def log_error_metrics(error, status_code):
    """
    Log error metrics for monitoring and alerting.
    
    Args:
        error: Exception instance
        status_code: HTTP status code
    """
    error_type = type(error).__name__
    
    # Log structured error information
    error_info = {
        'error_type': error_type,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(request, 'request_id', None),
        'path': request.path if request else None,
        'method': request.method if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
        'remote_addr': request.remote_addr if request else None
    }
    
    # Add user context if available
    if hasattr(request, 'current_user') and request.current_user:
        error_info['user_id'] = getattr(request.current_user, 'id', None)
    
    # Log with appropriate level
    if status_code >= 500:
        logger.error(f"Server error: {error_info}")
    elif status_code >= 400:
        logger.warning(f"Client error: {error_info}")
    else:
        logger.info(f"Error handled: {error_info}")
    
    # TODO: Send to external monitoring service (e.g., Sentry, DataDog)
    # This would be implemented based on the monitoring solution used