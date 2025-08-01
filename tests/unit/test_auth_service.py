"""
Unit tests for authentication service.

This module tests the AuthService class methods in isolation,
focusing on business logic and error handling.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.exceptions import (
    DuplicateResourceError,
    InvalidCredentialsError,
    TokenExpiredError,
    UserNotFoundError,
    ValidationError,
)
from tests.utils import DatabaseTestHelper, ValidationTestHelper


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.auth
class TestAuthService:
    """Test cases for AuthService."""

    def test_validate_login_data_success(self):
        """Test successful login data validation."""
        valid_data = {"username_or_email": "testuser", "password": "testpassword123"}

        # Should not raise any exception
        AuthService._validate_login_data(valid_data)

    def test_validate_login_data_missing_fields(self):
        """Test login data validation with missing fields."""
        invalid_data = {"username_or_email": "", "password": ""}

        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_login_data(invalid_data)

        error = exc_info.value
        assert error.error_code == "VALIDATION_ERROR"
        assert "field_errors" in error.details
        assert "username_or_email" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]

    def test_validate_registration_data_success(self):
        """Test successful registration data validation."""
        valid_data = ValidationTestHelper.get_valid_user_data()

        # Should not raise any exception
        AuthService._validate_registration_data(valid_data)

    def test_validate_registration_data_missing_fields(self):
        """Test registration data validation with missing fields."""
        invalid_data = {
            "username": "testuser"
            # Missing email and password
        }

        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_registration_data(invalid_data)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "email" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]

    def test_validate_registration_data_field_lengths(self):
        """Test registration data validation with invalid field lengths."""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "123",  # Too short
        }

        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_registration_data(invalid_data)

        error = exc_info.value
        assert "username" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]

    def test_validate_registration_data_invalid_email(self):
        """Test registration data validation with invalid email."""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpassword123",
        }

        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_registration_data(invalid_data)

        error = exc_info.value
        assert "email" in error.details["field_errors"]

    @patch("app.services.auth_service.User")
    def test_find_user_by_username_or_email_by_username(self, mock_user_model):
        """Test finding user by username."""
        mock_user = MagicMock()
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user

        result = AuthService._find_user_by_username_or_email("testuser")

        assert result == mock_user
        mock_user_model.query.filter_by.assert_called_once_with(username="testuser")

    @patch("app.services.auth_service.User")
    def test_find_user_by_username_or_email_by_email(self, mock_user_model):
        """Test finding user by email."""
        mock_user = MagicMock()
        mock_user_model.query.filter_by.return_value.first.side_effect = [
            None,
            mock_user,
        ]

        result = AuthService._find_user_by_username_or_email("test@example.com")

        assert result == mock_user
        assert mock_user_model.query.filter_by.call_count == 2

    @patch("app.services.auth_service.User")
    def test_find_user_by_username_or_email_not_found(self, mock_user_model):
        """Test finding user when user doesn't exist."""
        mock_user_model.query.filter_by.return_value.first.return_value = None

        result = AuthService._find_user_by_username_or_email("nonexistent")

        assert result is None

    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.create_refresh_token")
    def test_generate_tokens(self, mock_refresh_token, mock_access_token):
        """Test token generation."""
        mock_access_token.return_value = "access_token"
        mock_refresh_token.return_value = "refresh_token"

        user = MagicMock()
        user.id = 1

        tokens = AuthService._generate_tokens(user)

        assert tokens["access_token"] == "access_token"
        assert tokens["refresh_token"] == "refresh_token"
        mock_access_token.assert_called_once_with(identity=1)
        mock_refresh_token.assert_called_once_with(identity=1)

    @patch("app.services.auth_service.AuthService._validate_login_data")
    @patch("app.services.auth_service.AuthService._find_user_by_username_or_email")
    @patch("app.services.auth_service.AuthService._generate_tokens")
    def test_login_success(self, mock_generate_tokens, mock_find_user, mock_validate):
        """Test successful user login."""
        # Setup mocks
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.check_password.return_value = True

        mock_find_user.return_value = mock_user
        mock_generate_tokens.return_value = {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
        }

        login_data = {"username_or_email": "testuser", "password": "testpassword123"}

        result = AuthService.login(
            login_data["username_or_email"], login_data["password"]
        )

        # Assertions
        mock_validate.assert_called_once()
        mock_find_user.assert_called_once_with("testuser")
        mock_user.check_password.assert_called_once_with("testpassword123")
        mock_generate_tokens.assert_called_once_with(mock_user)

        assert result["user"]["id"] == 1
        assert result["user"]["username"] == "testuser"
        assert result["tokens"]["access_token"] == "access_token"
        assert result["tokens"]["refresh_token"] == "refresh_token"

    @patch("app.services.auth_service.AuthService._validate_login_data")
    @patch("app.services.auth_service.AuthService._find_user_by_username_or_email")
    def test_login_user_not_found(self, mock_find_user, mock_validate):
        """Test login with non-existent user."""
        mock_find_user.return_value = None

        with pytest.raises(InvalidCredentialsError):
            AuthService.login("nonexistent", "password")

    @patch("app.services.auth_service.AuthService._validate_login_data")
    @patch("app.services.auth_service.AuthService._find_user_by_username_or_email")
    def test_login_invalid_password(self, mock_find_user, mock_validate):
        """Test login with invalid password."""
        mock_user = MagicMock()
        mock_user.check_password.return_value = False
        mock_find_user.return_value = mock_user

        with pytest.raises(InvalidCredentialsError):
            AuthService.login("testuser", "wrongpassword")

    @patch("app.services.auth_service.AuthService._validate_login_data")
    @patch("app.services.auth_service.AuthService._find_user_by_username_or_email")
    def test_login_inactive_user(self, mock_find_user, mock_validate):
        """Test login with inactive user."""
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user.check_password.return_value = True
        mock_find_user.return_value = mock_user

        with pytest.raises(InvalidCredentialsError) as exc_info:
            AuthService.login("testuser", "password")

        assert "inactive" in str(exc_info.value.message).lower()

    @patch("app.services.auth_service.AuthService._validate_registration_data")
    @patch("app.services.auth_service.User")
    @patch("app.services.auth_service.db")
    def test_register_success(self, mock_db, mock_user_model, mock_validate):
        """Test successful user registration."""
        # Setup mocks
        mock_user_model.query.filter.return_value.first.return_value = None
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.username = "testuser"
        mock_user_instance.email = "test@example.com"
        mock_user_model.return_value = mock_user_instance

        registration_data = ValidationTestHelper.get_valid_user_data()

        result = AuthService.register(
            registration_data["username"],
            registration_data["email"],
            registration_data["password"],
        )

        # Assertions
        mock_validate.assert_called_once()
        mock_user_model.assert_called_once()
        mock_user_instance.set_password.assert_called_once_with("testpassword123")
        mock_db.session.add.assert_called_once_with(mock_user_instance)
        mock_db.session.commit.assert_called_once()

        assert result["id"] == 1
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"

    @patch("app.services.auth_service.AuthService._validate_registration_data")
    @patch("app.services.auth_service.User")
    def test_register_duplicate_username(self, mock_user_model, mock_validate):
        """Test registration with duplicate username."""
        mock_user_model.query.filter.return_value.first.return_value = MagicMock()

        with pytest.raises(DuplicateResourceError) as exc_info:
            AuthService.register("existinguser", "new@example.com", "password123")

        error = exc_info.value
        assert error.details["resource_type"] == "User"
        assert error.details["field"] == "username"

    @patch("app.services.auth_service.AuthService._validate_registration_data")
    @patch("app.services.auth_service.User")
    def test_register_duplicate_email(self, mock_user_model, mock_validate):
        """Test registration with duplicate email."""
        # First call returns None (username check), second returns user (email check)
        mock_user_model.query.filter.return_value.first.side_effect = [
            None,
            MagicMock(),
        ]

        with pytest.raises(DuplicateResourceError) as exc_info:
            AuthService.register("newuser", "existing@example.com", "password123")

        error = exc_info.value
        assert error.details["resource_type"] == "User"
        assert error.details["field"] == "email"

    @patch("app.services.auth_service.get_jwt_identity")
    @patch("app.services.auth_service.User")
    @patch("app.services.auth_service.create_access_token")
    def test_refresh_token_success(
        self, mock_create_token, mock_user_model, mock_get_identity
    ):
        """Test successful token refresh."""
        mock_get_identity.return_value = 1
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user_model.query.get.return_value = mock_user
        mock_create_token.return_value = "new_access_token"

        result = AuthService.refresh_token()

        assert result["access_token"] == "new_access_token"
        mock_create_token.assert_called_once_with(identity=1)

    @patch("app.services.auth_service.get_jwt_identity")
    @patch("app.services.auth_service.User")
    def test_refresh_token_user_not_found(self, mock_user_model, mock_get_identity):
        """Test token refresh with non-existent user."""
        mock_get_identity.return_value = 999
        mock_user_model.query.get.return_value = None

        with pytest.raises(UserNotFoundError):
            AuthService.refresh_token()

    @patch("app.services.auth_service.get_jwt_identity")
    @patch("app.services.auth_service.User")
    def test_refresh_token_inactive_user(self, mock_user_model, mock_get_identity):
        """Test token refresh with inactive user."""
        mock_get_identity.return_value = 1
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user_model.query.get.return_value = mock_user

        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_token()

    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password."""
        valid_passwords = [
            "testpassword123",
            "MySecurePass1",
            "another_valid_password123",
        ]

        for password in valid_passwords:
            # Should not raise any exception
            AuthService._validate_password_strength(password)

    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password."""
        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_password_strength("123")

        error = exc_info.value
        assert "password" in error.details["field_errors"]
        assert "at least" in error.details["field_errors"]["password"]

    def test_validate_password_strength_too_long(self):
        """Test password strength validation with long password."""
        long_password = "a" * 129

        with pytest.raises(ValidationError) as exc_info:
            AuthService._validate_password_strength(long_password)

        error = exc_info.value
        assert "password" in error.details["field_errors"]
        assert "no more than" in error.details["field_errors"]["password"]

    @patch("app.services.auth_service.AuthService._validate_login_data")
    def test_login_validation_error_propagation(self, mock_validate):
        """Test that validation errors are properly propagated."""
        mock_validate.side_effect = ValidationError(
            "Validation failed", field_errors={"username_or_email": "Required field"}
        )

        with pytest.raises(ValidationError) as exc_info:
            AuthService.login("", "password")

        error = exc_info.value
        assert "field_errors" in error.details
        assert "username_or_email" in error.details["field_errors"]

    @patch("app.services.auth_service.AuthService._validate_registration_data")
    def test_register_validation_error_propagation(self, mock_validate):
        """Test that registration validation errors are properly propagated."""
        mock_validate.side_effect = ValidationError(
            "Validation failed", field_errors={"email": "Invalid format"}
        )

        with pytest.raises(ValidationError) as exc_info:
            AuthService.register("user", "invalid-email", "password")

        error = exc_info.value
        assert "field_errors" in error.details
        assert "email" in error.details["field_errors"]
