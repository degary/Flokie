"""
Test utilities and helper functions.

This module provides utility functions and classes to support testing
across the application.
"""

import json
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from flask import Flask
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models.user import User


class APITestClient:
    """Enhanced test client with convenience methods for API testing."""

    def __init__(self, test_client):
        self.client = test_client

    def get_json(self, url: str, headers: Optional[Dict] = None, **kwargs) -> tuple:
        """GET request returning JSON response and status code."""
        response = self.client.get(url, headers=headers, **kwargs)
        return response.get_json(), response.status_code

    def post_json(
        self, url: str, data: Dict, headers: Optional[Dict] = None, **kwargs
    ) -> tuple:
        """POST request with JSON data returning JSON response and status code."""
        headers = headers or {}
        headers.setdefault("Content-Type", "application/json")
        response = self.client.post(url, json=data, headers=headers, **kwargs)
        return response.get_json(), response.status_code

    def put_json(
        self, url: str, data: Dict, headers: Optional[Dict] = None, **kwargs
    ) -> tuple:
        """PUT request with JSON data returning JSON response and status code."""
        headers = headers or {}
        headers.setdefault("Content-Type", "application/json")
        response = self.client.put(url, json=data, headers=headers, **kwargs)
        return response.get_json(), response.status_code

    def delete_json(self, url: str, headers: Optional[Dict] = None, **kwargs) -> tuple:
        """DELETE request returning JSON response and status code."""
        response = self.client.delete(url, headers=headers, **kwargs)
        return response.get_json(), response.status_code

    def authenticated_request(
        self, method: str, url: str, token: str, **kwargs
    ) -> tuple:
        """Make authenticated request with JWT token."""
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        response = getattr(self.client, method.lower())(url, **kwargs)
        return response.get_json(), response.status_code


class DatabaseTestHelper:
    """Helper class for database operations in tests."""

    @staticmethod
    def create_user(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword123",
        **kwargs,
    ) -> User:
        """Create a test user in the database."""
        user = User(username=username, email=email, **kwargs)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

    @staticmethod
    def create_users(count: int = 3, **kwargs) -> List[User]:
        """Create multiple test users."""
        users = []
        for i in range(count):
            user = DatabaseTestHelper.create_user(
                username=f"testuser{i}", email=f"test{i}@example.com", **kwargs
            )
            users.append(user)
        return users

    @staticmethod
    def clean_database():
        """Clean all data from the database."""
        # Get all table names
        tables = db.metadata.tables.keys()

        # Disable foreign key constraints for SQLite
        if "sqlite" in str(db.engine.url):
            db.session.execute("PRAGMA foreign_keys=OFF")

        # Delete all data
        for table in tables:
            db.session.execute(f"DELETE FROM {table}")

        # Re-enable foreign key constraints
        if "sqlite" in str(db.engine.url):
            db.session.execute("PRAGMA foreign_keys=ON")

        db.session.commit()

    @staticmethod
    @contextmanager
    def database_transaction():
        """Context manager for database transactions that can be rolled back."""
        connection = db.engine.connect()
        transaction = connection.begin()

        try:
            # Configure session to use the transaction
            db.session.configure(bind=connection)
            yield db.session
        finally:
            # Rollback transaction
            transaction.rollback()
            connection.close()
            db.session.remove()


class AuthTestHelper:
    """Helper class for authentication-related test operations."""

    @staticmethod
    def create_access_token(
        user_id: int, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token for testing."""
        return create_access_token(identity=user_id, expires_delta=expires_delta)

    @staticmethod
    def create_refresh_token(
        user_id: int, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT refresh token for testing."""
        return create_refresh_token(identity=user_id, expires_delta=expires_delta)

    @staticmethod
    def create_expired_token(user_id: int) -> str:
        """Create an expired JWT token for testing."""
        return create_access_token(
            identity=user_id, expires_delta=timedelta(seconds=-1)
        )

    @staticmethod
    def get_auth_headers(token: str) -> Dict[str, str]:
        """Get authorization headers with JWT token."""
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def login_user(client, username_or_email: str, password: str) -> tuple:
        """Login user and return response data and status code."""
        api_client = APITestClient(client)
        return api_client.post_json(
            "/api/auth/login",
            {"username_or_email": username_or_email, "password": password},
        )

    @staticmethod
    def register_user(client, user_data: Dict) -> tuple:
        """Register user and return response data and status code."""
        api_client = APITestClient(client)
        return api_client.post_json("/api/auth/register", user_data)


class ValidationTestHelper:
    """Helper class for validation testing."""

    @staticmethod
    def get_valid_user_data(**overrides) -> Dict[str, Any]:
        """Get valid user data for testing."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        }
        data.update(overrides)
        return data

    @staticmethod
    def get_invalid_user_data_scenarios() -> Dict[str, Dict[str, Any]]:
        """Get various invalid user data scenarios."""
        return {
            "missing_username": {
                "email": "test@example.com",
                "password": "testpassword123",
            },
            "missing_email": {"username": "testuser", "password": "testpassword123"},
            "missing_password": {"username": "testuser", "email": "test@example.com"},
            "empty_username": {
                "username": "",
                "email": "test@example.com",
                "password": "testpassword123",
            },
            "short_username": {
                "username": "ab",
                "email": "test@example.com",
                "password": "testpassword123",
            },
            "long_username": {
                "username": "a" * 101,
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


class ResponseTestHelper:
    """Helper class for testing API responses."""

    @staticmethod
    def assert_success_response(response_data: Dict, status_code: int = 200):
        """Assert that response is successful."""
        assert status_code in range(200, 300)
        assert response_data is not None
        assert "error" not in response_data

    @staticmethod
    def assert_error_response(
        response_data: Dict,
        status_code: int,
        expected_code: Optional[str] = None,
        expected_message: Optional[str] = None,
    ):
        """Assert that response is an error response."""
        assert status_code >= 400
        assert "error" in response_data or "message" in response_data

        if expected_code:
            assert response_data.get("code") == expected_code

        if expected_message:
            error_message = response_data.get("error") or response_data.get("message")
            assert expected_message in error_message

    @staticmethod
    def assert_validation_error(
        response_data: Dict, status_code: int, field_name: Optional[str] = None
    ):
        """Assert that response is a validation error."""
        assert status_code == 400
        assert response_data.get("code") == "VALIDATION_ERROR"

        if field_name:
            assert "details" in response_data
            assert "field_errors" in response_data["details"]
            assert field_name in response_data["details"]["field_errors"]

    @staticmethod
    def assert_user_response(response_data: Dict, expected_user: User):
        """Assert that response contains correct user data."""
        assert response_data["id"] == expected_user.id
        assert response_data["username"] == expected_user.username
        assert response_data["email"] == expected_user.email
        assert response_data["is_active"] == expected_user.is_active

        # Sensitive fields should not be present
        assert "password" not in response_data
        assert "password_hash" not in response_data


class MockHelper:
    """Helper class for creating mocks and patches."""

    @staticmethod
    def mock_external_service(service_name: str = "external_service"):
        """Create a mock external service."""
        mock_service = MagicMock()
        mock_service.name = service_name
        mock_service.call_api.return_value = {"status": "success", "data": "test"}
        mock_service.is_available.return_value = True
        return mock_service

    @staticmethod
    def mock_email_service():
        """Create a mock email service."""
        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_service.send_bulk_email.return_value = {"sent": 5, "failed": 0}
        return mock_service

    @staticmethod
    @contextmanager
    def mock_datetime_now(mock_datetime):
        """Context manager to mock datetime.now()."""
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_datetime
            mock_dt.utcnow.return_value = mock_datetime
            yield mock_dt

    @staticmethod
    @contextmanager
    def mock_database_error():
        """Context manager to mock database errors."""
        from sqlalchemy.exc import SQLAlchemyError

        with patch.object(db.session, "commit") as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database error")
            yield mock_commit


class PerformanceTestHelper:
    """Helper class for performance testing."""

    @staticmethod
    @contextmanager
    def measure_time():
        """Context manager to measure execution time."""
        import time

        start_time = time.time()
        yield
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.4f} seconds")

    @staticmethod
    def create_load_test_data(count: int = 100) -> List[Dict]:
        """Create data for load testing."""
        return [
            {
                "username": f"loaduser{i}",
                "email": f"load{i}@example.com",
                "password": "testpassword123",
            }
            for i in range(count)
        ]


class FileTestHelper:
    """Helper class for file-related testing."""

    @staticmethod
    @contextmanager
    def temporary_file(content: str = "", suffix: str = ".txt"):
        """Context manager for temporary files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            yield temp_path
        finally:
            import os

            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    @contextmanager
    def temporary_directory():
        """Context manager for temporary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir


# Test data constants
TEST_USER_DATA = {
    "valid": {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    },
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpassword123",
    },
}

TEST_LOGIN_DATA = {
    "valid": {"username_or_email": "testuser", "password": "testpassword123"},
    "invalid": {"username_or_email": "wronguser", "password": "wrongpassword"},
}

# Common test scenarios
COMMON_TEST_SCENARIOS = {
    "user_registration": [
        "valid_data",
        "missing_username",
        "missing_email",
        "missing_password",
        "invalid_email",
        "short_password",
        "duplicate_username",
        "duplicate_email",
    ],
    "user_login": [
        "valid_credentials",
        "invalid_username",
        "invalid_password",
        "inactive_user",
        "missing_credentials",
    ],
    "authenticated_requests": [
        "valid_token",
        "invalid_token",
        "expired_token",
        "missing_token",
    ],
}
