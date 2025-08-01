"""
Integration tests for authentication API endpoints.

This module tests the complete authentication flow including
API endpoints, database operations, and JWT token handling.
"""

import json
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.user import User
from tests.utils import (
    APITestClient,
    AuthTestHelper,
    DatabaseTestHelper,
    ResponseTestHelper,
    ValidationTestHelper,
)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthenticationAPI:
    """Integration tests for authentication API endpoints."""

    def test_register_success(self, client, app):
        """Test successful user registration."""
        api_client = APITestClient(client)
        user_data = ValidationTestHelper.get_valid_user_data()

        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )

        # Assert response
        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["user"]["username"] == user_data["username"]
        assert response_data["user"]["email"] == user_data["email"]
        assert response_data["user"]["is_active"] is True
        assert "password" not in response_data["user"]

        # Assert database
        with app.app_context():
            user = User.query.filter_by(username=user_data["username"]).first()
            assert user is not None
            assert user.email == user_data["email"]
            assert user.check_password(user_data["password"])

    def test_register_duplicate_username(self, client, app):
        """Test registration with duplicate username."""
        api_client = APITestClient(client)

        # Create existing user
        with app.app_context():
            DatabaseTestHelper.create_user(username="existinguser")

        user_data = ValidationTestHelper.get_valid_user_data(
            username="existinguser", email="new@example.com"
        )

        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "DUPLICATE_RESOURCE"
        )

    def test_register_duplicate_email(self, client, app):
        """Test registration with duplicate email."""
        api_client = APITestClient(client)

        # Create existing user
        with app.app_context():
            DatabaseTestHelper.create_user(email="existing@example.com")

        user_data = ValidationTestHelper.get_valid_user_data(
            username="newuser", email="existing@example.com"
        )

        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "DUPLICATE_RESOURCE"
        )

    def test_register_validation_errors(self, client):
        """Test registration with various validation errors."""
        api_client = APITestClient(client)
        invalid_scenarios = ValidationTestHelper.get_invalid_user_data_scenarios()

        for scenario_name, invalid_data in invalid_scenarios.items():
            response_data, status_code = api_client.post_json(
                "/api/auth/register", invalid_data
            )

            ResponseTestHelper.assert_validation_error(response_data, status_code)
            assert "field_errors" in response_data["details"]

    def test_login_success(self, client, app):
        """Test successful user login."""
        api_client = APITestClient(client)

        # Create test user
        with app.app_context():
            user = DatabaseTestHelper.create_user()

        login_data = {"username_or_email": user.username, "password": "testpassword123"}

        response_data, status_code = api_client.post_json("/api/auth/login", login_data)

        # Assert response
        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "user" in response_data
        assert "tokens" in response_data
        assert "access_token" in response_data["tokens"]
        assert "refresh_token" in response_data["tokens"]

        ResponseTestHelper.assert_user_data(response_data["user"], user)

    def test_login_with_email(self, client, app):
        """Test login using email instead of username."""
        api_client = APITestClient(client)

        # Create test user
        with app.app_context():
            user = DatabaseTestHelper.create_user()

        login_data = {"username_or_email": user.email, "password": "testpassword123"}

        response_data, status_code = api_client.post_json("/api/auth/login", login_data)

        ResponseTestHelper.assert_success_response(response_data, status_code)
        ResponseTestHelper.assert_user_data(response_data["user"], user)

    def test_login_invalid_credentials(self, client, app):
        """Test login with invalid credentials."""
        api_client = APITestClient(client)

        # Create test user
        with app.app_context():
            user = DatabaseTestHelper.create_user()

        login_data = {"username_or_email": user.username, "password": "wrongpassword"}

        response_data, status_code = api_client.post_json("/api/auth/login", login_data)

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "INVALID_CREDENTIALS"
        )

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        api_client = APITestClient(client)

        login_data = {"username_or_email": "nonexistent", "password": "password123"}

        response_data, status_code = api_client.post_json("/api/auth/login", login_data)

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "INVALID_CREDENTIALS"
        )

    def test_login_inactive_user(self, client, app):
        """Test login with inactive user."""
        api_client = APITestClient(client)

        # Create inactive user
        with app.app_context():
            user = DatabaseTestHelper.create_user(is_active=False)

        login_data = {"username_or_email": user.username, "password": "testpassword123"}

        response_data, status_code = api_client.post_json("/api/auth/login", login_data)

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "INVALID_CREDENTIALS"
        )

    def test_login_validation_errors(self, client):
        """Test login with validation errors."""
        api_client = APITestClient(client)

        invalid_scenarios = [
            {"username_or_email": "", "password": "password123"},
            {"username_or_email": "user", "password": ""},
            {"username_or_email": "", "password": ""},
        ]

        for invalid_data in invalid_scenarios:
            response_data, status_code = api_client.post_json(
                "/api/auth/login", invalid_data
            )

            ResponseTestHelper.assert_validation_error(response_data, status_code)

    def test_refresh_token_success(self, client, app):
        """Test successful token refresh."""
        api_client = APITestClient(client)

        # Create user and get refresh token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            refresh_token = AuthTestHelper.create_refresh_token(user.id)

        headers = {"Authorization": f"Bearer {refresh_token}"}
        response_data, status_code = api_client.post_json(
            "/api/auth/refresh", {}, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "access_token" in response_data
        assert response_data["access_token"] != refresh_token

    def test_refresh_token_invalid_token(self, client):
        """Test token refresh with invalid token."""
        api_client = APITestClient(client)

        headers = {"Authorization": "Bearer invalid-token"}
        response_data, status_code = api_client.post_json(
            "/api/auth/refresh", {}, headers
        )

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_refresh_token_missing_token(self, client):
        """Test token refresh without token."""
        api_client = APITestClient(client)

        response_data, status_code = api_client.post_json("/api/auth/refresh", {})

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_refresh_token_user_not_found(self, client, app):
        """Test token refresh when user no longer exists."""
        api_client = APITestClient(client)

        # Create token for non-existent user
        with app.app_context():
            refresh_token = AuthTestHelper.create_refresh_token(999)

        headers = {"Authorization": f"Bearer {refresh_token}"}
        response_data, status_code = api_client.post_json(
            "/api/auth/refresh", {}, headers
        )

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "USER_NOT_FOUND"
        )

    def test_refresh_token_inactive_user(self, client, app):
        """Test token refresh with inactive user."""
        api_client = APITestClient(client)

        # Create inactive user and token
        with app.app_context():
            user = DatabaseTestHelper.create_user(is_active=False)
            refresh_token = AuthTestHelper.create_refresh_token(user.id)

        headers = {"Authorization": f"Bearer {refresh_token}"}
        response_data, status_code = api_client.post_json(
            "/api/auth/refresh", {}, headers
        )

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "INVALID_CREDENTIALS"
        )

    def test_logout_success(self, client, app):
        """Test successful logout."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            "/api/auth/logout", {}, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "message" in response_data

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token."""
        api_client = APITestClient(client)

        headers = {"Authorization": "Bearer invalid-token"}
        response_data, status_code = api_client.post_json(
            "/api/auth/logout", {}, headers
        )

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_logout_missing_token(self, client):
        """Test logout without token."""
        api_client = APITestClient(client)

        response_data, status_code = api_client.post_json("/api/auth/logout", {})

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_complete_auth_flow(self, client, app):
        """Test complete authentication flow: register -> login -> refresh -> logout."""
        api_client = APITestClient(client)

        # 1. Register
        user_data = ValidationTestHelper.get_valid_user_data()
        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)

        # 2. Login
        login_data = {
            "username_or_email": user_data["username"],
            "password": user_data["password"],
        }
        response_data, status_code = api_client.post_json("/api/auth/login", login_data)
        ResponseTestHelper.assert_success_response(response_data, status_code)

        access_token = response_data["tokens"]["access_token"]
        refresh_token = response_data["tokens"]["refresh_token"]

        # 3. Use access token for authenticated request
        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users/profile", headers)
        ResponseTestHelper.assert_success_response(response_data, status_code)

        # 4. Refresh token
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response_data, status_code = api_client.post_json(
            "/api/auth/refresh", {}, headers
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)

        new_access_token = response_data["access_token"]
        assert new_access_token != access_token

        # 5. Logout
        headers = AuthTestHelper.get_auth_headers(new_access_token)
        response_data, status_code = api_client.post_json(
            "/api/auth/logout", {}, headers
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)

    def test_concurrent_registrations(self, client, app):
        """Test handling of concurrent registration attempts."""
        api_client = APITestClient(client)

        # This test simulates race conditions in user registration
        user_data = ValidationTestHelper.get_valid_user_data()

        # First registration should succeed
        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)

        # Second registration with same data should fail
        response_data, status_code = api_client.post_json(
            "/api/auth/register", user_data
        )
        ResponseTestHelper.assert_error_response(
            response_data, status_code, "DUPLICATE_RESOURCE"
        )

    def test_token_expiration_handling(self, client, app):
        """Test handling of expired tokens."""
        api_client = APITestClient(client)

        # Create user and expired token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            expired_token = AuthTestHelper.create_expired_token(user.id)

        headers = AuthTestHelper.get_auth_headers(expired_token)
        response_data, status_code = api_client.get_json("/api/users/profile", headers)

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_malformed_json_requests(self, client):
        """Test handling of malformed JSON requests."""
        # Test with invalid JSON
        response = client.post(
            "/api/auth/login", data='{"invalid": json}', content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data or "message" in data

    def test_missing_content_type(self, client):
        """Test handling of requests without proper content type."""
        user_data = ValidationTestHelper.get_valid_user_data()

        response = client.post("/api/auth/register", data=json.dumps(user_data))

        # Should handle missing content-type gracefully
        assert response.status_code in [
            400,
            415,
        ]  # Bad Request or Unsupported Media Type

    def test_rate_limiting_simulation(self, client):
        """Test multiple rapid requests (simulating rate limiting scenarios)."""
        api_client = APITestClient(client)

        # Make multiple rapid login attempts
        login_data = {"username_or_email": "nonexistent", "password": "wrongpassword"}

        responses = []
        for _ in range(5):
            response_data, status_code = api_client.post_json(
                "/api/auth/login", login_data
            )
            responses.append((response_data, status_code))

        # All should fail with invalid credentials
        for response_data, status_code in responses:
            ResponseTestHelper.assert_error_response(
                response_data, status_code, "INVALID_CREDENTIALS"
            )
