"""
Common Marshmallow schemas for shared data structures.

This module contains schemas for common data structures used across
multiple endpoints, such as pagination, error responses, and base models.
"""

from datetime import datetime

from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, validate


class PaginationSchema(Schema):
    """Schema for pagination parameters."""

    page = fields.Int(
        validate=validate.Range(min=1, error="Page must be at least 1"),
        missing=1,
        description="Page number",
    )
    per_page = fields.Int(
        validate=validate.Range(
            min=1, max=100, error="Per page must be between 1 and 100"
        ),
        missing=20,
        description="Items per page",
    )

    @post_load
    def make_pagination(self, data, **kwargs):
        """Post-process pagination data."""
        return data


class SortingSchema(Schema):
    """Schema for sorting parameters."""

    sort_by = fields.Str(
        validate=validate.OneOf(
            [
                "created_at",
                "updated_at",
                "username",
                "email",
                "first_name",
                "last_name",
            ],
            error="Invalid sort field",
        ),
        missing="created_at",
        description="Field to sort by",
    )
    sort_order = fields.Str(
        validate=validate.OneOf(
            ["asc", "desc"], error="Sort order must be 'asc' or 'desc'"
        ),
        missing="desc",
        description="Sort order",
    )


class SearchSchema(Schema):
    """Schema for search parameters."""

    search = fields.Str(
        validate=validate.Length(
            min=2, max=100, error="Search term must be between 2 and 100 characters"
        ),
        allow_none=True,
        description="Search term",
    )
    include_inactive = fields.Bool(
        missing=False, description="Include inactive records"
    )


class ErrorResponseSchema(Schema):
    """Schema for error responses."""

    error = fields.Str(required=True, description="Error message")
    code = fields.Str(required=True, description="Error code")
    details = fields.Raw(allow_none=True, description="Additional error details")
    timestamp = fields.DateTime(missing=datetime.utcnow, description="Error timestamp")


class SuccessResponseSchema(Schema):
    """Schema for success responses."""

    success = fields.Bool(required=True, description="Success status")
    message = fields.Str(allow_none=True, description="Success message")
    data = fields.Raw(allow_none=True, description="Response data")
    timestamp = fields.DateTime(
        missing=datetime.utcnow, description="Response timestamp"
    )


class ValidationErrorSchema(Schema):
    """Schema for validation error responses."""

    error = fields.Str(required=True, description="Error message")
    code = fields.Str(required=True, description="Error code")
    details = fields.Dict(required=True, description="Validation error details")
    timestamp = fields.DateTime(missing=datetime.utcnow, description="Error timestamp")


class BaseModelSchema(Schema):
    """Base schema for database models."""

    id = fields.Int(dump_only=True, description="Record ID")
    created_at = fields.DateTime(dump_only=True, description="Creation timestamp")
    updated_at = fields.DateTime(dump_only=True, description="Last update timestamp")

    class Meta:
        """Schema metadata."""

        ordered = True
        unknown = EXCLUDE  # Exclude unknown fields


class TimestampMixin:
    """Mixin for timestamp fields."""

    created_at = fields.DateTime(dump_only=True, description="Creation timestamp")
    updated_at = fields.DateTime(dump_only=True, description="Last update timestamp")


# Custom validation functions
def validate_password_strength(password):
    """
    Validate password strength.

    Args:
        password (str): Password to validate

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one digit")

    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        raise ValidationError("Password must contain at least one special character")


def validate_username_format(username):
    """
    Validate username format.

    Args:
        username (str): Username to validate

    Raises:
        ValidationError: If username format is invalid
    """
    import re

    # Username must start with letter, contain only letters, numbers, underscores, hyphens
    pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
    if not re.match(pattern, username):
        raise ValidationError(
            "Username must start with a letter and contain only letters, numbers, underscores, and hyphens"
        )

    # Check for reserved usernames
    reserved_usernames = [
        "admin",
        "administrator",
        "root",
        "system",
        "api",
        "www",
        "mail",
        "email",
        "support",
        "help",
        "info",
        "contact",
        "service",
        "user",
        "guest",
        "anonymous",
        "null",
        "undefined",
        "test",
        "demo",
        "example",
    ]

    if username.lower() in reserved_usernames:
        raise ValidationError("This username is reserved and cannot be used")


def validate_email_domain(email):
    """
    Validate email domain (optional additional validation).

    Args:
        email (str): Email to validate

    Raises:
        ValidationError: If email domain is not allowed
    """
    # This is an example - you might want to implement domain whitelist/blacklist
    blocked_domains = ["tempmail.com", "10minutemail.com", "guerrillamail.com"]

    domain = email.split("@")[1].lower() if "@" in email else ""
    if domain in blocked_domains:
        raise ValidationError("Email domain is not allowed")


def validate_name_format(name):
    """
    Validate name format (first name, last name).

    Args:
        name (str): Name to validate

    Raises:
        ValidationError: If name format is invalid
    """
    import re

    # Names should contain only letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']+$"
    if not re.match(pattern, name):
        raise ValidationError(
            "Name can only contain letters, spaces, hyphens, and apostrophes"
        )

    # Check for excessive spaces or special characters
    if "  " in name or name.startswith(" ") or name.endswith(" "):
        raise ValidationError(
            "Name cannot have leading/trailing spaces or multiple consecutive spaces"
        )


# Custom fields
class PasswordField(fields.Str):
    """Custom field for password validation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators.append(validate_password_strength)


class UsernameField(fields.Str):
    """Custom field for username validation."""

    def __init__(self, **kwargs):
        super().__init__(
            validate=[
                validate.Length(
                    min=3, max=80, error="Username must be between 3 and 80 characters"
                ),
                validate_username_format,
            ],
            **kwargs,
        )


class EmailField(fields.Email):
    """Custom field for email validation."""

    def __init__(self, **kwargs):
        super().__init__(
            validate=[
                validate.Length(max=120, error="Email must be at most 120 characters"),
                validate_email_domain,
            ],
            **kwargs,
        )


class NameField(fields.Str):
    """Custom field for name validation."""

    def __init__(self, **kwargs):
        super().__init__(
            validate=[
                validate.Length(
                    min=1, max=50, error="Name must be between 1 and 50 characters"
                ),
                validate_name_format,
            ],
            **kwargs,
        )
