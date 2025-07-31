"""
Authentication Service Module

This module provides authentication services including user login validation,
JWT token generation and refresh, password reset, and user registration functionality.
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.user import User
from app.utils.exceptions import (
    AuthenticationError, ValidationError, ConflictError, 
    InvalidCredentialsError, UserNotFoundError, BusinessLogicError
)
from app.utils.error_helpers import (
    validate_required_fields, validate_field_length, handle_duplicate_resource,
    validate_business_rule
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service class providing user authentication functionality.
    
    This service handles:
    - User login validation
    - JWT token generation and refresh
    - Password reset functionality
    - User registration
    - Account security features
    """
    
    @staticmethod
    def login(username_or_email: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """
        Authenticate user and generate JWT tokens.
        
        Args:
            username_or_email (str): Username or email address
            password (str): User password
            remember_me (bool): Whether to create longer-lived tokens
            
        Returns:
            Dict[str, Any]: Authentication result with tokens and user info
            
        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info(f"Login attempt for: {username_or_email}")
        
        # Input validation
        validate_required_fields(
            {'username_or_email': username_or_email, 'password': password},
            ['username_or_email', 'password']
        )
        
        # Find user by username or email
        user = AuthService._find_user_by_login(username_or_email)
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username_or_email}")
            raise InvalidCredentialsError()
        
        # Check if account is active
        validate_business_rule(
            user.is_active,
            "Account is deactivated. Please contact support.",
            details={'user_id': user.id, 'username': user.username}
        )
        
        # Check if account is locked
        validate_business_rule(
            not user.is_account_locked(),
            "Account is temporarily locked due to multiple failed login attempts. Please try again later.",
            details={'user_id': user.id, 'username': user.username}
        )
        
        # Verify password
        if not user.check_password(password):
            logger.warning(f"Invalid password for user: {user.username}")
            
            # Save failed attempt (check_password already increments counter)
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to save login attempt for user {user.username}: {e}")
                db.session.rollback()
            
            raise InvalidCredentialsError()
        
        # Generate tokens
        try:
            tokens = AuthService._generate_tokens(user, remember_me)
            
            # Save successful login
            db.session.commit()
            
            logger.info(f"Successful login for user: {user.username}")
            
            return {
                'user': user.to_dict(exclude_fields=['password_hash']),
                'tokens': tokens,
                'message': 'Login successful'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate tokens for user {user.username}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Authentication failed. Please try again.",
                code="TOKEN_GENERATION_ERROR",
                status_code=500
            )
    
    @staticmethod
    def refresh_token(current_user: User) -> Dict[str, Any]:
        """
        Generate new access token using refresh token.
        
        Args:
            current_user (User): Current authenticated user from JWT
            
        Returns:
            Dict[str, Any]: New access token
            
        Raises:
            AuthenticationError: If refresh fails
        """
        logger.info(f"Token refresh for user: {current_user.username}")
        
        # Verify user is still active and not locked
        if not current_user.is_active:
            logger.warning(f"Token refresh denied for inactive user: {current_user.username}")
            raise AuthenticationError(
                "Account is deactivated",
                code="ACCOUNT_INACTIVE",
                status_code=403
            )
        
        if current_user.is_account_locked():
            logger.warning(f"Token refresh denied for locked user: {current_user.username}")
            raise AuthenticationError(
                "Account is locked",
                code="ACCOUNT_LOCKED",
                status_code=423
            )
        
        try:
            # Generate new access token
            access_token = create_access_token(
                identity=current_user,
                expires_delta=timedelta(hours=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1))
            )
            
            logger.info(f"Token refreshed successfully for user: {current_user.username}")
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1) * 3600,
                'message': 'Token refreshed successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh token for user {current_user.username}: {e}")
            raise AuthenticationError(
                "Token refresh failed",
                code="TOKEN_REFRESH_ERROR",
                status_code=500
            )
    
    @staticmethod
    def register(username: str, email: str, password: str, first_name: str = None, 
                last_name: str = None) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            username (str): Desired username
            email (str): User email address
            password (str): User password
            first_name (str, optional): User's first name
            last_name (str, optional): User's last name
            
        Returns:
            Dict[str, Any]: Registration result with user info
            
        Raises:
            AuthenticationError: If registration fails
        """
        logger.info(f"Registration attempt for username: {username}, email: {email}")
        
        # Input validation
        validate_required_fields(
            {'username': username, 'email': email, 'password': password},
            ['username', 'email', 'password']
        )
        
        # Validate field lengths
        validate_field_length(
            {'username': username, 'email': email, 'password': password},
            {
                'username': {'min': 3, 'max': 50},
                'email': {'min': 5, 'max': 100},
                'password': {'min': 8, 'max': 128}
            }
        )
        
        # Check if username already exists
        if User.get_by_username(username):
            logger.warning(f"Registration attempt with existing username: {username}")
            handle_duplicate_resource('username', username, 'User')
        
        # Check if email already exists
        if User.get_by_email(email):
            logger.warning(f"Registration attempt with existing email: {email}")
            handle_duplicate_resource('email', email, 'User')
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                password=password,  # Will be hashed in User.__init__
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False  # Email verification required
            )
            
            # Generate email verification token
            verification_token = AuthService._generate_secure_token()
            user.set_email_verification_token(verification_token)
            
            # Save user
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User registered successfully: {user.username}")
            
            return {
                'user': user.to_dict(exclude_fields=['password_hash']),
                'verification_token': verification_token,
                'message': 'Registration successful. Please verify your email address.'
            }
            
        except Exception as e:
            logger.error(f"Registration failed for username {username}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Registration failed. Please try again.",
                code="REGISTRATION_ERROR",
                status_code=500
            )
    
    @staticmethod
    def request_password_reset(email: str) -> Dict[str, Any]:
        """
        Generate password reset token for user.
        
        Args:
            email (str): User email address
            
        Returns:
            Dict[str, Any]: Password reset result
            
        Raises:
            AuthenticationError: If request fails
        """
        logger.info(f"Password reset requested for email: {email}")
        
        if not email:
            raise AuthenticationError(
                "Email address is required",
                code="MISSING_EMAIL",
                status_code=400
            )
        
        # Find user by email
        user = User.get_by_email(email)
        if not user:
            # Don't reveal if email exists or not for security
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return {
                'message': 'If the email address exists, a password reset link has been sent.'
            }
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {user.username}")
            return {
                'message': 'If the email address exists, a password reset link has been sent.'
            }
        
        try:
            # Generate reset token
            reset_token = AuthService._generate_secure_token()
            user.set_password_reset_token(reset_token, expires_in_hours=24)
            
            db.session.commit()
            
            logger.info(f"Password reset token generated for user: {user.username}")
            
            return {
                'reset_token': reset_token,
                'expires_in': 24 * 3600,  # 24 hours in seconds
                'message': 'Password reset token generated successfully.'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate password reset token for email {email}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Password reset request failed. Please try again.",
                code="RESET_REQUEST_ERROR",
                status_code=500
            )
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password using reset token.
        
        Args:
            token (str): Password reset token
            new_password (str): New password
            
        Returns:
            Dict[str, Any]: Password reset result
            
        Raises:
            AuthenticationError: If reset fails
        """
        logger.info("Password reset attempt with token")
        
        if not token or not new_password:
            raise AuthenticationError(
                "Reset token and new password are required",
                code="MISSING_REQUIRED_FIELDS",
                status_code=400
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise AuthenticationError(
                "Password must be at least 8 characters long",
                code="WEAK_PASSWORD",
                status_code=400
            )
        
        # Find user with valid reset token
        user = User.query.filter_by(password_reset_token=token).first()
        if not user or not user.is_password_reset_token_valid(token):
            logger.warning("Password reset attempt with invalid or expired token")
            raise AuthenticationError(
                "Invalid or expired reset token",
                code="INVALID_RESET_TOKEN",
                status_code=400
            )
        
        try:
            # Reset password
            user.set_password(new_password)
            user.clear_password_reset_token()
            
            # Clear any account locks
            user.unlock_account()
            
            db.session.commit()
            
            logger.info(f"Password reset successfully for user: {user.username}")
            
            return {
                'message': 'Password reset successfully.'
            }
            
        except Exception as e:
            logger.error(f"Failed to reset password for user {user.username}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Password reset failed. Please try again.",
                code="PASSWORD_RESET_ERROR",
                status_code=500
            )
    
    @staticmethod
    def verify_email(token: str) -> Dict[str, Any]:
        """
        Verify user email address using verification token.
        
        Args:
            token (str): Email verification token
            
        Returns:
            Dict[str, Any]: Verification result
            
        Raises:
            AuthenticationError: If verification fails
        """
        logger.info("Email verification attempt")
        
        if not token:
            raise AuthenticationError(
                "Verification token is required",
                code="MISSING_TOKEN",
                status_code=400
            )
        
        # Find user with verification token
        user = User.query.filter_by(email_verification_token=token).first()
        if not user:
            logger.warning("Email verification attempt with invalid token")
            raise AuthenticationError(
                "Invalid verification token",
                code="INVALID_VERIFICATION_TOKEN",
                status_code=400
            )
        
        if user.is_verified:
            logger.info(f"Email already verified for user: {user.username}")
            return {
                'message': 'Email address is already verified.'
            }
        
        try:
            # Verify email
            user.verify_email()
            db.session.commit()
            
            logger.info(f"Email verified successfully for user: {user.username}")
            
            return {
                'user': user.to_dict(exclude_fields=['password_hash']),
                'message': 'Email verified successfully.'
            }
            
        except Exception as e:
            logger.error(f"Failed to verify email for user {user.username}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Email verification failed. Please try again.",
                code="EMAIL_VERIFICATION_ERROR",
                status_code=500
            )
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password (requires current password).
        
        Args:
            user (User): Current user
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            Dict[str, Any]: Password change result
            
        Raises:
            AuthenticationError: If password change fails
        """
        logger.info(f"Password change request for user: {user.username}")
        
        if not current_password or not new_password:
            raise AuthenticationError(
                "Current password and new password are required",
                code="MISSING_REQUIRED_FIELDS",
                status_code=400
            )
        
        # Verify current password
        if not user.check_password(current_password):
            logger.warning(f"Password change failed - invalid current password for user: {user.username}")
            raise AuthenticationError(
                "Current password is incorrect",
                code="INVALID_CURRENT_PASSWORD",
                status_code=400
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise AuthenticationError(
                "New password must be at least 8 characters long",
                code="WEAK_PASSWORD",
                status_code=400
            )
        
        # Check if new password is different from current
        if user.check_password(new_password):
            raise AuthenticationError(
                "New password must be different from current password",
                code="SAME_PASSWORD",
                status_code=400
            )
        
        try:
            # Change password
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f"Password changed successfully for user: {user.username}")
            
            return {
                'message': 'Password changed successfully.'
            }
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user.username}: {e}")
            db.session.rollback()
            raise AuthenticationError(
                "Password change failed. Please try again.",
                code="PASSWORD_CHANGE_ERROR",
                status_code=500
            )
    
    @staticmethod
    def logout(user: User) -> Dict[str, Any]:
        """
        Logout user (placeholder for token blacklisting if implemented).
        
        Args:
            user (User): Current user
            
        Returns:
            Dict[str, Any]: Logout result
        """
        logger.info(f"User logout: {user.username}")
        
        # In a full implementation, you might want to:
        # - Add token to blacklist
        # - Clear refresh tokens from database
        # - Log logout event
        
        return {
            'message': 'Logged out successfully.'
        }
    
    @staticmethod
    def _find_user_by_login(username_or_email: str) -> Optional[User]:
        """
        Find user by username or email.
        
        Args:
            username_or_email (str): Username or email address
            
        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        # Try to find by email first (contains @)
        if '@' in username_or_email:
            return User.get_by_email(username_or_email)
        else:
            # Try username first, then email as fallback
            user = User.get_by_username(username_or_email)
            if not user:
                user = User.get_by_email(username_or_email)
            return user
    
    @staticmethod
    def _generate_tokens(user: User, remember_me: bool = False) -> Dict[str, Any]:
        """
        Generate JWT access and refresh tokens for user.
        
        Args:
            user (User): User instance
            remember_me (bool): Whether to create longer-lived tokens
            
        Returns:
            Dict[str, Any]: Token information
        """
        # Configure token expiration times
        access_expires = timedelta(
            hours=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)
        )
        
        if remember_me:
            refresh_expires = timedelta(
                days=current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS_REMEMBER', 30)
            )
        else:
            refresh_expires = timedelta(
                days=current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 7)
            )
        
        # Generate tokens
        access_token = create_access_token(
            identity=user,
            expires_delta=access_expires
        )
        
        refresh_token = create_refresh_token(
            identity=user,
            expires_delta=refresh_expires
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(access_expires.total_seconds()),
            'refresh_expires_in': int(refresh_expires.total_seconds())
        }
    
    @staticmethod
    def _generate_secure_token(length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length (int): Token length (default: 32)
            
        Returns:
            str: Secure random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))