"""
User-related Marshmallow schemas.

This module contains schemas for user management operations including
user creation, updates, queries, and response serialization.
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
    PaginationSchema,
    PasswordField,
    SearchSchema,
    SortingSchema,
    TimestampMixin,
    UsernameField,
)


class UserResponseSchema(BaseModelSchema, TimestampMixin):
    """Schema for user response serialization."""

    username = fields.Str(required=True, description="Username")
    email = fields.Str(required=True, description="Email address")
    first_name = fields.Str(allow_none=True, description="First name")
    last_name = fields.Str(allow_none=True, description="Last name")
    bio = fields.Str(allow_none=True, description="User biography")
    is_active = fields.Bool(required=True, description="Whether user is active")
    is_verified = fields.Bool(required=True, description="Whether email is verified")
    is_admin = fields.Bool(required=True, description="Whether user is admin")
    last_login_at = fields.DateTime(allow_none=True, description="Last login timestamp")
    failed_login_attempts = fields.Int(description="Number of failed login attempts")
    account_locked_until = fields.DateTime(
        allow_none=True, description="Account lock expiration"
    )

    # Computed fields
    full_name = fields.Method("get_full_name", description="Full name")
    is_locked = fields.Method("get_is_locked", description="Whether account is locked")

    def get_full_name(self, obj):
        """Get user's full name."""
        if hasattr(obj, "first_name") and hasattr(obj, "last_name"):
            parts = [obj.first_name, obj.last_name]
            return " ".join(filter(None, parts)) or None
        return None

    def get_is_locked(self, obj):
        """Check if account is locked."""
        if hasattr(obj, "is_account_locked"):
            return obj.is_account_locked()
        return False


class CreateUserRequestSchema(Schema):
    """Schema for create user request validation."""

    username = UsernameField(required=True, description="Username (3-80 characters)")
    email = EmailField(required=True, description="Email address")
    password = PasswordField(
        allow_none=True,
        description="Password (minimum 8 characters with complexity requirements, optional)",
    )
    first_name = NameField(
        allow_none=True, description="First name (max 50 characters)"
    )
    last_name = NameField(allow_none=True, description="Last name (max 50 characters)")
    bio = fields.Str(
        validate=validate.Length(max=500, error="Bio must be at most 500 characters"),
        allow_none=True,
        description="User biography (max 500 characters)",
    )
    is_admin = fields.Bool(missing=False, description="Whether user should be admin")
    is_verified = fields.Bool(
        missing=False, description="Whether email should be pre-verified"
    )

    @validates_schema
    def validate_create_user_data(self, data, **kwargs):
        """Validate user creation data."""
        # Additional cross-field validation can be added here
        pass

    @post_load
    def process_create_user_data(self, data, **kwargs):
        """Process user creation data after validation."""
        # Normalize email and username
        data["email"] = data["email"].strip().lower()
        data["username"] = data["username"].strip().lower()

        # Capitalize names if provided
        if data.get("first_name"):
            data["first_name"] = data["first_name"].strip().title()
        if data.get("last_name"):
            data["last_name"] = data["last_name"].strip().title()

        # Clean bio
        if data.get("bio"):
            data["bio"] = data["bio"].strip()

        return data


class UpdateUserRequestSchema(Schema):
    """Schema for update user request validation."""

    username = UsernameField(allow_none=True, description="Username (3-80 characters)")
    email = EmailField(allow_none=True, description="Email address")
    first_name = NameField(
        allow_none=True, description="First name (max 50 characters)"
    )
    last_name = NameField(allow_none=True, description="Last name (max 50 characters)")
    bio = fields.Str(
        validate=validate.Length(max=500, error="Bio must be at most 500 characters"),
        allow_none=True,
        description="User biography (max 500 characters)",
    )
    is_active = fields.Bool(
        allow_none=True, description="Whether user is active (admin only)"
    )
    is_verified = fields.Bool(
        allow_none=True, description="Whether email is verified (admin only)"
    )
    is_admin = fields.Bool(
        allow_none=True, description="Whether user is admin (admin only)"
    )

    @validates_schema
    def validate_update_user_data(self, data, **kwargs):
        """Validate user update data."""
        if not any(data.values()):
            raise ValidationError("At least one field must be provided for update")

    @post_load
    def process_update_user_data(self, data, **kwargs):
        """Process user update data after validation."""
        # Normalize email and username if provided
        if data.get("email"):
            data["email"] = data["email"].strip().lower()
        if data.get("username"):
            data["username"] = data["username"].strip().lower()

        # Capitalize names if provided
        if data.get("first_name"):
            data["first_name"] = data["first_name"].strip().title()
        if data.get("last_name"):
            data["last_name"] = data["last_name"].strip().title()

        # Clean bio if provided
        if data.get("bio") is not None:
            data["bio"] = data["bio"].strip() if data["bio"] else None

        return data


class UserQuerySchema(PaginationSchema, SortingSchema, SearchSchema):
    """Schema for user query parameters validation."""

    pass


class UserSearchSchema(SearchSchema):
    """Schema for user search parameters validation."""

    q = fields.Str(
        required=True,
        validate=validate.Length(
            min=2, max=100, error="Search term must be between 2 and 100 characters"
        ),
        description="Search term (min 2 characters)",
    )
    limit = fields.Int(
        validate=validate.Range(min=1, max=50, error="Limit must be between 1 and 50"),
        missing=20,
        description="Maximum results (max 50)",
    )


class SetAdminStatusSchema(Schema):
    """Schema for setting user admin status."""

    is_admin = fields.Bool(required=True, description="Whether user should be admin")


class UserListResponseSchema(Schema):
    """Schema for user list response serialization."""

    success = fields.Bool(required=True, description="Operation success status")
    data = fields.Nested(
        "UserListDataSchema", required=True, description="User list response data"
    )


class UserListDataSchema(Schema):
    """Schema for user list response data."""

    users = fields.List(
        fields.Nested(UserResponseSchema), required=True, description="List of users"
    )
    pagination = fields.Nested(
        "PaginationInfoSchema", required=True, description="Pagination information"
    )


class PaginationInfoSchema(Schema):
    """Schema for pagination information."""

    page = fields.Int(required=True, description="Current page number")
    per_page = fields.Int(required=True, description="Items per page")
    total = fields.Int(required=True, description="Total number of items")
    pages = fields.Int(required=True, description="Total number of pages")
    has_prev = fields.Bool(
        required=True, description="Whether there is a previous page"
    )
    has_next = fields.Bool(required=True, description="Whether there is a next page")


class UserSingleResponseSchema(Schema):
    """Schema for single user response serialization."""

    success = fields.Bool(required=True, description="Operation success status")
    message = fields.Str(description="Response message")
    data = fields.Nested(
        "UserDataSchema", required=True, description="User response data"
    )


class UserDataSchema(Schema):
    """Schema for single user response data."""

    user = fields.Nested(
        UserResponseSchema, required=True, description="User information"
    )


class UserStatisticsSchema(Schema):
    """Schema for user statistics."""

    total_users = fields.Int(required=True, description="Total number of users")
    active_users = fields.Int(required=True, description="Number of active users")
    inactive_users = fields.Int(required=True, description="Number of inactive users")
    verified_users = fields.Int(required=True, description="Number of verified users")
    unverified_users = fields.Int(
        required=True, description="Number of unverified users"
    )
    admin_users = fields.Int(required=True, description="Number of admin users")
    locked_users = fields.Int(required=True, description="Number of locked users")
    users_created_today = fields.Int(required=True, description="Users created today")
    users_created_this_week = fields.Int(
        required=True, description="Users created this week"
    )
    users_created_this_month = fields.Int(
        required=True, description="Users created this month"
    )


class UserStatisticsResponseSchema(Schema):
    """Schema for user statistics response serialization."""

    success = fields.Bool(required=True, description="Operation success status")
    data = fields.Nested(
        "UserStatisticsDataSchema",
        required=True,
        description="User statistics response data",
    )


class UserStatisticsDataSchema(Schema):
    """Schema for user statistics response data."""

    statistics = fields.Nested(
        UserStatisticsSchema, required=True, description="User statistics"
    )


class UserSearchResponseSchema(Schema):
    """Schema for user search response serialization."""

    success = fields.Bool(required=True, description="Operation success status")
    data = fields.Nested(
        "UserSearchDataSchema", required=True, description="User search response data"
    )


class UserSearchDataSchema(Schema):
    """Schema for user search response data."""

    users = fields.List(
        fields.Nested(UserResponseSchema),
        required=True,
        description="List of matching users",
    )
    search_term = fields.Str(required=True, description="Search term used")
    total_results = fields.Int(required=True, description="Total number of results")


class UserDeleteResponseSchema(Schema):
    """Schema for user deletion response serialization."""

    success = fields.Bool(required=True, description="Operation success status")
    message = fields.Str(required=True, description="Deletion result message")
    data = fields.Nested(
        "UserDeleteDataSchema", required=True, description="User deletion response data"
    )


class UserDeleteDataSchema(Schema):
    """Schema for user deletion response data."""

    user_id = fields.Int(required=True, description="Deleted user ID")
    soft_delete = fields.Bool(required=True, description="Whether it was a soft delete")
