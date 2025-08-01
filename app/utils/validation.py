"""
Validation utilities and helper functions.

This module provides utility functions for data validation,
error handling, and schema processing.
"""

import logging
import re
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type

import jsonschema
from flask import jsonify, request
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

# Email validation regex - more strict
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"
)

# Username validation regex
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")


def validate_json(schema_class: Type, location: str = "json") -> Callable:
    """
    Decorator for validating request data using Marshmallow schemas.

    Args:
        schema_class: Marshmallow schema class to use for validation
        location: Where to get data from ('json', 'args', 'form')

    Returns:
        Decorated function
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()

                # Get data based on location
                if location == "json":
                    data = request.get_json() or {}
                elif location == "args":
                    data = request.args.to_dict()
                elif location == "form":
                    data = request.form.to_dict()
                else:
                    raise ValueError(f"Invalid location: {location}")

                # Validate data
                validated_data = schema.load(data)

                # Add validated data to kwargs
                kwargs["validated_data"] = validated_data

                return f(*args, **kwargs)

            except ValidationError as e:
                logger.warning(f"Validation error in {f.__name__}: {e.messages}")
                return (
                    jsonify(
                        {
                            "error": "Validation failed",
                            "code": "VALIDATION_ERROR",
                            "details": e.messages,
                        }
                    ),
                    400,
                )
            except Exception as e:
                logger.error(f"Unexpected error in validation decorator: {e}")
                return (
                    jsonify(
                        {"error": "Internal validation error", "code": "INTERNAL_ERROR"}
                    ),
                    500,
                )

        return decorated_function

    return decorator


def validate_query_params(schema_class: Type) -> Callable:
    """
    Decorator for validating query parameters.

    Args:
        schema_class: Marshmallow schema class to use for validation

    Returns:
        Decorated function
    """
    return validate_json(schema_class, location="args")


def serialize_response(
    data: Any, schema_class: Type, many: bool = False
) -> Dict[str, Any]:
    """
    Serialize response data using Marshmallow schema.

    Args:
        data: Data to serialize
        schema_class: Marshmallow schema class to use for serialization
        many: Whether to serialize multiple objects

    Returns:
        Serialized data

    Raises:
        ValidationError: If serialization fails
    """
    try:
        schema = schema_class()
        return schema.dump(data, many=many)
    except Exception as e:
        logger.error(f"Serialization error: {e}")
        raise ValidationError(f"Failed to serialize response: {str(e)}")


def handle_validation_error(error: ValidationError) -> tuple:
    """
    Handle marshmallow validation errors consistently.

    Args:
        error: ValidationError instance

    Returns:
        Tuple of (response_dict, status_code)
    """
    logger.warning(f"Validation error: {error.messages}")
    return {
        "error": "Validation failed",
        "code": "VALIDATION_ERROR",
        "details": error.messages,
    }, 400


def validate_pagination_params(
    page: Optional[int] = None, per_page: Optional[int] = None
) -> Dict[str, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        page: Page number
        per_page: Items per page

    Returns:
        Dictionary with validated pagination parameters

    Raises:
        ValidationError: If parameters are invalid
    """
    # Set defaults
    page = page or 1
    per_page = per_page or 20

    # Validate page
    if page < 1:
        raise ValidationError("Page must be at least 1")

    # Validate per_page
    if per_page < 1:
        raise ValidationError("Per page must be at least 1")
    if per_page > 100:
        raise ValidationError("Per page cannot exceed 100")

    return {"page": page, "per_page": per_page}


def validate_sort_params(
    sort_by: Optional[str] = None, sort_order: Optional[str] = None
) -> Dict[str, str]:
    """
    Validate and normalize sorting parameters.

    Args:
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')

    Returns:
        Dictionary with validated sorting parameters

    Raises:
        ValidationError: If parameters are invalid
    """
    # Set defaults
    sort_by = sort_by or "created_at"
    sort_order = sort_order or "desc"

    # Validate sort_by
    valid_sort_fields = [
        "created_at",
        "updated_at",
        "username",
        "email",
        "first_name",
        "last_name",
    ]
    if sort_by not in valid_sort_fields:
        raise ValidationError(
            f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}"
        )

    # Validate sort_order
    if sort_order not in ["asc", "desc"]:
        raise ValidationError("Sort order must be 'asc' or 'desc'")

    return {"sort_by": sort_by, "sort_order": sort_order}


def sanitize_search_term(search_term: Optional[str]) -> Optional[str]:
    """
    Sanitize search term for safe database queries.

    Args:
        search_term: Raw search term

    Returns:
        Sanitized search term or None
    """
    if not search_term:
        return None

    # Strip whitespace
    search_term = search_term.strip()

    # Return None if empty after stripping
    if not search_term:
        return None

    # Validate length
    if len(search_term) < 2:
        raise ValidationError("Search term must be at least 2 characters")
    if len(search_term) > 100:
        raise ValidationError("Search term cannot exceed 100 characters")

    # Remove potentially dangerous characters for SQL injection prevention
    # This is a basic sanitization - the ORM should handle SQL injection prevention
    dangerous_chars = ["%", "_", ";", "--", "/*", "*/", "xp_", "sp_"]
    for char in dangerous_chars:
        search_term = search_term.replace(char, "")

    return search_term


def validate_id_parameter(id_value: Any, parameter_name: str = "id") -> int:
    """
    Validate ID parameter from URL.

    Args:
        id_value: ID value to validate
        parameter_name: Name of the parameter for error messages

    Returns:
        Validated integer ID

    Raises:
        ValidationError: If ID is invalid
    """
    try:
        id_int = int(id_value)
        if id_int < 1:
            raise ValidationError(f"{parameter_name} must be a positive integer")
        return id_int
    except (ValueError, TypeError):
        raise ValidationError(f"{parameter_name} must be a valid integer")


def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message

    Returns:
        Standardized success response dictionary
    """
    response = {"success": True}

    if message:
        response["message"] = message

    if data is not None:
        response["data"] = data

    return response


def create_error_response(
    error_message: str, error_code: str = "ERROR", details: Any = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        error_message: Error message
        error_code: Error code
        details: Additional error details

    Returns:
        Standardized error response dictionary
    """
    response = {"error": error_message, "code": error_code}

    if details is not None:
        response["details"] = details

    return response


def validate_boolean_param(value: Any, default: bool = False) -> bool:
    """
    Validate and convert boolean parameter.

    Args:
        value: Value to convert to boolean
        default: Default value if conversion fails

    Returns:
        Boolean value
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "on"]

    if isinstance(value, int):
        return bool(value)

    return default


class ValidationMixin:
    """
    Mixin class for adding validation capabilities to controllers.
    """

    def validate_request_data(
        self, schema_class: Type, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate request data using schema.

        Args:
            schema_class: Marshmallow schema class
            data: Data to validate (defaults to request JSON)

        Returns:
            Validated data

        Raises:
            ValidationError: If validation fails
        """
        if data is None:
            data = request.get_json() or {}

        schema = schema_class()
        return schema.load(data)

    def serialize_data(
        self, data: Any, schema_class: Type, many: bool = False
    ) -> Dict[str, Any]:
        """
        Serialize data using schema.

        Args:
            data: Data to serialize
            schema_class: Marshmallow schema class
            many: Whether to serialize multiple objects

        Returns:
            Serialized data
        """
        return serialize_response(data, schema_class, many=many)

    def create_response(
        self, data: Any = None, message: str = None, status_code: int = 200
    ) -> tuple:
        """
        Create a standardized response.

        Args:
            data: Response data
            message: Response message
            status_code: HTTP status code

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = create_success_response(data, message)
        return response, status_code

    def create_error_response(
        self,
        error_message: str,
        error_code: str = "ERROR",
        details: Any = None,
        status_code: int = 400,
    ) -> tuple:
        """
        Create a standardized error response.

        Args:
            error_message: Error message
            error_code: Error code
            details: Additional error details
            status_code: HTTP status code

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = create_error_response(error_message, error_code, details)
        return response, status_code


# Individual validation functions
def is_valid_email(email: str) -> bool:
    """
    Check if email format is valid.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()

    # Check for basic format
    if not EMAIL_REGEX.match(email):
        return False

    # Additional checks for edge cases
    local_part, domain = email.split("@", 1)

    # Check for consecutive dots in local part
    if ".." in local_part:
        return False

    # Check for consecutive dots in domain
    if ".." in domain:
        return False

    # Check for leading/trailing dots in local part
    if local_part.startswith(".") or local_part.endswith("."):
        return False

    return True


def is_valid_username(username: str) -> bool:
    """
    Check if username format is valid.

    Args:
        username: Username to validate

    Returns:
        True if username is valid, False otherwise
    """
    if not username or not isinstance(username, str):
        return False

    username = username.strip()

    # Check basic format
    if not USERNAME_REGEX.match(username):
        return False

    # Don't allow usernames that are only numbers
    if username.isdigit():
        return False

    return True


def validate_email(email: str, custom_message: str = None) -> None:
    """
    Validate email format and raise exception if invalid.

    Args:
        email: Email address to validate
        custom_message: Custom error message

    Raises:
        ValidationError: If email is invalid
    """
    if not is_valid_email(email):
        message = custom_message or "Invalid email format"
        raise ValidationError(
            message=message, details={"field_errors": {"email": message}}
        )


def validate_username(username: str, custom_message: str = None) -> None:
    """
    Validate username format and raise exception if invalid.

    Args:
        username: Username to validate
        custom_message: Custom error message

    Raises:
        ValidationError: If username is invalid
    """
    if not is_valid_username(username):
        message = (
            custom_message
            or "Username must be 3-50 characters long and contain only letters, numbers, underscores, and hyphens"
        )
        raise ValidationError(
            message=message, details={"field_errors": {"username": message}}
        )


def validate_password(password: str, custom_message: str = None) -> None:
    """
    Validate password format and raise exception if invalid.

    Args:
        password: Password to validate
        custom_message: Custom error message

    Raises:
        ValidationError: If password is invalid
    """
    if not password or not isinstance(password, str):
        message = custom_message or "Password is required"
        raise ValidationError(
            message=message, details={"field_errors": {"password": message}}
        )

    password = password.strip()
    if len(password) < 8:
        message = custom_message or "Password must be at least 8 characters long"
        raise ValidationError(
            message=message, details={"field_errors": {"password": message}}
        )

    if len(password) > 128:
        message = custom_message or "Password cannot exceed 128 characters"
        raise ValidationError(
            message=message, details={"field_errors": {"password": message}}
        )


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present and not empty.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required fields are missing or empty
    """
    field_errors = {}

    for field in required_fields:
        if field not in data:
            field_errors[field] = f"{field} is required"
        elif data[field] is None:
            field_errors[field] = f"{field} cannot be null"
        elif isinstance(data[field], str) and not data[field].strip():
            field_errors[field] = f"{field} cannot be empty"

    if field_errors:
        raise ValidationError(
            message="Required fields are missing or empty",
            details={"field_errors": field_errors},
        )


def validate_field_length(
    data: Dict[str, Any], constraints: Dict[str, Dict[str, int]]
) -> None:
    """
    Validate field lengths against constraints.

    Args:
        data: Data dictionary to validate
        constraints: Dictionary of field constraints with min/max lengths

    Raises:
        ValidationError: If any fields violate length constraints
    """
    field_errors = {}

    for field, constraint in constraints.items():
        if field not in data:
            continue  # Skip missing fields (handled by required validation)

        value = data[field]
        if not isinstance(value, str):
            continue

        min_length = constraint.get("min", 0)
        max_length = constraint.get("max", float("inf"))

        if len(value) < min_length:
            field_errors[
                field
            ] = f"{field} must be at least {min_length} characters long"
        elif len(value) > max_length:
            field_errors[
                field
            ] = f"{field} must be no more than {max_length} characters long"

    if field_errors:
        raise ValidationError(
            message="Field length validation failed",
            details={"field_errors": field_errors},
        )


def sanitize_input(input_value: Any) -> str:
    """
    Sanitize input by removing HTML tags and normalizing whitespace.

    Args:
        input_value: Input value to sanitize

    Returns:
        Sanitized string
    """
    if input_value is None:
        return ""

    if not isinstance(input_value, str):
        input_value = str(input_value)

    # Remove HTML tags
    import re

    html_tag_regex = re.compile(r"<[^>]+>")
    sanitized = html_tag_regex.sub("", input_value)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized.strip())

    return sanitized


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate data against JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema to validate against

    Raises:
        ValidationError: If data doesn't match schema
    """
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(
            message=f"Schema validation failed: {e.message}",
            details={"schema_error": str(e)},
        )
    except jsonschema.SchemaError as e:
        raise ValidationError(
            message=f"Invalid schema: {e.message}", details={"schema_error": str(e)}
        )
