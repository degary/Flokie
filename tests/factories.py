"""
Test data factories for generating test objects.

This module provides factory classes for creating test data using factory_boy.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from app.extensions import db
from app.models.user import User

fake = Faker()


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory class with common configuration."""

    class Meta:
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return

        password = extracted or "testpassword123"
        obj.set_password(password)


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive User instances."""

    is_active = False


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""

    username = factory.Sequence(lambda n: f"admin{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@admin.example.com")
    # Add admin-specific fields when implemented


# Factory traits for different user scenarios
class UserFactoryTraits:
    """Traits for UserFactory to create specific user types."""

    @staticmethod
    def with_long_username():
        """Create user with long username."""
        return UserFactory(username="a" * 50)

    @staticmethod
    def with_special_chars_username():
        """Create user with special characters in username."""
        return UserFactory(username="user_test-123")

    @staticmethod
    def with_gmail_email():
        """Create user with Gmail email."""
        return UserFactory(
            email=factory.LazyAttribute(lambda obj: f"{obj.username}@gmail.com")
        )

    @staticmethod
    def with_corporate_email():
        """Create user with corporate email."""
        return UserFactory(
            email=factory.LazyAttribute(lambda obj: f"{obj.username}@company.com")
        )


# Data generators for testing
class TestDataGenerator:
    """Generator for various test data scenarios."""

    @staticmethod
    def valid_user_data():
        """Generate valid user registration data."""
        return {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password(length=12),
        }

    @staticmethod
    def invalid_user_data():
        """Generate invalid user registration data."""
        return {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
            "password": "123",  # Too short
        }

    @staticmethod
    def valid_login_data():
        """Generate valid login data."""
        return {"username_or_email": fake.user_name(), "password": fake.password()}

    @staticmethod
    def invalid_login_data():
        """Generate invalid login data."""
        return {"username_or_email": "", "password": ""}  # Empty  # Empty

    @staticmethod
    def user_update_data():
        """Generate user update data."""
        return {"email": fake.email(), "is_active": fake.boolean()}

    @staticmethod
    def password_change_data():
        """Generate password change data."""
        return {
            "current_password": "oldpassword123",
            "new_password": fake.password(length=12),
            "confirm_password": None,  # Will be set to new_password
        }

    @staticmethod
    def bulk_user_data(count=5):
        """Generate bulk user data for testing."""
        users = []
        for i in range(count):
            users.append(
                {
                    "username": f"bulkuser{i}",
                    "email": f"bulk{i}@example.com",
                    "password": "testpassword123",
                }
            )
        return users


# Mock data for external services
class MockDataGenerator:
    """Generator for mock external service responses."""

    @staticmethod
    def external_api_success_response():
        """Generate successful external API response."""
        return {
            "status": "success",
            "data": {"id": fake.uuid4(), "message": "Operation completed successfully"},
        }

    @staticmethod
    def external_api_error_response():
        """Generate error external API response."""
        return {
            "status": "error",
            "error": {
                "code": "EXTERNAL_ERROR",
                "message": "External service unavailable",
            },
        }

    @staticmethod
    def rate_limit_response():
        """Generate rate limit response."""
        return {
            "status": "error",
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "retry_after": 60,
            },
        }


# Database state helpers
class DatabaseStateHelper:
    """Helper class for managing database state in tests."""

    @staticmethod
    def create_users(count=3):
        """Create multiple users for testing."""
        return UserFactory.create_batch(count)

    @staticmethod
    def create_user_with_posts(post_count=3):
        """Create user with associated posts (when Post model is implemented)."""
        user = UserFactory()
        # TODO: Create posts when Post model is implemented
        return user

    @staticmethod
    def create_test_scenario_users():
        """Create users for common test scenarios."""
        return {
            "active_user": UserFactory(),
            "inactive_user": InactiveUserFactory(),
            "admin_user": AdminUserFactory(),
        }

    @staticmethod
    def cleanup_test_data():
        """Clean up test data from database."""
        db.session.query(User).delete()
        db.session.commit()


# Assertion helpers
class TestAssertions:
    """Helper class for common test assertions."""

    @staticmethod
    def assert_user_created(user_data, created_user):
        """Assert that user was created correctly."""
        assert created_user.username == user_data["username"]
        assert created_user.email == user_data["email"]
        assert created_user.check_password(user_data["password"])
        assert created_user.is_active is True
        assert created_user.created_at is not None
        assert created_user.updated_at is not None

    @staticmethod
    def assert_user_response(response_data, user):
        """Assert that user response contains correct data."""
        assert response_data["id"] == user.id
        assert response_data["username"] == user.username
        assert response_data["email"] == user.email
        assert response_data["is_active"] == user.is_active
        # Password should not be in response
        assert "password" not in response_data
        assert "password_hash" not in response_data

    @staticmethod
    def assert_error_response(response_data, expected_code, expected_message=None):
        """Assert that error response has correct format."""
        assert "error" in response_data or "message" in response_data
        assert response_data.get("code") == expected_code

        if expected_message:
            error_message = response_data.get("error") or response_data.get("message")
            assert expected_message in error_message

    @staticmethod
    def assert_validation_error(response_data, field_name):
        """Assert that validation error contains specific field error."""
        assert response_data.get("code") == "VALIDATION_ERROR"
        assert "details" in response_data
        assert "field_errors" in response_data["details"]
        assert field_name in response_data["details"]["field_errors"]
