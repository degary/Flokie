"""
Unit tests for User model.

This module tests the User model class methods and properties,
focusing on data validation, password handling, and serialization.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from app.extensions import db
from app.models.user import User


@pytest.mark.unit
@pytest.mark.model
@pytest.mark.database
class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, app):
        """Test basic user creation."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")

            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.is_active is True  # Default value
            assert user.password_hash is None
            assert isinstance(user.created_at, datetime)
            assert isinstance(user.updated_at, datetime)

    def test_user_creation_with_optional_fields(self, app):
        """Test user creation with optional fields."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com", is_active=False)
            user.set_password("testpassword123")

            assert user.is_active is False

    def test_set_password(self, app):
        """Test password setting and hashing."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")

            assert user.password_hash is not None
            assert user.password_hash != "testpassword123"  # Should be hashed
            assert len(user.password_hash) > 20  # Hashed password should be longer

    def test_check_password_correct(self, app):
        """Test password verification with correct password."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")

            assert user.check_password("testpassword123") is True

    def test_check_password_incorrect(self, app):
        """Test password verification with incorrect password."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")

            assert user.check_password("wrongpassword") is False

    def test_check_password_no_password_set(self, app):
        """Test password verification when no password is set."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            assert user.check_password("anypassword") is False

    def test_to_dict_basic(self, app):
        """Test basic dictionary serialization."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.id = 1  # Simulate database ID

            result = user.to_dict()

            assert result["id"] == 1
            assert result["username"] == "testuser"
            assert result["email"] == "test@example.com"
            assert result["is_active"] is True
            assert "created_at" in result
            assert "updated_at" in result

            # Sensitive fields should not be included
            assert "password_hash" not in result

    def test_to_dict_include_timestamps(self, app):
        """Test dictionary serialization with timestamps."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.id = 1

            result = user.to_dict(include_timestamps=True)

            assert "created_at" in result
            assert "updated_at" in result
            assert isinstance(result["created_at"], str)  # Should be ISO format
            assert isinstance(result["updated_at"], str)

    def test_to_dict_exclude_timestamps(self, app):
        """Test dictionary serialization without timestamps."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.id = 1

            result = user.to_dict(include_timestamps=False)

            assert "created_at" not in result
            assert "updated_at" not in result

    def test_from_dict_basic(self, app):
        """Test user creation from dictionary."""
        with app.app_context():
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "is_active": False,
            }

            user = User.from_dict(user_data)

            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.is_active is False

    def test_from_dict_with_password(self, app):
        """Test user creation from dictionary with password."""
        with app.app_context():
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
            }

            user = User.from_dict(user_data)

            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.password_hash is not None
            assert user.check_password("testpassword123") is True

    def test_from_dict_ignore_sensitive_fields(self, app):
        """Test that sensitive fields are ignored in from_dict."""
        with app.app_context():
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "should_be_ignored",
                "id": 999,  # Should be ignored
                "created_at": "2023-01-01T00:00:00",  # Should be ignored
                "updated_at": "2023-01-01T00:00:00",  # Should be ignored
            }

            user = User.from_dict(user_data)

            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.password_hash != "should_be_ignored"
            assert user.id is None  # Not set from dict
            assert isinstance(user.created_at, datetime)  # Auto-generated

    def test_repr(self, app):
        """Test string representation of user."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.id = 1

            repr_str = repr(user)

            assert "User" in repr_str
            assert "testuser" in repr_str
            assert "1" in repr_str

    def test_str(self, app):
        """Test string conversion of user."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            str_repr = str(user)

            assert "testuser" in str_repr

    def test_username_validation_length(self, app):
        """Test username length validation."""
        with app.app_context():
            # Test minimum length
            user = User(username="ab", email="test@example.com")
            with pytest.raises(Exception):  # Should raise validation error
                db.session.add(user)
                db.session.commit()

    def test_email_validation_format(self, app):
        """Test email format validation."""
        with app.app_context():
            user = User(username="testuser", email="invalid-email")
            with pytest.raises(Exception):  # Should raise validation error
                db.session.add(user)
                db.session.commit()

    def test_unique_username_constraint(self, app):
        """Test username uniqueness constraint."""
        with app.app_context():
            user1 = User(username="testuser", email="test1@example.com")
            user2 = User(username="testuser", email="test2@example.com")

            db.session.add(user1)
            db.session.commit()

            db.session.add(user2)
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()

    def test_unique_email_constraint(self, app):
        """Test email uniqueness constraint."""
        with app.app_context():
            user1 = User(username="testuser1", email="test@example.com")
            user2 = User(username="testuser2", email="test@example.com")

            db.session.add(user1)
            db.session.commit()

            db.session.add(user2)
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()

    def test_password_hashing_different_passwords(self, app):
        """Test that different passwords produce different hashes."""
        with app.app_context():
            user1 = User(username="testuser1", email="test1@example.com")
            user2 = User(username="testuser2", email="test2@example.com")

            user1.set_password("password123")
            user2.set_password("differentpassword")

            assert user1.password_hash != user2.password_hash

    def test_password_hashing_same_password(self, app):
        """Test that same password produces different hashes (salt)."""
        with app.app_context():
            user1 = User(username="testuser1", email="test1@example.com")
            user2 = User(username="testuser2", email="test2@example.com")

            user1.set_password("samepassword")
            user2.set_password("samepassword")

            # Should be different due to salt
            assert user1.password_hash != user2.password_hash

            # But both should verify correctly
            assert user1.check_password("samepassword") is True
            assert user2.check_password("samepassword") is True

    def test_updated_at_changes_on_modification(self, app):
        """Test that updated_at changes when user is modified."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")
            db.session.add(user)
            db.session.commit()

            original_updated_at = user.updated_at

            # Simulate time passing
            import time

            time.sleep(0.01)

            # Modify user
            user.email = "newemail@example.com"
            db.session.commit()

            assert user.updated_at > original_updated_at

    def test_is_active_default_true(self, app):
        """Test that is_active defaults to True."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            assert user.is_active is True

    def test_user_equality(self, app):
        """Test user equality comparison."""
        with app.app_context():
            user1 = User(username="testuser", email="test@example.com")
            user1.id = 1

            user2 = User(username="testuser", email="test@example.com")
            user2.id = 1

            user3 = User(username="testuser", email="test@example.com")
            user3.id = 2

            assert user1 == user2  # Same ID
            assert user1 != user3  # Different ID

    def test_user_hash(self, app):
        """Test user hash for use in sets/dicts."""
        with app.app_context():
            user1 = User(username="testuser", email="test@example.com")
            user1.id = 1

            user2 = User(username="testuser", email="test@example.com")
            user2.id = 1

            # Should have same hash if same ID
            assert hash(user1) == hash(user2)

            # Should be usable in sets
            user_set = {user1, user2}
            assert len(user_set) == 1  # Only one unique user

    @patch("app.models.user.datetime")
    def test_timestamps_use_utc(self, mock_datetime, app):
        """Test that timestamps use UTC."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            mock_datetime.utcnow.assert_called()

    def test_to_dict_serialization_types(self, app):
        """Test that to_dict returns JSON-serializable types."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.id = 1

            result = user.to_dict()

            # All values should be JSON-serializable
            import json

            json_str = json.dumps(result)  # Should not raise exception
            assert json_str is not None

    def test_user_database_persistence(self, app):
        """Test that user can be saved to and loaded from database."""
        with app.app_context():
            # Create and save user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")
            db.session.add(user)
            db.session.commit()

            user_id = user.id

            # Clear session and reload
            db.session.expunge_all()
            loaded_user = User.query.get(user_id)

            assert loaded_user is not None
            assert loaded_user.username == "testuser"
            assert loaded_user.email == "test@example.com"
            assert loaded_user.check_password("testpassword123") is True
