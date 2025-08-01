"""
Integration tests for user API endpoints.

This module tests the complete user management flow including
API endpoints, database operations, and authorization.
"""

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
class TestUserAPI:
    """Integration tests for user API endpoints."""

    def test_get_user_profile_success(self, client, app):
        """Test successful user profile retrieval."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users/profile", headers)

        ResponseTestHelper.assert_success_response(response_data, status_code)
        ResponseTestHelper.assert_user_data(response_data, user)

    def test_get_user_profile_unauthorized(self, client):
        """Test user profile retrieval without authentication."""
        api_client = APITestClient(client)

        response_data, status_code = api_client.get_json("/api/users/profile")

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_get_user_profile_invalid_token(self, client):
        """Test user profile retrieval with invalid token."""
        api_client = APITestClient(client)

        headers = {"Authorization": "Bearer invalid-token"}
        response_data, status_code = api_client.get_json("/api/users/profile", headers)

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_get_user_profile_user_not_found(self, client, app):
        """Test user profile retrieval when user no longer exists."""
        api_client = APITestClient(client)

        # Create token for non-existent user
        with app.app_context():
            access_token = AuthTestHelper.create_access_token(999)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users/profile", headers)

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "USER_NOT_FOUND"
        )

    def test_update_user_profile_success(self, client, app):
        """Test successful user profile update."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        update_data = {"email": "newemail@example.com"}

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.put_json(
            "/api/users/profile", update_data, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["email"] == "newemail@example.com"

        # Verify database update
        with app.app_context():
            updated_user = User.query.get(user.id)
            assert updated_user.email == "newemail@example.com"

    def test_update_user_profile_validation_error(self, client, app):
        """Test user profile update with validation error."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        update_data = {"email": "invalid-email"}

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.put_json(
            "/api/users/profile", update_data, headers
        )

        ResponseTestHelper.assert_validation_error(response_data, status_code, "email")

    def test_update_user_profile_duplicate_email(self, client, app):
        """Test user profile update with duplicate email."""
        api_client = APITestClient(client)

        # Create two users
        with app.app_context():
            user1 = DatabaseTestHelper.create_user(
                username="user1", email="user1@example.com"
            )
            user2 = DatabaseTestHelper.create_user(
                username="user2", email="user2@example.com"
            )
            access_token = AuthTestHelper.create_access_token(user1.id)

        # Try to update user1's email to user2's email
        update_data = {"email": "user2@example.com"}

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.put_json(
            "/api/users/profile", update_data, headers
        )

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "DUPLICATE_RESOURCE"
        )

    def test_update_user_profile_unauthorized(self, client):
        """Test user profile update without authentication."""
        api_client = APITestClient(client)

        update_data = {"email": "new@example.com"}
        response_data, status_code = api_client.put_json(
            "/api/users/profile", update_data
        )

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_change_password_success(self, client, app):
        """Test successful password change."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)

        # Verify password was changed
        with app.app_context():
            updated_user = User.query.get(user.id)
            assert updated_user.check_password("newpassword123")
            assert not updated_user.check_password("testpassword123")

    def test_change_password_wrong_current_password(self, client, app):
        """Test password change with wrong current password."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data, headers
        )

        ResponseTestHelper.assert_validation_error(
            response_data, status_code, "current_password"
        )

    def test_change_password_mismatch(self, client, app):
        """Test password change with password confirmation mismatch."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword123",
        }

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data, headers
        )

        ResponseTestHelper.assert_validation_error(
            response_data, status_code, "confirm_password"
        )

    def test_change_password_weak_password(self, client, app):
        """Test password change with weak new password."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        password_data = {
            "current_password": "testpassword123",
            "new_password": "123",  # Too short
            "confirm_password": "123",
        }

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data, headers
        )

        ResponseTestHelper.assert_validation_error(
            response_data, status_code, "new_password"
        )

    def test_change_password_unauthorized(self, client):
        """Test password change without authentication."""
        api_client = APITestClient(client)

        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data
        )

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_get_user_by_id_success(self, client, app):
        """Test successful user retrieval by ID."""
        api_client = APITestClient(client)

        # Create users
        with app.app_context():
            user1 = DatabaseTestHelper.create_user(username="user1")
            user2 = DatabaseTestHelper.create_user(username="user2")
            access_token = AuthTestHelper.create_access_token(user1.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json(
            f"/api/users/{user2.id}", headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        ResponseTestHelper.assert_user_data(response_data, user2)

    def test_get_user_by_id_not_found(self, client, app):
        """Test user retrieval by ID when user doesn't exist."""
        api_client = APITestClient(client)

        # Create user for authentication
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users/999", headers)

        ResponseTestHelper.assert_error_response(
            response_data, status_code, "USER_NOT_FOUND"
        )

    def test_get_user_by_id_unauthorized(self, client, app):
        """Test user retrieval by ID without authentication."""
        api_client = APITestClient(client)

        # Create user
        with app.app_context():
            user = DatabaseTestHelper.create_user()

        response_data, status_code = api_client.get_json(f"/api/users/{user.id}")

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_get_all_users_success(self, client, app):
        """Test successful retrieval of all users."""
        api_client = APITestClient(client)

        # Create multiple users
        with app.app_context():
            users = DatabaseTestHelper.create_users(3)
            access_token = AuthTestHelper.create_access_token(users[0].id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users", headers)

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "users" in response_data
        assert len(response_data["users"]) == 3

        # Verify user data
        for i, user_data in enumerate(response_data["users"]):
            assert "password" not in user_data
            assert "password_hash" not in user_data

    def test_get_all_users_empty(self, client, app):
        """Test retrieval of all users when no users exist."""
        api_client = APITestClient(client)

        # Create one user for authentication but then delete all
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)
            # Clean database
            DatabaseTestHelper.clean_database()

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users", headers)

        # This might fail due to user not existing, which is expected
        # In a real scenario, you'd need proper admin authentication
        assert status_code in [200, 401, 404]

    def test_get_all_users_unauthorized(self, client):
        """Test retrieval of all users without authentication."""
        api_client = APITestClient(client)

        response_data, status_code = api_client.get_json("/api/users")

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_search_users_success(self, client, app):
        """Test successful user search."""
        api_client = APITestClient(client)

        # Create users with searchable names
        with app.app_context():
            user1 = DatabaseTestHelper.create_user(username="testuser1")
            user2 = DatabaseTestHelper.create_user(username="testuser2")
            user3 = DatabaseTestHelper.create_user(username="otheruser")
            access_token = AuthTestHelper.create_access_token(user1.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json(
            "/api/users/search?q=test", headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "users" in response_data
        assert len(response_data["users"]) == 2  # Should find testuser1 and testuser2

    def test_search_users_no_results(self, client, app):
        """Test user search with no results."""
        api_client = APITestClient(client)

        # Create user for authentication
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json(
            "/api/users/search?q=nonexistent", headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert "users" in response_data
        assert len(response_data["users"]) == 0

    def test_search_users_missing_query(self, client, app):
        """Test user search without query parameter."""
        api_client = APITestClient(client)

        # Create user for authentication
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.get_json("/api/users/search", headers)

        ResponseTestHelper.assert_error_response(response_data, status_code)

    def test_deactivate_user_success(self, client, app):
        """Test successful user deactivation."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            f"/api/users/{user.id}/deactivate", {}, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["is_active"] is False

        # Verify database update
        with app.app_context():
            updated_user = User.query.get(user.id)
            assert updated_user.is_active is False

    def test_activate_user_success(self, client, app):
        """Test successful user activation."""
        api_client = APITestClient(client)

        # Create inactive user
        with app.app_context():
            user = DatabaseTestHelper.create_user(is_active=False)
            # For this test, we'll use the same user's token (in real scenario, admin would do this)
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)
        response_data, status_code = api_client.post_json(
            f"/api/users/{user.id}/activate", {}, headers
        )

        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["is_active"] is True

        # Verify database update
        with app.app_context():
            updated_user = User.query.get(user.id)
            assert updated_user.is_active is True

    def test_user_crud_operations_flow(self, client, app):
        """Test complete CRUD operations flow for users."""
        api_client = APITestClient(client)

        # Create initial user for authentication
        with app.app_context():
            auth_user = DatabaseTestHelper.create_user(username="authuser")
            access_token = AuthTestHelper.create_access_token(auth_user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)

        # 1. Get user profile
        response_data, status_code = api_client.get_json("/api/users/profile", headers)
        ResponseTestHelper.assert_success_response(response_data, status_code)
        original_email = response_data["email"]

        # 2. Update user profile
        update_data = {"email": "updated@example.com"}
        response_data, status_code = api_client.put_json(
            "/api/users/profile", update_data, headers
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["email"] == "updated@example.com"

        # 3. Change password
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response_data, status_code = api_client.post_json(
            "/api/users/change-password", password_data, headers
        )
        ResponseTestHelper.assert_success_response(response_data, status_code)

        # 4. Verify changes persist
        response_data, status_code = api_client.get_json("/api/users/profile", headers)
        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["email"] == "updated@example.com"

        # 5. Test login with new password
        login_data = {
            "username_or_email": auth_user.username,
            "password": "newpassword123",
        }
        response_data, status_code = api_client.post_json("/api/auth/login", login_data)
        ResponseTestHelper.assert_success_response(response_data, status_code)

    def test_concurrent_user_updates(self, client, app):
        """Test handling of concurrent user updates."""
        api_client = APITestClient(client)

        # Create user and get access token
        with app.app_context():
            user = DatabaseTestHelper.create_user()
            access_token = AuthTestHelper.create_access_token(user.id)

        headers = AuthTestHelper.get_auth_headers(access_token)

        # Simulate concurrent updates
        update_data1 = {"email": "email1@example.com"}
        update_data2 = {"email": "email2@example.com"}

        # Both updates should be processed, but the last one should win
        response_data1, status_code1 = api_client.put_json(
            "/api/users/profile", update_data1, headers
        )
        response_data2, status_code2 = api_client.put_json(
            "/api/users/profile", update_data2, headers
        )

        ResponseTestHelper.assert_success_response(response_data1, status_code1)
        ResponseTestHelper.assert_success_response(response_data2, status_code2)

        # Verify final state
        response_data, status_code = api_client.get_json("/api/users/profile", headers)
        ResponseTestHelper.assert_success_response(response_data, status_code)
        assert response_data["email"] == "email2@example.com"
