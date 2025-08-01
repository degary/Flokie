"""
User Management Controller Module

This module provides REST API endpoints for user management including
CRUD operations, user information queries and updates, and user permission management.
"""

import logging

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required
from marshmallow import Schema, ValidationError, fields, validate

from app.models.user import User
from app.services.user_service import UserService, UserServiceError

logger = logging.getLogger(__name__)

# Create user management blueprint
user_bp = Blueprint("users", __name__, url_prefix="/api/users")


# Request/Response Schemas for validation and documentation
class CreateUserRequestSchema(Schema):
    """Schema for create user request validation."""

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(validate=validate.Length(min=8), allow_none=True)
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    is_admin = fields.Bool(missing=False)
    is_verified = fields.Bool(missing=False)


class UpdateUserRequestSchema(Schema):
    """Schema for update user request validation."""

    username = fields.Str(validate=validate.Length(min=3, max=80), allow_none=True)
    email = fields.Email(validate=validate.Length(max=120), allow_none=True)
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    bio = fields.Str(validate=validate.Length(max=500), allow_none=True)
    is_active = fields.Bool(allow_none=True)
    is_verified = fields.Bool(allow_none=True)
    is_admin = fields.Bool(allow_none=True)


class UserQuerySchema(Schema):
    """Schema for user query parameters validation."""

    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), missing=20)
    include_inactive = fields.Bool(missing=False)
    search = fields.Str(validate=validate.Length(max=100), allow_none=True)
    sort_by = fields.Str(
        validate=validate.OneOf(["created_at", "updated_at", "username", "email"]),
        missing="created_at",
    )
    sort_order = fields.Str(validate=validate.OneOf(["asc", "desc"]), missing="desc")


class UserSearchSchema(Schema):
    """Schema for user search parameters validation."""

    q = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    limit = fields.Int(validate=validate.Range(min=1, max=50), missing=20)
    include_inactive = fields.Bool(missing=False)


def handle_validation_error(error):
    """
    Handle marshmallow validation errors.

    Args:
        error (ValidationError): Validation error

    Returns:
        tuple: Error response and status code
    """
    logger.warning(f"Validation error: {error.messages}")
    return (
        jsonify(
            {
                "error": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": error.messages,
            }
        ),
        400,
    )


def handle_user_service_error(error):
    """
    Handle user service errors.

    Args:
        error (UserServiceError): User service error

    Returns:
        tuple: Error response and status code
    """
    logger.warning(f"User service error: {error.message}")
    return jsonify({"error": error.message, "code": error.code}), error.status_code


def check_admin_permission(current_user):
    """
    Check if current user has admin permissions.

    Args:
        current_user (User): Current authenticated user

    Raises:
        UserServiceError: If user doesn't have admin permissions
    """
    if not current_user.is_admin:
        raise UserServiceError(
            "Admin privileges required",
            code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
        )


def check_user_access_permission(current_user, target_user_id):
    """
    Check if current user can access target user's information.

    Args:
        current_user (User): Current authenticated user
        target_user_id (int): Target user ID

    Returns:
        bool: True if access is allowed, False otherwise
    """
    # Users can always access their own information
    if current_user.id == target_user_id:
        return True

    # Admin users can access any user's information
    if current_user.is_admin:
        return True

    return False


@user_bp.route("", methods=["GET"])
@jwt_required()
def get_users():
    """
    Get paginated list of users with optional filtering and sorting.

    Headers:
        Authorization: Bearer <access_token>

    Query Parameters:
        page (int, optional): Page number (default: 1)
        per_page (int, optional): Users per page (default: 20, max: 100)
        include_inactive (bool, optional): Include inactive users (default: false)
        search (str, optional): Search term for username, email, or name
        sort_by (str, optional): Field to sort by (default: 'created_at')
        sort_order (str, optional): Sort order 'asc' or 'desc' (default: 'desc')

    Returns:
        JSON: Paginated user data with metadata

    Status Codes:
        200: Users retrieved successfully
        400: Invalid query parameters
        401: Invalid or expired access token
        403: Insufficient permissions
        500: Internal server error
    """
    logger.info("Get users request received")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Validate query parameters
        schema = UserQuerySchema()
        query_params = schema.load(request.args.to_dict())

        # Get users from service
        result = UserService.get_users(
            page=query_params["page"],
            per_page=query_params["per_page"],
            include_inactive=query_params["include_inactive"],
            search=query_params.get("search"),
            sort_by=query_params["sort_by"],
            sort_order=query_params["sort_order"],
        )

        logger.info(
            f"Retrieved {len(result['users'])} users (page {query_params['page']})"
        )

        return jsonify({"success": True, "data": result}), 200

    except ValidationError as e:
        return handle_validation_error(e)
    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error getting users: {e}")
        return (
            jsonify({"error": "Failed to retrieve users", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    """
    Get user by ID.

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Returns:
        JSON: User information

    Status Codes:
        200: User retrieved successfully
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Get user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()

        if not check_user_access_permission(current_user, user_id):
            raise UserServiceError(
                "Insufficient permissions to access this user",
                code="INSUFFICIENT_PERMISSIONS",
                status_code=403,
            )

        # Get user from service
        user = UserService.get_user_by_id(
            user_id, include_inactive=current_user.is_admin
        )

        if not user:
            raise UserServiceError(
                "User not found", code="USER_NOT_FOUND", status_code=404
            )

        logger.info(f"User retrieved: {user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error getting user {user_id}: {e}")
        return (
            jsonify({"error": "Failed to retrieve user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("", methods=["POST"])
@jwt_required()
def create_user():
    """
    Create a new user (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Request Body:
        username (str): Username
        email (str): Email address
        password (str, optional): Password (if None, user must reset password)
        first_name (str, optional): First name
        last_name (str, optional): Last name
        is_admin (bool, optional): Whether user should be admin (default: false)
        is_verified (bool, optional): Whether email should be pre-verified (default: false)

    Returns:
        JSON: Created user information

    Status Codes:
        201: User created successfully
        400: Invalid request data
        401: Invalid or expired access token
        403: Insufficient permissions
        409: Username or email already exists
        500: Internal server error
    """
    logger.info("Create user request received")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Validate request data
        schema = CreateUserRequestSchema()
        data = schema.load(request.get_json() or {})

        # Create user
        user = UserService.create_user(
            username=data["username"],
            email=data["email"],
            password=data.get("password"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            is_admin=data.get("is_admin", False),
            is_verified=data.get("is_verified", False),
            created_by_user=current_user,
        )

        logger.info(f"User created: {user.username} by {current_user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User created successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            201,
        )

    except ValidationError as e:
        return handle_validation_error(e)
    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        return (
            jsonify({"error": "Failed to create user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    """
    Update user information.

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Request Body:
        username (str, optional): Username
        email (str, optional): Email address
        first_name (str, optional): First name
        last_name (str, optional): Last name
        bio (str, optional): User bio
        is_active (bool, optional): Whether user is active (admin only)
        is_verified (bool, optional): Whether email is verified (admin only)
        is_admin (bool, optional): Whether user is admin (admin only)

    Returns:
        JSON: Updated user information

    Status Codes:
        200: User updated successfully
        400: Invalid request data
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        409: Username or email already exists
        500: Internal server error
    """
    logger.info(f"Update user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()

        if not check_user_access_permission(current_user, user_id):
            raise UserServiceError(
                "Insufficient permissions to update this user",
                code="INSUFFICIENT_PERMISSIONS",
                status_code=403,
            )

        # Validate request data
        schema = UpdateUserRequestSchema()
        data = schema.load(request.get_json() or {})

        # Filter admin-only fields for non-admin users
        if not current_user.is_admin:
            admin_only_fields = ["is_active", "is_verified", "is_admin"]
            for field in admin_only_fields:
                if field in data:
                    del data[field]

        # Update user
        user = UserService.update_user(
            user_id=user_id, update_data=data, updated_by_user=current_user
        )

        logger.info(f"User updated: {user.username} by {current_user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User updated successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except ValidationError as e:
        return handle_validation_error(e)
    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error updating user {user_id}: {e}")
        return (
            jsonify({"error": "Failed to update user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """
    Delete user (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Query Parameters:
        hard_delete (bool, optional): Whether to permanently delete (default: false)

    Returns:
        JSON: Deletion result

    Status Codes:
        200: User deleted successfully
        400: Invalid request
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Delete user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Get query parameters
        hard_delete = request.args.get("hard_delete", "false").lower() == "true"

        # Delete user
        result = UserService.delete_user(
            user_id=user_id, deleted_by_user=current_user, soft_delete=not hard_delete
        )

        logger.info(
            f"User deleted (hard_delete={hard_delete}) by {current_user.username}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": result["message"],
                    "data": {
                        "user_id": result["user_id"],
                        "soft_delete": result["soft_delete"],
                    },
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error deleting user {user_id}: {e}")
        return (
            jsonify({"error": "Failed to delete user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>/activate", methods=["POST"])
@jwt_required()
def activate_user(user_id):
    """
    Activate user account (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Returns:
        JSON: Activation result

    Status Codes:
        200: User activated successfully
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Activate user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Activate user
        user = UserService.activate_user(
            user_id=user_id, activated_by_user=current_user
        )

        logger.info(f"User activated: {user.username} by {current_user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User activated successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error activating user {user_id}: {e}")
        return (
            jsonify({"error": "Failed to activate user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>/deactivate", methods=["POST"])
@jwt_required()
def deactivate_user(user_id):
    """
    Deactivate user account (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Returns:
        JSON: Deactivation result

    Status Codes:
        200: User deactivated successfully
        400: Cannot deactivate own account
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Deactivate user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Deactivate user
        user = UserService.deactivate_user(
            user_id=user_id, deactivated_by_user=current_user
        )

        logger.info(f"User deactivated: {user.username} by {current_user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User deactivated successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error deactivating user {user_id}: {e}")
        return (
            jsonify({"error": "Failed to deactivate user", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/<int:user_id>/unlock", methods=["POST"])
@jwt_required()
def unlock_user(user_id):
    """
    Unlock user account (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Returns:
        JSON: Unlock result

    Status Codes:
        200: User unlocked successfully
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Unlock user request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Unlock user
        user = UserService.unlock_user_account(
            user_id=user_id, unlocked_by_user=current_user
        )

        logger.info(f"User unlocked: {user.username} by {current_user.username}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User account unlocked successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error unlocking user {user_id}: {e}")
        return (
            jsonify(
                {"error": "Failed to unlock user account", "code": "INTERNAL_ERROR"}
            ),
            500,
        )


@user_bp.route("/<int:user_id>/admin", methods=["POST"])
@jwt_required()
def set_admin_status(user_id):
    """
    Set user admin status (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        user_id (int): User ID

    Request Body:
        is_admin (bool): Whether user should be admin

    Returns:
        JSON: Admin status update result

    Status Codes:
        200: Admin status updated successfully
        400: Invalid request data or cannot demote self
        401: Invalid or expired access token
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    logger.info(f"Set admin status request received for ID: {user_id}")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Validate request data
        data = request.get_json() or {}
        if "is_admin" not in data:
            raise UserServiceError(
                "is_admin field is required",
                code="MISSING_REQUIRED_FIELD",
                status_code=400,
            )

        is_admin = data["is_admin"]
        if not isinstance(is_admin, bool):
            raise UserServiceError(
                "is_admin must be a boolean value",
                code="INVALID_FIELD_TYPE",
                status_code=400,
            )

        # Set admin status
        user = UserService.set_user_admin_status(
            user_id=user_id, is_admin=is_admin, updated_by_user=current_user
        )

        status = "granted" if is_admin else "revoked"
        logger.info(
            f"Admin privileges {status} for user: {user.username} by {current_user.username}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Admin privileges {status} successfully",
                    "data": {"user": user.to_dict(exclude_fields=["password_hash"])},
                }
            ),
            200,
        )

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error setting admin status for user {user_id}: {e}")
        return (
            jsonify(
                {"error": "Failed to update admin status", "code": "INTERNAL_ERROR"}
            ),
            500,
        )


@user_bp.route("/search", methods=["GET"])
@jwt_required()
def search_users():
    """
    Search users by username, email, or name (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Query Parameters:
        q (str): Search term (min 2 characters)
        limit (int, optional): Maximum results (default: 20, max: 50)
        include_inactive (bool, optional): Include inactive users (default: false)

    Returns:
        JSON: List of matching users

    Status Codes:
        200: Search completed successfully
        400: Invalid query parameters
        401: Invalid or expired access token
        403: Insufficient permissions
        500: Internal server error
    """
    logger.info("Search users request received")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Validate query parameters
        schema = UserSearchSchema()
        query_params = schema.load(request.args.to_dict())

        # Search users
        users = UserService.search_users(
            search_term=query_params["q"],
            limit=query_params["limit"],
            include_inactive=query_params["include_inactive"],
        )

        # Convert to dictionaries
        users_data = [user.to_dict(exclude_fields=["password_hash"]) for user in users]

        logger.info(
            f"Search completed: found {len(users_data)} users for term '{query_params['q']}'"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "users": users_data,
                        "search_term": query_params["q"],
                        "total_results": len(users_data),
                    },
                }
            ),
            200,
        )

    except ValidationError as e:
        return handle_validation_error(e)
    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error searching users: {e}")
        return (
            jsonify({"error": "Failed to search users", "code": "INTERNAL_ERROR"}),
            500,
        )


@user_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_user_statistics():
    """
    Get user statistics (admin only).

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        JSON: User statistics

    Status Codes:
        200: Statistics retrieved successfully
        401: Invalid or expired access token
        403: Insufficient permissions
        500: Internal server error
    """
    logger.info("Get user statistics request received")

    try:
        # Get current user and check permissions
        current_user = get_current_user()
        check_admin_permission(current_user)

        # Get statistics
        stats = UserService.get_user_statistics()

        logger.info("User statistics retrieved successfully")

        return jsonify({"success": True, "data": {"statistics": stats}}), 200

    except UserServiceError as e:
        return handle_user_service_error(e)
    except Exception as e:
        logger.error(f"Unexpected error getting user statistics: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to retrieve user statistics",
                    "code": "INTERNAL_ERROR",
                }
            ),
            500,
        )


# Error handlers for the blueprint
@user_bp.errorhandler(ValidationError)
def handle_marshmallow_error(error):
    """Handle marshmallow validation errors."""
    return handle_validation_error(error)


@user_bp.errorhandler(UserServiceError)
def handle_user_service_error_handler(error):
    """Handle user service errors."""
    return handle_user_service_error(error)


@user_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found", "code": "NOT_FOUND"}), 404


@user_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed", "code": "METHOD_NOT_ALLOWED"}), 405


@user_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error in user controller: {error}")
    return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500
