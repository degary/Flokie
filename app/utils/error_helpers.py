"""
Error handling helper functions for services and controllers.

This module provides utility functions to help raise appropriate exceptions
and handle common error scenarios in a consistent way.
"""

from typing import Any, Dict, Optional

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConflictError,
    DuplicateResourceError,
    InvalidCredentialsError,
    InvalidOperationError,
    NotFoundError,
    UserNotFoundError,
    ValidationError,
)


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present in the data.

    Args:
        data: Dictionary containing the data to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            field_errors={field: "This field is required" for field in missing_fields},
        )


def validate_field_length(
    data: Dict[str, Any], field_constraints: Dict[str, Dict[str, int]]
) -> None:
    """
    Validate field lengths against constraints.

    Args:
        data: Dictionary containing the data to validate
        field_constraints: Dictionary mapping field names to constraint dictionaries
                          e.g., {'username': {'min': 3, 'max': 50}}

    Raises:
        ValidationError: If any field length constraints are violated
    """
    field_errors = {}

    for field, constraints in field_constraints.items():
        if field in data and data[field] is not None:
            value = str(data[field])
            min_length = constraints.get("min", 0)
            max_length = constraints.get("max", float("inf"))

            if len(value) < min_length:
                field_errors[field] = f"Must be at least {min_length} characters long"
            elif len(value) > max_length:
                field_errors[
                    field
                ] = f"Must be no more than {max_length} characters long"

    if field_errors:
        raise ValidationError(
            message="Field length validation failed", field_errors=field_errors
        )


def check_resource_exists(
    resource, resource_type: str, identifier: Optional[str] = None
) -> None:
    """
    Check if a resource exists and raise NotFoundError if it doesn't.

    Args:
        resource: The resource object (None if not found)
        resource_type: Type of resource (e.g., 'User', 'Post')
        identifier: Optional identifier for the resource

    Raises:
        NotFoundError: If the resource is None
    """
    if resource is None:
        if identifier:
            raise NotFoundError(
                message=f"{resource_type} with identifier '{identifier}' not found",
                resource_type=resource_type,
                details={"identifier": identifier},
            )
        else:
            raise NotFoundError(
                message=f"{resource_type} not found", resource_type=resource_type
            )


def check_user_exists(user, user_id: Optional[str] = None) -> None:
    """
    Check if a user exists and raise UserNotFoundError if not.

    Args:
        user: The user object (None if not found)
        user_id: Optional user identifier

    Raises:
        UserNotFoundError: If the user is None
    """
    if user is None:
        raise UserNotFoundError(user_id=user_id)


def check_permissions(user, required_permission: str, resource=None) -> None:
    """
    Check if a user has the required permission.

    Args:
        user: User object
        required_permission: Permission string required
        resource: Optional resource the permission applies to

    Raises:
        AuthorizationError: If the user lacks the required permission
    """
    # This is a simplified permission check - implement according to your permission system
    if not user:
        raise AuthenticationError("User not authenticated")

    # Example permission check logic
    if hasattr(user, "has_permission") and not user.has_permission(required_permission):
        raise AuthorizationError(
            message=f"Permission '{required_permission}' required",
            details={"required_permission": required_permission},
        )


def check_resource_ownership(user, resource, resource_type: str) -> None:
    """
    Check if a user owns a resource.

    Args:
        user: User object
        resource: Resource object
        resource_type: Type of resource

    Raises:
        AuthorizationError: If the user doesn't own the resource
    """
    if not user:
        raise AuthenticationError("User not authenticated")

    if not resource:
        raise NotFoundError(f"{resource_type} not found")

    # Check ownership - adapt this to your model structure
    if hasattr(resource, "user_id") and resource.user_id != user.id:
        raise AuthorizationError(
            message=f"You don't have permission to access this {resource_type.lower()}",
            details={
                "resource_type": resource_type,
                "resource_id": getattr(resource, "id", None),
            },
        )


def handle_duplicate_resource(
    field: str, value: str, resource_type: str = "Resource"
) -> None:
    """
    Raise a DuplicateResourceError for duplicate field values.

    Args:
        field: Field name that has duplicate value
        value: The duplicate value
        resource_type: Type of resource

    Raises:
        DuplicateResourceError: Always raises this exception
    """
    raise DuplicateResourceError(
        resource_type=resource_type,
        field=field,
        details={"field": field, "value": value},
    )


def validate_business_rule(
    condition: bool, message: str, details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate a business rule and raise BusinessLogicError if violated.

    Args:
        condition: Boolean condition that should be True
        message: Error message if condition is False
        details: Optional additional details

    Raises:
        BusinessLogicError: If condition is False
    """
    if not condition:
        raise BusinessLogicError(message=message, details=details)


def validate_operation_allowed(
    operation: str, reason: str, details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate that an operation is allowed.

    Args:
        operation: Name of the operation
        reason: Reason why the operation is not allowed
        details: Optional additional details

    Raises:
        InvalidOperationError: Always raises this exception
    """
    raise InvalidOperationError(operation=operation, reason=reason, details=details)


def safe_get_or_404(model_class, **kwargs):
    """
    Safely get a model instance or raise NotFoundError.

    Args:
        model_class: SQLAlchemy model class
        **kwargs: Query parameters

    Returns:
        Model instance

    Raises:
        NotFoundError: If no instance is found
    """
    try:
        instance = model_class.query.filter_by(**kwargs).first()
        if instance is None:
            resource_type = model_class.__name__
            identifier = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            raise NotFoundError(
                message=f"{resource_type} not found",
                resource_type=resource_type,
                details={"query_params": kwargs, "identifier": identifier},
            )
        return instance
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        # Convert database errors to our custom exceptions
        from .exceptions import DatabaseError

        raise DatabaseError(
            message="Error querying database",
            details={"model": model_class.__name__, "query_params": kwargs},
        )


def handle_authentication_error(message: str = "Authentication failed") -> None:
    """
    Raise an authentication error.

    Args:
        message: Error message

    Raises:
        AuthenticationError: Always raises this exception
    """
    raise AuthenticationError(message=message)


def handle_invalid_credentials() -> None:
    """
    Raise an invalid credentials error.

    Raises:
        InvalidCredentialsError: Always raises this exception
    """
    raise InvalidCredentialsError()
