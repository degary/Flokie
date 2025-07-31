"""
Middleware package for Flask API Template.

This package contains middleware components for request/response processing.
"""

from .auth_middleware import (
    AuthenticationMiddleware,
    auth_middleware,
    require_auth,
    require_roles,
    get_current_user,
    get_current_user_id,
    is_authenticated
)

from .logging_middleware import (
    LoggingMiddleware,
    PerformanceMiddleware,
    logging_middleware,
    performance_middleware
)

__all__ = [
    'AuthenticationMiddleware',
    'auth_middleware',
    'require_auth',
    'require_roles',
    'get_current_user',
    'get_current_user_id',
    'is_authenticated',
    'LoggingMiddleware',
    'PerformanceMiddleware',
    'logging_middleware',
    'performance_middleware'
]