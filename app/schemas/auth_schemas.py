"""
Authentication-related Marshmallow schemas.

This module contains schemas for authentication operations including
login, registration, password management, and token operations.
"""

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)

from .common_schemas import (
    BaseModelSchema,
    EmailField,
    NameField,
    PasswordField,
    UsernameField,
)


class LoginRequestSchema(Schema):
    """Schema for login request validation."""

    username_or_email = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=120, error="Username or email is required"),
        description="Username or email address",
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Password is required"),
        description="User password",
    )
    remember_me = fields.Bool(
        missing=False, description="Whether to create longer-lived tokens"
    )

    @post_load
    def process_login_data(self, data, **kwargs):
        """Process login data after validation."""
        # Normalize username_or_email
        data["username_or_email"] = data["username_or_email"].strip().lower()
        return data


class RegisterRequestSchema(Schema):
    """Schema for registration request validation."""

    username = UsernameField(
        required=True, description="Desired username (3-80 characters)"
    )
    email = EmailField(required=True, description="Email address")
    password = PasswordField(
        required=True,
        description="Password (minimum 8 characters with complexity requirements)",
    )
    first_name = NameField(
        allow_none=True, description="First name (max 50 characters)"
    )
    last_name = NameField(allow_none=True, description="Last name (max 50 characters)")

    @validates_schema
    def validate_registration_data(self, data, **kwargs):
        """Validate registration data consistency."""
        # Additional cross-field validation can be added here
        pass

    @post_load
    def process_registration_data(self, data, **kwargs):
        """Process registration data after validation."""
        # Normalize email and username
        data["email"] = data["email"].strip().lower()
        data["username"] = data["username"].strip().lower()

        # Capitalize names if provided
        if data.get("first_name"):
            data["first_name"] = data["first_name"].strip().title()
        if data.get("last_name"):
            data["last_name"] = data["last_name"].strip().title()

        return data


class PasswordResetRequestSchema(Schema):
    """Schema for password reset request validation."""

    email = EmailField(required=True, description="Email address for password reset")

    @post_load
    def process_reset_request_data(self, data, **kwargs):
        """Process password reset request data."""
        data["email"] = data["email"].strip().lower()
        return data


class PasswordResetSchema(Schema):
    """Schema for password reset validation."""

    token = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Reset token is required"),
        description="Password reset token",
    )
    new_password = PasswordField(
        required=True,
        description="New password (minimum 8 characters with complexity requirements)",
    )

    @validates_schema
    def validate_password_reset(self, data, **kwargs):
        """Validate password reset data."""
        # Additional validation can be added here
        pass


class ChangePasswordSchema(Schema):
    """Schema for password change validation."""

    current_password = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Current password is required"),
        description="Current password",
    )
    new_password = PasswordField(
        required=True,
        description="New password (minimum 8 characters with complexity requirements)",
    )

    @validates_schema
    def validate_password_change(self, data, **kwargs):
        """Validate password change data."""
        if data.get("current_password") == data.get("new_password"):
            raise ValidationError(
                "New password must be different from current password"
            )


class EmailVerificationSchema(Schema):
    """Schema for email verification validation."""

    token = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Verification token is required"),
        description="Email verification token",
    )


class TokenResponseSchema(BaseModelSchema):
    """Schema for token response serialization."""

    access_token = fields.Str(required=True, description="JWT access token")
    refresh_token = fields.Str(description="JWT refresh token")
    token_type = fields.Str(required=True, description="Token type", default="Bearer")
    expires_in = fields.Int(
        required=True, description="Token expiration time in seconds"
    )


class LoginResponseSchema(Schema):
    """Schema for login response serialization."""

    success = fields.Bool(required=True, description="Login success status")
    message = fields.Str(required=True, description="Login result message")
    data = fields.Nested(
        "LoginDataSchema", required=True, description="Login response data"
    )


class LoginDataSchema(Schema):
    """Schema for login response data."""

    user = fields.Nested(
        "UserResponseSchema", required=True, description="User information"
    )
    tokens = fields.Nested(
        TokenResponseSchema, required=True, description="Authentication tokens"
    )


class RegisterResponseSchema(Schema):
    """Schema for registration response serialization."""

    success = fields.Bool(required=True, description="Registration success status")
    message = fields.Str(required=True, description="Registration result message")
    data = fields.Nested(
        "RegisterDataSchema", required=True, description="Registration response data"
    )


class RegisterDataSchema(Schema):
    """Schema for registration response data."""

    user = fields.Nested(
        "UserResponseSchema", required=True, description="User information"
    )
    verification_token = fields.Str(description="Email verification token")


class RefreshTokenResponseSchema(Schema):
    """Schema for token refresh response serialization."""

    success = fields.Bool(required=True, description="Token refresh success status")
    message = fields.Str(required=True, description="Token refresh result message")
    data = fields.Nested(
        "RefreshTokenDataSchema",
        required=True,
        description="Token refresh response data",
    )


class RefreshTokenDataSchema(Schema):
    """Schema for token refresh response data."""

    access_token = fields.Str(required=True, description="New JWT access token")
    token_type = fields.Str(required=True, description="Token type")
    expires_in = fields.Int(
        required=True, description="Token expiration time in seconds"
    )


class PasswordResetResponseSchema(Schema):
    """Schema for password reset response serialization."""

    success = fields.Bool(required=True, description="Password reset success status")
    message = fields.Str(required=True, description="Password reset result message")
    data = fields.Nested(
        "PasswordResetDataSchema", description="Password reset response data"
    )


class PasswordResetDataSchema(Schema):
    """Schema for password reset response data."""

    reset_token = fields.Str(description="Password reset token")
    expires_in = fields.Int(description="Token expiration time in seconds")


class EmailVerificationResponseSchema(Schema):
    """Schema for email verification response serialization."""

    success = fields.Bool(
        required=True, description="Email verification success status"
    )
    message = fields.Str(required=True, description="Email verification result message")
    data = fields.Nested(
        "EmailVerificationDataSchema", description="Email verification response data"
    )


class EmailVerificationDataSchema(Schema):
    """Schema for email verification response data."""

    user = fields.Nested("UserResponseSchema", description="Updated user information")
