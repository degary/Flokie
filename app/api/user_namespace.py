"""
User Management API namespace for Flask-RESTX documentation.

This module defines the user management API endpoints with comprehensive
documentation using Flask-RESTX decorators and models.
"""

from flask import request
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required

from app.api.models import (
    user_model, user_response_model, user_list_response_model,
    create_user_request_model, update_user_request_model, set_admin_status_model,
    user_statistics_response_model, success_model, error_model, validation_error_model
)

# Create user management namespace
user_ns = Namespace('users', description='User management operations', path='/users')

# Add models to namespace
user_ns.models[user_model.name] = user_model
user_ns.models[user_response_model.name] = user_response_model
user_ns.models[user_list_response_model.name] = user_list_response_model
user_ns.models[create_user_request_model.name] = create_user_request_model
user_ns.models[update_user_request_model.name] = update_user_request_model
user_ns.models[set_admin_status_model.name] = set_admin_status_model
user_ns.models[user_statistics_response_model.name] = user_statistics_response_model
user_ns.models[success_model.name] = success_model
user_ns.models[error_model.name] = error_model
user_ns.models[validation_error_model.name] = validation_error_model


@user_ns.route('')
class UserListResource(Resource):
    @user_ns.doc('get_users', security='Bearer')
    @user_ns.param('page', 'Page number', type='integer', default=1)
    @user_ns.param('per_page', 'Users per page (max 100)', type='integer', default=20)
    @user_ns.param('include_inactive', 'Include inactive users', type='boolean', default=False)
    @user_ns.param('search', 'Search term for username, email, or name', type='string')
    @user_ns.param('sort_by', 'Field to sort by', type='string', enum=['created_at', 'updated_at', 'username', 'email'], default='created_at')
    @user_ns.param('sort_order', 'Sort order', type='string', enum=['asc', 'desc'], default='desc')
    @user_ns.marshal_with(user_list_response_model, code=200, description='Users retrieved successfully')
    @user_ns.response(400, 'Invalid query parameters', validation_error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """
        Get paginated list of users
        
        Retrieve a paginated list of users with optional filtering and sorting.
        Requires admin privileges.
        """
        # This is handled by the actual controller
        pass

    @user_ns.doc('create_user', security='Bearer')
    @user_ns.expect(create_user_request_model, validate=True)
    @user_ns.marshal_with(user_response_model, code=201, description='User created successfully')
    @user_ns.response(400, 'Invalid request data', validation_error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(409, 'Username or email already exists', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self):
        """
        Create a new user
        
        Create a new user account. Requires admin privileges.
        If no password is provided, user must reset password before first login.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/<int:user_id>')
@user_ns.param('user_id', 'User ID')
class UserResource(Resource):
    @user_ns.doc('get_user', security='Bearer')
    @user_ns.marshal_with(user_response_model, code=200, description='User retrieved successfully')
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self, user_id):
        """
        Get user by ID
        
        Retrieve user information by ID.
        Users can access their own information, admins can access any user.
        """
        # This is handled by the actual controller
        pass

    @user_ns.doc('update_user', security='Bearer')
    @user_ns.expect(update_user_request_model, validate=True)
    @user_ns.marshal_with(user_response_model, code=200, description='User updated successfully')
    @user_ns.response(400, 'Invalid request data', validation_error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(409, 'Username or email already exists', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def put(self, user_id):
        """
        Update user information
        
        Update user information by ID.
        Users can update their own information, admins can update any user.
        Some fields (is_active, is_verified, is_admin) are admin-only.
        """
        # This is handled by the actual controller
        pass

    @user_ns.doc('delete_user', security='Bearer')
    @user_ns.param('hard_delete', 'Whether to permanently delete', type='boolean', default=False)
    @user_ns.marshal_with(success_model, code=200, description='User deleted successfully')
    @user_ns.response(400, 'Invalid request', error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def delete(self, user_id):
        """
        Delete user
        
        Delete user by ID. Requires admin privileges.
        By default performs soft delete (deactivates user).
        Use hard_delete=true for permanent deletion.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/<int:user_id>/activate')
@user_ns.param('user_id', 'User ID')
class UserActivateResource(Resource):
    @user_ns.doc('activate_user', security='Bearer')
    @user_ns.marshal_with(user_response_model, code=200, description='User activated successfully')
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self, user_id):
        """
        Activate user account
        
        Activate a user account. Requires admin privileges.
        Sets the user's is_active flag to True.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/<int:user_id>/deactivate')
@user_ns.param('user_id', 'User ID')
class UserDeactivateResource(Resource):
    @user_ns.doc('deactivate_user', security='Bearer')
    @user_ns.marshal_with(user_response_model, code=200, description='User deactivated successfully')
    @user_ns.response(400, 'Cannot deactivate own account', error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self, user_id):
        """
        Deactivate user account
        
        Deactivate a user account. Requires admin privileges.
        Sets the user's is_active flag to False.
        Admins cannot deactivate their own account.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/<int:user_id>/unlock')
@user_ns.param('user_id', 'User ID')
class UserUnlockResource(Resource):
    @user_ns.doc('unlock_user', security='Bearer')
    @user_ns.marshal_with(user_response_model, code=200, description='User unlocked successfully')
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self, user_id):
        """
        Unlock user account
        
        Unlock a locked user account. Requires admin privileges.
        Resets failed login attempts and unlocks the account.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/<int:user_id>/admin')
@user_ns.param('user_id', 'User ID')
class UserAdminStatusResource(Resource):
    @user_ns.doc('set_admin_status', security='Bearer')
    @user_ns.expect(set_admin_status_model, validate=True)
    @user_ns.marshal_with(user_response_model, code=200, description='Admin status updated successfully')
    @user_ns.response(400, 'Invalid request data or cannot demote self', validation_error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(404, 'User not found', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self, user_id):
        """
        Set user admin status
        
        Grant or revoke admin privileges for a user. Requires admin privileges.
        Admins cannot revoke their own admin status.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/search')
class UserSearchResource(Resource):
    @user_ns.doc('search_users', security='Bearer')
    @user_ns.param('q', 'Search term (min 2 characters)', type='string', required=True)
    @user_ns.param('limit', 'Maximum results (max 50)', type='integer', default=20)
    @user_ns.param('include_inactive', 'Include inactive users', type='boolean', default=False)
    @user_ns.marshal_with(user_list_response_model, code=200, description='Search completed successfully')
    @user_ns.response(400, 'Invalid query parameters', validation_error_model)
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """
        Search users
        
        Search users by username, email, or name. Requires admin privileges.
        Searches across username, email, first_name, and last_name fields.
        """
        # This is handled by the actual controller
        pass


@user_ns.route('/statistics')
class UserStatisticsResource(Resource):
    @user_ns.doc('get_user_statistics', security='Bearer')
    @user_ns.marshal_with(user_statistics_response_model, code=200, description='Statistics retrieved successfully')
    @user_ns.response(401, 'Invalid or expired access token', error_model)
    @user_ns.response(403, 'Insufficient permissions', error_model)
    @user_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """
        Get user statistics
        
        Retrieve comprehensive user statistics. Requires admin privileges.
        Includes counts of total, active, inactive, verified, admin users, etc.
        """
        # This is handled by the actual controller
        pass