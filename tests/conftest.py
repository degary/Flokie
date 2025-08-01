"""
Pytest configuration and fixtures for Flask API Template tests.

This module provides shared fixtures and configuration for all test modules.
"""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask application."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Test configuration
    test_config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(days=30),
        "SECRET_KEY": "test-secret-key",
        "ERROR_INCLUDE_MESSAGE": True,
        "ERROR_INCLUDE_DETAILS": True,
        "ERROR_INCLUDE_TRACEBACK": False,
        "ERROR_MONITORING_ENABLED": False,
        "SLOW_REQUEST_THRESHOLD": 1.0,
    }

    # Create app with test configuration
    app = create_app("testing")

    # Override config with test values
    app.config.update(test_config)

    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app

        # Clean up
        db.drop_all()

    # Close and remove the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Create an application context for testing."""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app):
    """Create a request context for testing."""
    with app.test_request_context():
        yield app


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean database before each test."""
    with app.app_context():
        # Clean up any existing data
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        # Clean up after test
        db.session.remove()


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def created_user(app, sample_user_data):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            username=sample_user_data["username"], email=sample_user_data["email"]
        )
        user.set_password(sample_user_data["password"])
        db.session.add(user)
        db.session.commit()

        # Refresh the user object to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture
def inactive_user(app):
    """Create an inactive test user in the database."""
    with app.app_context():
        user = User(
            username="inactiveuser", email="inactive@example.com", is_active=False
        )
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()

        db.session.refresh(user)
        return user


@pytest.fixture
def multiple_users(app):
    """Create multiple test users in the database."""
    with app.app_context():
        users = []
        for i in range(3):
            user = User(username=f"testuser{i}", email=f"test{i}@example.com")
            user.set_password("testpassword123")
            db.session.add(user)
            users.append(user)

        db.session.commit()

        # Refresh all user objects
        for user in users:
            db.session.refresh(user)

        return users


@pytest.fixture
def access_token(app, created_user):
    """Create a valid JWT access token for testing."""
    with app.app_context():
        return create_access_token(identity=created_user.id)


@pytest.fixture
def refresh_token(app, created_user):
    """Create a valid JWT refresh token for testing."""
    with app.app_context():
        return create_refresh_token(identity=created_user.id)


@pytest.fixture
def expired_token(app, created_user):
    """Create an expired JWT token for testing."""
    with app.app_context():
        # Create token that expires immediately
        return create_access_token(
            identity=created_user.id, expires_delta=timedelta(seconds=-1)
        )


@pytest.fixture
def auth_headers(access_token):
    """Create authorization headers with valid JWT token."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def invalid_auth_headers():
    """Create authorization headers with invalid JWT token."""
    return {"Authorization": "Bearer invalid-token", "Content-Type": "application/json"}


@pytest.fixture
def json_headers():
    """Create JSON content-type headers."""
    return {"Content-Type": "application/json"}


@pytest.fixture
def mock_external_service():
    """Mock external service for testing."""
    mock_service = MagicMock()
    mock_service.call_api.return_value = {"status": "success", "data": "test"}
    return mock_service


@pytest.fixture
def sample_validation_data():
    """Provide sample data for validation testing."""
    return {
        "valid_data": {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "validpassword123",
        },
        "invalid_data": {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
            "password": "123",  # Too short
        },
        "missing_fields": {
            "username": "testuser"
            # Missing email and password
        },
    }


@pytest.fixture
def database_error_mock():
    """Mock database error for testing error handling."""

    def _mock_db_error():
        from sqlalchemy.exc import SQLAlchemyError

        raise SQLAlchemyError("Database connection failed")

    return _mock_db_error


# Test markers for different test types
pytest_plugins = []


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "database: mark test as database related")
    config.addinivalue_line("markers", "api: mark test as API endpoint related")


# Performance monitoring fixtures
@pytest.fixture
def performance_monitor():
    """Monitor test performance."""
    import time

    start_time = time.time()
    yield
    end_time = time.time()
    duration = end_time - start_time
    if duration > 1.0:  # Log slow tests
        print(f"\nSlow test detected: {duration:.2f}s")


@pytest.fixture
def db_transaction(app):
    """Provide database transaction that can be rolled back."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        # Configure session to use the transaction
        db.session.configure(bind=connection)

        yield db.session

        # Rollback transaction
        transaction.rollback()
        connection.close()
        db.session.remove()


@pytest.fixture
def api_client(client):
    """Enhanced API client with helper methods."""

    class APIClient:
        def __init__(self, test_client):
            self.client = test_client

        def get(self, url, headers=None, **kwargs):
            return self.client.get(url, headers=headers, **kwargs)

        def post(self, url, json=None, headers=None, **kwargs):
            return self.client.post(url, json=json, headers=headers, **kwargs)

        def put(self, url, json=None, headers=None, **kwargs):
            return self.client.put(url, json=json, headers=headers, **kwargs)

        def delete(self, url, headers=None, **kwargs):
            return self.client.delete(url, headers=headers, **kwargs)

        def patch(self, url, json=None, headers=None, **kwargs):
            return self.client.patch(url, json=json, headers=headers, **kwargs)

        def post_json(self, url, data, headers=None):
            """POST with JSON data and proper headers."""
            headers = headers or {}
            headers.update({"Content-Type": "application/json"})
            return self.client.post(url, json=data, headers=headers)

        def authenticated_request(self, method, url, token, **kwargs):
            """Make authenticated request with JWT token."""
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {token}"
            kwargs["headers"] = headers
            return getattr(self.client, method.lower())(url, **kwargs)

    return APIClient(client)


# Test utilities
class TestDataFactory:
    """Factory class for creating test data."""

    @staticmethod
    def create_user_data(username=None, email=None, password=None, **kwargs):
        """Create user data for testing."""
        base_data = {
            "username": username or "testuser",
            "email": email or "test@example.com",
            "password": password or "testpassword123",
        }
        base_data.update(kwargs)
        return base_data

    @staticmethod
    def create_login_data(username_or_email=None, password=None):
        """Create login data for testing."""
        return {
            "username_or_email": username_or_email or "testuser",
            "password": password or "testpassword123",
        }

    @staticmethod
    def create_invalid_data(field_name, invalid_value):
        """Create data with specific invalid field."""
        valid_data = TestDataFactory.create_user_data()
        valid_data[field_name] = invalid_value
        return valid_data

    @staticmethod
    def create_batch_user_data(count=5):
        """Create multiple user data entries."""
        return [
            TestDataFactory.create_user_data(
                username=f"user{i}", email=f"user{i}@example.com"
            )
            for i in range(count)
        ]


# Helper functions for tests
def assert_error_response(
    response, expected_status, expected_code=None, expected_message=None
):
    """Assert that response is a proper error response."""
    assert response.status_code == expected_status

    data = response.get_json()
    assert "error" in data or "message" in data

    if expected_code:
        assert data.get("code") == expected_code

    if expected_message:
        error_message = data.get("error") or data.get("message")
        assert expected_message in error_message


def assert_success_response(response, expected_status=200):
    """Assert that response is a successful response."""
    assert response.status_code == expected_status

    data = response.get_json()
    assert data is not None

    # Should not contain error fields
    assert "error" not in data
    assert "code" not in data or data.get("code") != "ERROR"


def create_test_user(
    app,
    username="testuser",
    email="test@example.com",
    password="testpassword123",
    **kwargs,
):
    """Helper function to create a test user."""
    with app.app_context():
        user = User(username=username, email=email, **kwargs)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


def get_auth_headers(token):
    """Helper function to create authorization headers."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    import os

    os.environ["FLASK_ENV"] = "testing"
    os.environ["TESTING"] = "True"
    yield
    # Cleanup if needed


# Database fixtures for different scenarios
@pytest.fixture
def empty_db(app):
    """Provide empty database for tests that need clean state."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.session.remove()


@pytest.fixture
def populated_db(app, multiple_users):
    """Provide database with sample data."""
    with app.app_context():
        yield db


# Mock fixtures
@pytest.fixture
def mock_jwt_manager():
    """Mock JWT manager for testing."""
    from unittest.mock import MagicMock

    mock_jwt = MagicMock()
    mock_jwt.decode_token.return_value = {"sub": 1, "exp": 9999999999}
    return mock_jwt


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    from unittest.mock import MagicMock

    mock_service = MagicMock()
    mock_service.send_email.return_value = True
    return mock_service


# Test data fixtures
@pytest.fixture
def test_user_payload():
    """Standard test user payload."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def invalid_user_payloads():
    """Various invalid user payloads for testing."""
    return {
        "missing_username": {
            "email": "test@example.com",
            "password": "testpassword123",
        },
        "missing_email": {"username": "testuser", "password": "testpassword123"},
        "missing_password": {"username": "testuser", "email": "test@example.com"},
        "short_username": {
            "username": "ab",
            "email": "test@example.com",
            "password": "testpassword123",
        },
        "invalid_email": {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpassword123",
        },
        "short_password": {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
        },
    }


# Utility classes for testing
class TestAssertions:
    """Helper class for common test assertions."""

    @staticmethod
    def assert_error_response(response, expected_status, expected_code=None):
        """Assert error response format."""
        assert response.status_code == expected_status
        data = response.get_json()
        assert "error" in data or "message" in data
        if expected_code:
            assert data.get("code") == expected_code

    @staticmethod
    def assert_success_response(response, expected_status=200):
        """Assert successful response format."""
        assert response.status_code == expected_status
        data = response.get_json()
        assert data is not None
        assert "error" not in data

    @staticmethod
    def assert_user_data(response_data, expected_user):
        """Assert user data in response."""
        assert response_data["id"] == expected_user.id
        assert response_data["username"] == expected_user.username
        assert response_data["email"] == expected_user.email
        assert "password" not in response_data
        assert "password_hash" not in response_data

    @staticmethod
    def assert_validation_error(response, field_name):
        """Assert validation error for specific field."""
        assert response.status_code == 400
        data = response.get_json()
        assert data.get("code") == "VALIDATION_ERROR"
        if "details" in data and "field_errors" in data["details"]:
            assert field_name in data["details"]["field_errors"]


class TestHelpers:
    """Helper methods for common test operations."""

    @staticmethod
    def create_test_user(
        app, username="testuser", email="test@example.com", password="testpassword123"
    ):
        """Create a test user in database."""
        with app.app_context():
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            return user

    @staticmethod
    def login_user(client, username_or_email, password):
        """Login user and return response."""
        return client.post(
            "/api/auth/login",
            json={"username_or_email": username_or_email, "password": password},
        )

    @staticmethod
    def register_user(client, user_data):
        """Register user and return response."""
        return client.post("/api/auth/register", json=user_data)

    @staticmethod
    def get_user_profile(client, token):
        """Get user profile with authentication."""
        headers = {"Authorization": f"Bearer {token}"}
        return client.get("/api/users/profile", headers=headers)
