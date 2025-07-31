"""
Authentication Controller Module

This module provides REST API endpoints for user authentication including
login, registration, token refresh, password reset, and email verification.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_current_user
from marshmallow import Schema, fields, ValidationError, validate

from app.services.auth_service import AuthService, AuthenticationError
from app.models.user import User

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


# Request/Response Schemas for validation and documentation
class LoginRequestSchema(Schema):
    """Schema for login request validation."""
    username_or_email = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    password = fields.Str(required=True, validate=validate.Length(min=1))
    remember_me = fields.Bool(missing=False)


class RegisterRequestSchema(Schema):
    """Schema for registration request validation."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)


class PasswordResetRequestSchema(Schema):
    """Schema for password reset request validation."""
    email = fields.Email(required=True, validate=validate.Length(max=120))


class PasswordResetSchema(Schema):
    """Schema for password reset validation."""
    token = fields.Str(required=True, validate=validate.Length(min=1))
    new_password = fields.Str(required=True, validate=validate.Length(min=8))


class ChangePasswordSchema(Schema):
    """Schema for password change validation."""
    current_password = fields.Str(required=True, validate=validate.Length(min=1))
    new_password = fields.Str(required=True, validate=validate.Length(min=8))


class EmailVerificationSchema(Schema):
    """Schema for email verification validation."""
    token = fields.Str(required=True, validate=validate.Length(min=1))


def handle_validation_error(error):
    """
    Handle marshmallow validation errors.
    
    Args:
        error (ValidationError): Validation error
        
    Returns:
        tuple: Error response and status code
    """
    logger.warning(f"Validation error: {error.messages}")
    return jsonify({
        'error': 'Validation failed',
        'code': 'VALIDATION_ERROR',
        'details': error.messages
    }), 400


def handle_auth_error(error):
    """
    Handle authentication service errors.
    
    Args:
        error (AuthenticationError): Authentication error
        
    Returns:
        tuple: Error response and status code
    """
    logger.warning(f"Authentication error: {error.message}")
    return jsonify({
        'error': error.message,
        'code': error.code
    }), error.status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Request Body:
        username_or_email (str): Username or email address
        password (str): User password
        remember_me (bool, optional): Whether to create longer-lived tokens
        
    Returns:
        JSON: Authentication result with tokens and user info
        
    Status Codes:
        200: Login successful
        400: Invalid request data
        401: Invalid credentials
        403: Account inactive
        423: Account locked
        500: Internal server error
    """
    logger.info("Login request received")
    
    try:
        # Validate request data
        schema = LoginRequestSchema()
        data = schema.load(request.get_json() or {})
        
        # Authenticate user
        result = AuthService.login(
            username_or_email=data['username_or_email'],
            password=data['password'],
            remember_me=data.get('remember_me', False)
        )
        
        logger.info(f"Login successful for user: {result['user']['username']}")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'user': result['user'],
                'tokens': result['tokens']
            }
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return jsonify({
            'error': 'Login failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    
    Request Body:
        username (str): Desired username
        email (str): User email address
        password (str): User password (min 8 characters)
        first_name (str, optional): User's first name
        last_name (str, optional): User's last name
        
    Returns:
        JSON: Registration result with user info and verification token
        
    Status Codes:
        201: Registration successful
        400: Invalid request data
        409: Username or email already exists
        500: Internal server error
    """
    logger.info("Registration request received")
    
    try:
        # Validate request data
        schema = RegisterRequestSchema()
        data = schema.load(request.get_json() or {})
        
        # Register user
        result = AuthService.register(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        logger.info(f"Registration successful for user: {result['user']['username']}")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'user': result['user'],
                'verification_token': result['verification_token']
            }
        }), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        return jsonify({
            'error': 'Registration failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Token refresh endpoint.
    
    Headers:
        Authorization: Bearer <refresh_token>
        
    Returns:
        JSON: New access token
        
    Status Codes:
        200: Token refreshed successfully
        401: Invalid or expired refresh token
        403: Account inactive or locked
        500: Internal server error
    """
    logger.info("Token refresh request received")
    
    try:
        # Get current user from refresh token
        current_user = get_current_user()
        
        # Generate new access token
        result = AuthService.refresh_token(current_user)
        
        logger.info(f"Token refreshed for user: {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'access_token': result['access_token'],
                'token_type': result['token_type'],
                'expires_in': result['expires_in']
            }
        }), 200
        
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        return jsonify({
            'error': 'Token refresh failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/password/reset-request', methods=['POST'])
def request_password_reset():
    """
    Password reset request endpoint.
    
    Request Body:
        email (str): User email address
        
    Returns:
        JSON: Password reset request result
        
    Status Codes:
        200: Reset request processed (always returns 200 for security)
        400: Invalid request data
        500: Internal server error
    """
    logger.info("Password reset request received")
    
    try:
        # Validate request data
        schema = PasswordResetRequestSchema()
        data = schema.load(request.get_json() or {})
        
        # Process password reset request
        result = AuthService.request_password_reset(data['email'])
        
        logger.info(f"Password reset requested for email: {data['email']}")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'reset_token': result.get('reset_token'),
                'expires_in': result.get('expires_in')
            } if 'reset_token' in result else None
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during password reset request: {e}")
        return jsonify({
            'error': 'Password reset request failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/password/reset', methods=['POST'])
def reset_password():
    """
    Password reset endpoint.
    
    Request Body:
        token (str): Password reset token
        new_password (str): New password (min 8 characters)
        
    Returns:
        JSON: Password reset result
        
    Status Codes:
        200: Password reset successful
        400: Invalid request data or token
        500: Internal server error
    """
    logger.info("Password reset request received")
    
    try:
        # Validate request data
        schema = PasswordResetSchema()
        data = schema.load(request.get_json() or {})
        
        # Reset password
        result = AuthService.reset_password(
            token=data['token'],
            new_password=data['new_password']
        )
        
        logger.info("Password reset completed successfully")
        
        return jsonify({
            'success': True,
            'message': result['message']
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {e}")
        return jsonify({
            'error': 'Password reset failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/password/change', methods=['POST'])
@jwt_required()
def change_password():
    """
    Password change endpoint (requires authentication).
    
    Headers:
        Authorization: Bearer <access_token>
        
    Request Body:
        current_password (str): Current password
        new_password (str): New password (min 8 characters)
        
    Returns:
        JSON: Password change result
        
    Status Codes:
        200: Password changed successfully
        400: Invalid request data or current password
        401: Invalid or expired access token
        500: Internal server error
    """
    logger.info("Password change request received")
    
    try:
        # Get current user
        current_user = get_current_user()
        
        # Validate request data
        schema = ChangePasswordSchema()
        data = schema.load(request.get_json() or {})
        
        # Change password
        result = AuthService.change_password(
            user=current_user,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        logger.info(f"Password changed for user: {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': result['message']
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during password change: {e}")
        return jsonify({
            'error': 'Password change failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/email/verify', methods=['POST'])
def verify_email():
    """
    Email verification endpoint.
    
    Request Body:
        token (str): Email verification token
        
    Returns:
        JSON: Email verification result
        
    Status Codes:
        200: Email verified successfully
        400: Invalid request data or token
        500: Internal server error
    """
    logger.info("Email verification request received")
    
    try:
        # Validate request data
        schema = EmailVerificationSchema()
        data = schema.load(request.get_json() or {})
        
        # Verify email
        result = AuthService.verify_email(data['token'])
        
        logger.info("Email verification completed successfully")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'user': result.get('user')
            } if 'user' in result else None
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthenticationError as e:
        return handle_auth_error(e)
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}")
        return jsonify({
            'error': 'Email verification failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint.
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        JSON: Logout result
        
    Status Codes:
        200: Logout successful
        401: Invalid or expired access token
        500: Internal server error
    """
    logger.info("Logout request received")
    
    try:
        # Get current user
        current_user = get_current_user()
        
        # Process logout
        result = AuthService.logout(current_user)
        
        logger.info(f"Logout successful for user: {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': result['message']
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}")
        return jsonify({
            'error': 'Logout failed due to server error',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Get current user information endpoint.
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        JSON: Current user information
        
    Status Codes:
        200: User information retrieved successfully
        401: Invalid or expired access token
        500: Internal server error
    """
    logger.info("Current user info request received")
    
    try:
        # Get current user
        current_user = get_current_user()
        
        logger.info(f"Current user info retrieved for: {current_user.username}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': current_user.to_dict(exclude_fields=['password_hash'])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error getting current user info: {e}")
        return jsonify({
            'error': 'Failed to retrieve user information',
            'code': 'INTERNAL_ERROR'
        }), 500


# Error handlers for the blueprint
@auth_bp.errorhandler(ValidationError)
def handle_marshmallow_error(error):
    """Handle marshmallow validation errors."""
    return handle_validation_error(error)


@auth_bp.errorhandler(AuthenticationError)
def handle_authentication_error(error):
    """Handle authentication service errors."""
    return handle_auth_error(error)


@auth_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404


@auth_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405


@auth_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error in auth controller: {error}")
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500