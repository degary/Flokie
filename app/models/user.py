"""
User model module for Flask API Template.

This module provides the User model class that handles user data,
authentication, and user state management functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from .base import BaseModel, ValidationMixin

logger = logging.getLogger(__name__)


class User(BaseModel, ValidationMixin):
    """
    User model for handling user authentication and profile data.

    This model extends BaseModel and includes:
    - User authentication fields (username, email, password)
    - User state management (is_active, is_verified, etc.)
    - Password hashing and verification methods
    - User profile information
    """

    # User identification fields
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # User profile fields
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)

    # User state management fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Authentication tracking fields
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(String(10), default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Email verification fields
    email_verified_at = Column(DateTime, nullable=True)
    email_verification_token = Column(String(255), nullable=True)

    # Password reset fields
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        """
        Initialize User instance.

        Args:
            **kwargs: User field values
        """
        # Handle password separately to ensure it gets hashed
        password = kwargs.pop("password", None)

        # Set default values for fields that have defaults
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "is_verified" not in kwargs:
            kwargs["is_verified"] = False
        if "is_admin" not in kwargs:
            kwargs["is_admin"] = False
        if "failed_login_attempts" not in kwargs:
            kwargs["failed_login_attempts"] = "0"

        super().__init__(**kwargs)

        if password:
            self.set_password(password)

    def __repr__(self):
        """
        String representation of the User instance.

        Returns:
            str: String representation showing username and id
        """
        return f"<User(id={self.id}, username='{self.username}')>"

    def set_password(self, password: str) -> None:
        """
        Hash and set user password.

        Args:
            password (str): Plain text password to hash and store

        Raises:
            ValueError: If password is invalid
        """
        if not password or len(password.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long")

        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        logger.info(f"Password updated for user {self.username}")

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password (str): Plain text password to verify

        Returns:
            bool: True if password is correct, False otherwise
        """
        if not password or not self.password_hash:
            return False

        is_valid = check_password_hash(self.password_hash, password)

        if is_valid:
            # Reset failed login attempts on successful login
            self.failed_login_attempts = "0"
            self.last_login_at = datetime.utcnow()
            self.locked_until = None
            logger.info(f"Successful login for user {self.username}")
        else:
            # Increment failed login attempts
            current_attempts = int(self.failed_login_attempts or "0")
            self.failed_login_attempts = str(current_attempts + 1)

            # Lock account after 5 failed attempts for 30 minutes
            if current_attempts + 1 >= 5:
                from datetime import timedelta

                self.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(
                    f"Account locked for user {self.username} due to failed login attempts"
                )
            else:
                logger.warning(
                    f"Failed login attempt for user {self.username} (attempt {current_attempts + 1})"
                )

        return is_valid

    def is_account_locked(self) -> bool:
        """
        Check if user account is currently locked.

        Returns:
            bool: True if account is locked, False otherwise
        """
        if not self.locked_until:
            return False

        if datetime.utcnow() > self.locked_until:
            # Lock has expired, clear it
            self.locked_until = None
            self.failed_login_attempts = "0"
            return False

        return True

    def unlock_account(self) -> None:
        """
        Manually unlock user account and reset failed login attempts.
        """
        self.locked_until = None
        self.failed_login_attempts = "0"
        logger.info(f"Account manually unlocked for user {self.username}")

    def activate(self) -> None:
        """
        Activate user account.
        """
        self.is_active = True
        logger.info(f"Account activated for user {self.username}")

    def deactivate(self) -> None:
        """
        Deactivate user account.
        """
        self.is_active = False
        logger.info(f"Account deactivated for user {self.username}")

    def verify_email(self) -> None:
        """
        Mark user email as verified.
        """
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
        self.email_verification_token = None
        logger.info(f"Email verified for user {self.username}")

    def set_email_verification_token(self, token: str) -> None:
        """
        Set email verification token.

        Args:
            token (str): Email verification token
        """
        self.email_verification_token = token
        logger.info(f"Email verification token set for user {self.username}")

    def set_password_reset_token(self, token: str, expires_in_hours: int = 24) -> None:
        """
        Set password reset token with expiration.

        Args:
            token (str): Password reset token
            expires_in_hours (int): Token expiration time in hours (default: 24)
        """
        from datetime import timedelta

        self.password_reset_token = token
        self.password_reset_expires_at = datetime.utcnow() + timedelta(
            hours=expires_in_hours
        )
        logger.info(f"Password reset token set for user {self.username}")

    def clear_password_reset_token(self) -> None:
        """
        Clear password reset token and expiration.
        """
        self.password_reset_token = None
        self.password_reset_expires_at = None
        logger.info(f"Password reset token cleared for user {self.username}")

    def is_password_reset_token_valid(self, token: str) -> bool:
        """
        Check if password reset token is valid and not expired.

        Args:
            token (str): Token to validate

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.password_reset_token or not self.password_reset_expires_at:
            return False

        if self.password_reset_token != token:
            return False

        if datetime.utcnow() > self.password_reset_expires_at:
            # Token has expired, clear it
            self.clear_password_reset_token()
            return False

        return True

    def get_full_name(self) -> str:
        """
        Get user's full name.

        Returns:
            str: Full name or username if names are not set
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def get_display_name(self) -> str:
        """
        Get user's display name for UI purposes.

        Returns:
            str: Display name (full name or username)
        """
        full_name = self.get_full_name()
        return full_name if full_name != self.username else f"@{self.username}"

    def to_dict(
        self, include_relationships: bool = False, exclude_fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Convert User instance to dictionary, excluding sensitive fields by default.

        Args:
            include_relationships (bool): Whether to include relationship data
            exclude_fields (list, optional): Additional fields to exclude

        Returns:
            Dict[str, Any]: Dictionary representation of the user
        """
        # Always exclude sensitive fields
        default_exclude = [
            "password_hash",
            "email_verification_token",
            "password_reset_token",
            "failed_login_attempts",
        ]

        if exclude_fields:
            default_exclude.extend(exclude_fields)

        user_dict = super().to_dict(
            include_relationships=include_relationships, exclude_fields=default_exclude
        )

        # Add computed fields
        user_dict["full_name"] = self.get_full_name()
        user_dict["display_name"] = self.get_display_name()
        user_dict["is_locked"] = self.is_account_locked()

        return user_dict

    def to_public_dict(self) -> Dict[str, Any]:
        """
        Convert User instance to public dictionary with minimal information.

        Returns:
            Dict[str, Any]: Public dictionary representation
        """
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.get_display_name(),
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def _validate_custom(self) -> None:
        """
        Custom validation logic for User model.

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        self.validate_required_fields(["username", "email"])

        # Validate field lengths
        self.validate_field_length("username", min_length=3, max_length=80)
        self.validate_field_length("first_name", max_length=50)
        self.validate_field_length("last_name", max_length=50)

        # Validate email format
        self.validate_email_format("email")

        # Validate username format (alphanumeric and underscores only)
        import re

        if not re.match(r"^[a-zA-Z0-9_]+$", self.username):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )

        # Validate unique fields (only for new records or when fields change)
        if not self.id:  # New record
            self.validate_unique_field("username")
            self.validate_unique_field("email")
        else:  # Existing record - check if fields changed
            original = User.get_by_id(self.id)
            if original:
                if original.username != self.username:
                    self.validate_unique_field("username", exclude_id=self.id)
                if original.email != self.email:
                    self.validate_unique_field("email", exclude_id=self.id)

    @validates("email")
    def validate_email(self, key, email):
        """
        SQLAlchemy validator for email field.

        Args:
            key (str): Field name
            email (str): Email value to validate

        Returns:
            str: Validated email (converted to lowercase)
        """
        if email:
            return email.lower().strip()
        return email

    @validates("username")
    def validate_username(self, key, username):
        """
        SQLAlchemy validator for username field.

        Args:
            key (str): Field name
            username (str): Username value to validate

        Returns:
            str: Validated username (converted to lowercase)
        """
        if username:
            return username.lower().strip()
        return username

    @classmethod
    def get_by_id(cls, user_id: int):
        """
        Get user by ID.

        Args:
            user_id (int): User ID to search for

        Returns:
            User or None: User instance if found, None otherwise
        """
        try:
            return cls.query.get(user_id)
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    @classmethod
    def get_by_username(cls, username: str):
        """
        Get user by username.

        Args:
            username (str): Username to search for

        Returns:
            User or None: User instance if found, None otherwise
        """
        try:
            return cls.query.filter_by(username=username.lower().strip()).first()
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None

    @classmethod
    def get_by_email(cls, email: str):
        """
        Get user by email address.

        Args:
            email (str): Email address to search for

        Returns:
            User or None: User instance if found, None otherwise
        """
        try:
            return cls.query.filter_by(email=email.lower().strip()).first()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    @classmethod
    def get_active_users(
        cls, limit: Optional[int] = None, offset: Optional[int] = None
    ):
        """
        Get all active users.

        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip

        Returns:
            List[User]: List of active user instances
        """
        try:
            query = cls.query.filter_by(is_active=True)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []

    @classmethod
    def get_verified_users(
        cls, limit: Optional[int] = None, offset: Optional[int] = None
    ):
        """
        Get all verified users.

        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip

        Returns:
            List[User]: List of verified user instances
        """
        try:
            query = cls.query.filter_by(is_verified=True)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get verified users: {e}")
            return []

    @classmethod
    def search_users(cls, search_term: str, limit: Optional[int] = None):
        """
        Search users by username, email, or name.

        Args:
            search_term (str): Term to search for
            limit (int, optional): Maximum number of results to return

        Returns:
            List[User]: List of matching user instances
        """
        try:
            search_pattern = f"%{search_term.lower()}%"
            query = cls.query.filter(
                (cls.username.ilike(search_pattern))
                | (cls.email.ilike(search_pattern))
                | (cls.first_name.ilike(search_pattern))
                | (cls.last_name.ilike(search_pattern))
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        except Exception as e:
            logger.error(f"Failed to search users with term '{search_term}': {e}")
            return []
