"""
Custom exception classes for the Flask API application.

This module defines a hierarchy of custom exceptions that provide structured
error handling with proper status codes, error messages, and logging capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class APIException(Exception):
    """
    Base exception class for all API-related errors.

    This class provides a foundation for all custom exceptions in the application,
    ensuring consistent error handling and logging.
    """

    status_code: int = 500
    error_code: str = "API_ERROR"
    message: str = "An error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "error",
    ):
        """
        Initialize the API exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
            log_level: Logging level for this exception
        """
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.log_level = log_level

        # Log the exception
        self._log_exception()

        super().__init__(self.message)

    def _log_exception(self):
        """Log the exception with appropriate level."""
        log_message = f"{self.error_code}: {self.message}"
        if self.details:
            log_message += f" - Details: {self.details}"

        log_method = getattr(logger, self.log_level, logger.error)
        log_method(log_message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the exception
        """
        result = {
            "error": self.message,
            "code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.details:
            result["details"] = self.details

        return result


class ValidationError(APIException):
    """Exception raised for data validation errors."""

    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"

    def __init__(
        self,
        message: Optional[str] = None,
        field_errors: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            field_errors: Field-specific validation errors
            **kwargs: Additional arguments passed to parent
        """
        if field_errors:
            kwargs["details"] = {"field_errors": field_errors}
        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class AuthenticationError(APIException):
    """Exception raised for authentication failures."""

    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"

    def __init__(self, message: Optional[str] = None, **kwargs):
        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class AuthorizationError(APIException):
    """Exception raised for authorization failures."""

    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    message = "Access denied"

    def __init__(self, message: Optional[str] = None, **kwargs):
        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class NotFoundError(APIException):
    """Exception raised when a resource is not found."""

    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"

    def __init__(
        self,
        message: Optional[str] = None,
        resource_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize not found error.

        Args:
            message: Error message
            resource_type: Type of resource that was not found
            **kwargs: Additional arguments passed to parent
        """
        if resource_type and not message:
            message = f"{resource_type} not found"

        if resource_type:
            if "details" not in kwargs:
                kwargs["details"] = {}
            kwargs["details"]["resource_type"] = resource_type

        kwargs["log_level"] = "info"
        super().__init__(message, **kwargs)


class ConflictError(APIException):
    """Exception raised for resource conflicts."""

    status_code = 409
    error_code = "CONFLICT_ERROR"
    message = "Resource conflict"

    def __init__(self, message: Optional[str] = None, **kwargs):
        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class BusinessLogicError(APIException):
    """Exception raised for business logic violations."""

    status_code = 400
    error_code = "BUSINESS_LOGIC_ERROR"
    message = "Business logic violation"

    def __init__(self, message: Optional[str] = None, **kwargs):
        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class ExternalServiceError(APIException):
    """Exception raised for external service failures."""

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "External service unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize external service error.

        Args:
            message: Error message
            service_name: Name of the external service
            **kwargs: Additional arguments passed to parent
        """
        if service_name and not message:
            message = f"{service_name} service unavailable"

        if service_name:
            kwargs["details"] = {"service_name": service_name}

        super().__init__(message, **kwargs)


class RateLimitError(APIException):
    """Exception raised when rate limits are exceeded."""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded"

    def __init__(
        self, message: Optional[str] = None, retry_after: Optional[int] = None, **kwargs
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments passed to parent
        """
        if retry_after:
            kwargs["details"] = {"retry_after": retry_after}

        kwargs["log_level"] = "warning"
        super().__init__(message, **kwargs)


class DatabaseError(APIException):
    """Exception raised for database operation failures."""

    status_code = 500
    error_code = "DATABASE_ERROR"
    message = "Database operation failed"

    def __init__(
        self, message: Optional[str] = None, operation: Optional[str] = None, **kwargs
    ):
        """
        Initialize database error.

        Args:
            message: Error message
            operation: Database operation that failed
            **kwargs: Additional arguments passed to parent
        """
        if operation:
            kwargs["details"] = {"operation": operation}

        super().__init__(message, **kwargs)


class ConfigurationError(APIException):
    """Exception raised for configuration-related errors."""

    status_code = 500
    error_code = "CONFIGURATION_ERROR"
    message = "Configuration error"

    def __init__(
        self, message: Optional[str] = None, config_key: Optional[str] = None, **kwargs
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional arguments passed to parent
        """
        if config_key:
            kwargs["details"] = {"config_key": config_key}

        super().__init__(message, **kwargs)


# Specific business domain exceptions


class UserNotFoundError(NotFoundError):
    """Exception raised when a user is not found."""

    error_code = "USER_NOT_FOUND"
    message = "User not found"

    def __init__(self, user_id: Optional[str] = None, **kwargs):
        if user_id:
            if "details" not in kwargs:
                kwargs["details"] = {}
            kwargs["details"]["user_id"] = user_id
        super().__init__(resource_type="User", **kwargs)


class InvalidCredentialsError(AuthenticationError):
    """Exception raised for invalid login credentials."""

    error_code = "INVALID_CREDENTIALS"
    message = "Invalid username or password"


class TokenExpiredError(AuthenticationError):
    """Exception raised when a token has expired."""

    error_code = "TOKEN_EXPIRED"
    message = "Token has expired"


class TokenInvalidError(AuthenticationError):
    """Exception raised when a token is invalid."""

    error_code = "TOKEN_INVALID"
    message = "Invalid token"


class InsufficientPermissionsError(AuthorizationError):
    """Exception raised when user lacks required permissions."""

    error_code = "INSUFFICIENT_PERMISSIONS"
    message = "Insufficient permissions for this operation"

    def __init__(self, required_permission: Optional[str] = None, **kwargs):
        if required_permission:
            kwargs["details"] = {"required_permission": required_permission}
        super().__init__(**kwargs)


class DuplicateResourceError(ConflictError):
    """Exception raised when trying to create a duplicate resource."""

    error_code = "DUPLICATE_RESOURCE"
    message = "Resource already exists"

    def __init__(
        self, resource_type: Optional[str] = None, field: Optional[str] = None, **kwargs
    ):
        if resource_type and field:
            message = f"{resource_type} with this {field} already exists"
            kwargs["details"] = {"resource_type": resource_type, "field": field}
        elif resource_type:
            message = f"{resource_type} already exists"
            kwargs["details"] = {"resource_type": resource_type}
        else:
            message = self.message

        super().__init__(message, **kwargs)


class InvalidOperationError(BusinessLogicError):
    """Exception raised for invalid business operations."""

    error_code = "INVALID_OPERATION"
    message = "Invalid operation"

    def __init__(
        self, operation: Optional[str] = None, reason: Optional[str] = None, **kwargs
    ):
        if operation and reason:
            message = f"Cannot {operation}: {reason}"
            kwargs["details"] = {"operation": operation, "reason": reason}
        elif operation:
            message = f"Invalid operation: {operation}"
            kwargs["details"] = {"operation": operation}
        else:
            message = self.message

        super().__init__(message, **kwargs)
