"""
Unit tests for user service.

This module tests the UserService class methods in isolation,
focusing on business logic and error handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User
from app.services.user_service import UserService
from app.utils.exceptions import (
    AuthorizationError,
    DuplicateResourceError,
    UserNotFoundError,
    ValidationError,
)
from tests.utils import ValidationTestHelper


@pytest.mark.unit
@pytest.mark.service
class TestUserService:
    """Test cases for UserService."""

    @patch("app.services.user_service.User")
    def test_get_user_by_id_success(self, mock_user_model):
        """Test successful user retrieval by ID."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user_model.query.get.return_value = mock_user

        result = UserService.get_user_by_id(1)

        assert result == mock_user
        mock_user_model.query.get.assert_called_once_with(1)

    @patch("app.services.user_service.User")
    def test_get_user_by_id_not_found(self, mock_user_model):
        """Test user retrieval by ID when user doesn't exist."""
        mock_user_model.query.get.return_value = None

        with pytest.raises(UserNotFoundError) as exc_info:
            UserService.get_user_by_id(999)

        error = exc_info.value
        assert error.details["user_id"] == "999"

    @patch("app.services.user_service.User")
    def test_get_user_by_username_success(self, mock_user_model):
        """Test successful user retrieval by username."""
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user

        result = UserService.get_user_by_username("testuser")

        assert result == mock_user
        mock_user_model.query.filter_by.assert_called_once_with(username="testuser")

    @patch("app.services.user_service.User")
    def test_get_user_by_username_not_found(self, mock_user_model):
        """Test user retrieval by username when user doesn't exist."""
        mock_user_model.query.filter_by.return_value.first.return_value = None

        result = UserService.get_user_by_username("nonexistent")

        assert result is None

    @patch("app.services.user_service.User")
    def test_get_user_by_email_success(self, mock_user_model):
        """Test successful user retrieval by email."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user

        result = UserService.get_user_by_email("test@example.com")

        assert result == mock_user
        mock_user_model.query.filter_by.assert_called_once_with(
            email="test@example.com"
        )

    @patch("app.services.user_service.User")
    def test_get_user_by_email_not_found(self, mock_user_model):
        """Test user retrieval by email when user doesn't exist."""
        mock_user_model.query.filter_by.return_value.first.return_value = None

        result = UserService.get_user_by_email("nonexistent@example.com")

        assert result is None

    @patch("app.services.user_service.User")
    def test_get_all_users_success(self, mock_user_model):
        """Test successful retrieval of all users."""
        mock_users = [MagicMock(), MagicMock(), MagicMock()]
        mock_user_model.query.all.return_value = mock_users

        result = UserService.get_all_users()

        assert result == mock_users
        mock_user_model.query.all.assert_called_once()

    @patch("app.services.user_service.User")
    def test_get_all_users_empty(self, mock_user_model):
        """Test retrieval of all users when no users exist."""
        mock_user_model.query.all.return_value = []

        result = UserService.get_all_users()

        assert result == []

    @patch("app.services.user_service.User")
    def test_get_active_users(self, mock_user_model):
        """Test retrieval of active users only."""
        mock_users = [MagicMock(), MagicMock()]
        mock_user_model.query.filter_by.return_value.all.return_value = mock_users

        result = UserService.get_active_users()

        assert result == mock_users
        mock_user_model.query.filter_by.assert_called_once_with(is_active=True)

    def test_validate_user_update_data_success(self):
        """Test successful user update data validation."""
        valid_data = {"email": "newemail@example.com", "is_active": True}

        # Should not raise any exception
        UserService._validate_user_update_data(valid_data)

    def test_validate_user_update_data_invalid_email(self):
        """Test user update data validation with invalid email."""
        invalid_data = {"email": "invalid-email"}

        with pytest.raises(ValidationError) as exc_info:
            UserService._validate_user_update_data(invalid_data)

        error = exc_info.value
        assert "email" in error.details["field_errors"]

    def test_validate_user_update_data_empty_data(self):
        """Test user update data validation with empty data."""
        # Empty data should be valid (no updates)
        UserService._validate_user_update_data({})

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserService._validate_user_update_data")
    @patch("app.services.user_service.db")
    def test_update_user_success(self, mock_db, mock_validate, mock_get_user):
        """Test successful user update."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "old@example.com"
        mock_get_user.return_value = mock_user

        update_data = {"email": "new@example.com", "is_active": False}

        result = UserService.update_user(1, update_data)

        mock_validate.assert_called_once_with(update_data)
        mock_get_user.assert_called_once_with(1)
        assert mock_user.email == "new@example.com"
        assert mock_user.is_active == False
        mock_db.session.commit.assert_called_once()
        assert result == mock_user

    @patch("app.services.user_service.UserService.get_user_by_id")
    def test_update_user_not_found(self, mock_get_user):
        """Test user update when user doesn't exist."""
        mock_get_user.side_effect = UserNotFoundError(user_id="999")

        with pytest.raises(UserNotFoundError):
            UserService.update_user(999, {"email": "new@example.com"})

    @patch("app.services.user_service.UserService._validate_user_update_data")
    def test_update_user_validation_error(self, mock_validate):
        """Test user update with validation error."""
        mock_validate.side_effect = ValidationError(
            "Validation failed", field_errors={"email": "Invalid format"}
        )

        with pytest.raises(ValidationError):
            UserService.update_user(1, {"email": "invalid-email"})

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.User")
    def test_update_user_duplicate_email(self, mock_user_model, mock_get_user):
        """Test user update with duplicate email."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_get_user.return_value = mock_user

        # Mock existing user with same email
        mock_existing_user = MagicMock()
        mock_existing_user.id = 2
        mock_user_model.query.filter_by.return_value.first.return_value = (
            mock_existing_user
        )

        with pytest.raises(DuplicateResourceError) as exc_info:
            UserService.update_user(1, {"email": "existing@example.com"})

        error = exc_info.value
        assert error.details["resource_type"] == "User"
        assert error.details["field"] == "email"

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.db")
    def test_delete_user_success(self, mock_db, mock_get_user):
        """Test successful user deletion."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_get_user.return_value = mock_user

        result = UserService.delete_user(1)

        mock_get_user.assert_called_once_with(1)
        mock_db.session.delete.assert_called_once_with(mock_user)
        mock_db.session.commit.assert_called_once()
        assert result is True

    @patch("app.services.user_service.UserService.get_user_by_id")
    def test_delete_user_not_found(self, mock_get_user):
        """Test user deletion when user doesn't exist."""
        mock_get_user.side_effect = UserNotFoundError(user_id="999")

        with pytest.raises(UserNotFoundError):
            UserService.delete_user(999)

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.db")
    def test_deactivate_user_success(self, mock_db, mock_get_user):
        """Test successful user deactivation."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_get_user.return_value = mock_user

        result = UserService.deactivate_user(1)

        mock_get_user.assert_called_once_with(1)
        assert mock_user.is_active == False
        mock_db.session.commit.assert_called_once()
        assert result == mock_user

    @patch("app.services.user_service.UserService.get_user_by_id")
    def test_deactivate_user_not_found(self, mock_get_user):
        """Test user deactivation when user doesn't exist."""
        mock_get_user.side_effect = UserNotFoundError(user_id="999")

        with pytest.raises(UserNotFoundError):
            UserService.deactivate_user(999)

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.db")
    def test_activate_user_success(self, mock_db, mock_get_user):
        """Test successful user activation."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = False
        mock_get_user.return_value = mock_user

        result = UserService.activate_user(1)

        mock_get_user.assert_called_once_with(1)
        assert mock_user.is_active == True
        mock_db.session.commit.assert_called_once()
        assert result == mock_user

    def test_validate_password_change_data_success(self):
        """Test successful password change data validation."""
        valid_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        # Should not raise any exception
        UserService._validate_password_change_data(valid_data)

    def test_validate_password_change_data_missing_fields(self):
        """Test password change data validation with missing fields."""
        invalid_data = {
            "current_password": "oldpassword123"
            # Missing new_password and confirm_password
        }

        with pytest.raises(ValidationError) as exc_info:
            UserService._validate_password_change_data(invalid_data)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "new_password" in error.details["field_errors"]
        assert "confirm_password" in error.details["field_errors"]

    def test_validate_password_change_data_password_mismatch(self):
        """Test password change data validation with password mismatch."""
        invalid_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserService._validate_password_change_data(invalid_data)

        error = exc_info.value
        assert "confirm_password" in error.details["field_errors"]
        assert "match" in error.details["field_errors"]["confirm_password"]

    def test_validate_password_change_data_weak_password(self):
        """Test password change data validation with weak password."""
        invalid_data = {
            "current_password": "oldpassword123",
            "new_password": "123",  # Too short
            "confirm_password": "123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserService._validate_password_change_data(invalid_data)

        error = exc_info.value
        assert "new_password" in error.details["field_errors"]

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserService._validate_password_change_data")
    @patch("app.services.user_service.db")
    def test_change_password_success(self, mock_db, mock_validate, mock_get_user):
        """Test successful password change."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.check_password.return_value = True
        mock_get_user.return_value = mock_user

        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        result = UserService.change_password(1, password_data)

        mock_validate.assert_called_once_with(password_data)
        mock_get_user.assert_called_once_with(1)
        mock_user.check_password.assert_called_once_with("oldpassword123")
        mock_user.set_password.assert_called_once_with("newpassword123")
        mock_db.session.commit.assert_called_once()
        assert result is True

    @patch("app.services.user_service.UserService.get_user_by_id")
    @patch("app.services.user_service.UserService._validate_password_change_data")
    def test_change_password_wrong_current_password(self, mock_validate, mock_get_user):
        """Test password change with wrong current password."""
        mock_user = MagicMock()
        mock_user.check_password.return_value = False
        mock_get_user.return_value = mock_user

        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserService.change_password(1, password_data)

        error = exc_info.value
        assert "current_password" in error.details["field_errors"]

    @patch("app.services.user_service.User")
    def test_search_users_by_username(self, mock_user_model):
        """Test user search by username."""
        mock_users = [MagicMock(), MagicMock()]
        mock_user_model.query.filter.return_value.all.return_value = mock_users

        result = UserService.search_users("test")

        assert result == mock_users
        # Verify that filter was called with username LIKE pattern
        mock_user_model.query.filter.assert_called_once()

    @patch("app.services.user_service.User")
    def test_search_users_no_results(self, mock_user_model):
        """Test user search with no results."""
        mock_user_model.query.filter.return_value.all.return_value = []

        result = UserService.search_users("nonexistent")

        assert result == []

    def test_can_user_modify_user_same_user(self):
        """Test user modification permission for same user."""
        result = UserService.can_user_modify_user(1, 1)
        assert result is True

    def test_can_user_modify_user_different_user(self):
        """Test user modification permission for different user."""
        # For now, users can only modify themselves
        result = UserService.can_user_modify_user(1, 2)
        assert result is False

    @patch("app.services.user_service.UserService.can_user_modify_user")
    def test_check_user_modification_permission_allowed(self, mock_can_modify):
        """Test user modification permission check when allowed."""
        mock_can_modify.return_value = True

        # Should not raise any exception
        UserService.check_user_modification_permission(1, 1)

    @patch("app.services.user_service.UserService.can_user_modify_user")
    def test_check_user_modification_permission_denied(self, mock_can_modify):
        """Test user modification permission check when denied."""
        mock_can_modify.return_value = False

        with pytest.raises(AuthorizationError):
            UserService.check_user_modification_permission(1, 2)
