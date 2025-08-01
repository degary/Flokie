"""
Integration tests for database operations.

This module tests database operations, transactions, and data integrity
across the application.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from tests.utils import DatabaseTestHelper


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """Integration tests for database operations."""

    def test_user_creation_and_persistence(self, app):
        """Test user creation and database persistence."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword123")

            db.session.add(user)
            db.session.commit()

            # Verify user was saved
            assert user.id is not None
            assert user.created_at is not None
            assert user.updated_at is not None

            # Retrieve user from database
            retrieved_user = User.query.filter_by(username="testuser").first()
            assert retrieved_user is not None
            assert retrieved_user.username == "testuser"
            assert retrieved_user.email == "test@example.com"
            assert retrieved_user.check_password("testpassword123")

    def test_user_update_operations(self, app):
        """Test user update operations and timestamp handling."""
        with app.app_context():
            # Create user
            user = DatabaseTestHelper.create_user()
            original_updated_at = user.updated_at

            # Wait a bit to ensure timestamp difference
            import time

            time.sleep(0.01)

            # Update user
            user.email = "newemail@example.com"
            db.session.commit()

            # Verify update
            assert user.email == "newemail@example.com"
            assert user.updated_at > original_updated_at

            # Verify in database
            retrieved_user = User.query.get(user.id)
            assert retrieved_user.email == "newemail@example.com"
            assert retrieved_user.updated_at > original_updated_at

    def test_user_deletion(self, app):
        """Test user deletion operations."""
        with app.app_context():
            # Create user
            user = DatabaseTestHelper.create_user()
            user_id = user.id

            # Delete user
            db.session.delete(user)
            db.session.commit()

            # Verify deletion
            retrieved_user = User.query.get(user_id)
            assert retrieved_user is None

    def test_unique_constraints(self, app):
        """Test database unique constraints."""
        with app.app_context():
            # Create first user
            user1 = User(username="testuser", email="test@example.com")
            db.session.add(user1)
            db.session.commit()

            # Try to create user with same username
            user2 = User(username="testuser", email="different@example.com")
            db.session.add(user2)

            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()

            # Try to create user with same email
            user3 = User(username="differentuser", email="test@example.com")
            db.session.add(user3)

            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_transaction_rollback(self, app):
        """Test transaction rollback functionality."""
        with app.app_context():
            # Start transaction
            user1 = User(username="user1", email="user1@example.com")
            user2 = User(username="user2", email="user2@example.com")

            db.session.add(user1)
            db.session.add(user2)

            # Commit first part
            db.session.commit()

            # Verify users exist
            assert User.query.count() == 2

            # Start new transaction that will fail
            user3 = User(username="user3", email="user3@example.com")
            user4 = User(
                username="user1", email="user4@example.com"
            )  # Duplicate username

            db.session.add(user3)
            db.session.add(user4)

            # This should fail and rollback
            with pytest.raises(IntegrityError):
                db.session.commit()

            # Verify rollback - should still have only 2 users
            db.session.rollback()
            assert User.query.count() == 2
            assert User.query.filter_by(username="user3").first() is None

    def test_bulk_operations(self, app):
        """Test bulk database operations."""
        with app.app_context():
            # Create multiple users
            users = []
            for i in range(10):
                user = User(username=f"user{i}", email=f"user{i}@example.com")
                user.set_password("password123")
                users.append(user)

            # Bulk insert
            db.session.add_all(users)
            db.session.commit()

            # Verify all users were created
            assert User.query.count() == 10

            # Bulk update
            User.query.update({"is_active": False})
            db.session.commit()

            # Verify bulk update
            active_users = User.query.filter_by(is_active=True).count()
            assert active_users == 0

            # Bulk delete
            User.query.filter(User.username.like("user%")).delete()
            db.session.commit()

            # Verify bulk delete
            assert User.query.count() == 0

    def test_query_operations(self, app):
        """Test various database query operations."""
        with app.app_context():
            # Create test data
            users = [
                User(username="alice", email="alice@example.com", is_active=True),
                User(username="bob", email="bob@example.com", is_active=False),
                User(username="charlie", email="charlie@example.com", is_active=True),
                User(username="david", email="david@example.com", is_active=True),
            ]

            for user in users:
                user.set_password("password123")

            db.session.add_all(users)
            db.session.commit()

            # Test basic queries
            assert User.query.count() == 4
            assert User.query.filter_by(is_active=True).count() == 3
            assert User.query.filter_by(is_active=False).count() == 1

            # Test ordering
            ordered_users = User.query.order_by(User.username).all()
            assert ordered_users[0].username == "alice"
            assert ordered_users[-1].username == "david"

            # Test filtering
            active_users = User.query.filter(User.is_active == True).all()
            assert len(active_users) == 3

            # Test like queries
            users_with_a = User.query.filter(User.username.like("%a%")).all()
            assert len(users_with_a) >= 2  # alice, charlie, david

            # Test limit and offset
            limited_users = User.query.limit(2).all()
            assert len(limited_users) == 2

            offset_users = User.query.offset(2).all()
            assert len(offset_users) == 2

    def test_relationship_operations(self, app):
        """Test database relationship operations (when relationships exist)."""
        with app.app_context():
            # For now, just test basic user operations
            # This test can be extended when relationships are added
            user = DatabaseTestHelper.create_user()

            # Test user exists
            assert user.id is not None
            assert User.query.get(user.id) is not None

    def test_database_constraints_validation(self, app):
        """Test database-level constraint validation."""
        with app.app_context():
            # Test NOT NULL constraints
            with pytest.raises(IntegrityError):
                user = User(username=None, email="test@example.com")
                db.session.add(user)
                db.session.commit()

            db.session.rollback()

            with pytest.raises(IntegrityError):
                user = User(username="testuser", email=None)
                db.session.add(user)
                db.session.commit()

    def test_concurrent_database_access(self, app):
        """Test concurrent database access scenarios."""
        with app.app_context():
            # Create initial user
            user = DatabaseTestHelper.create_user()
            user_id = user.id

            # Simulate concurrent updates
            # In a real scenario, this would involve multiple threads/processes

            # First "transaction"
            user1 = User.query.get(user_id)
            user1.email = "email1@example.com"

            # Second "transaction"
            user2 = User.query.get(user_id)
            user2.email = "email2@example.com"

            # Commit first transaction
            db.session.add(user1)
            db.session.commit()

            # Commit second transaction (should overwrite)
            db.session.add(user2)
            db.session.commit()

            # Verify final state
            final_user = User.query.get(user_id)
            assert final_user.email == "email2@example.com"

    def test_database_performance_operations(self, app):
        """Test database performance with larger datasets."""
        with app.app_context():
            import time

            # Create larger dataset
            start_time = time.time()

            users = []
            for i in range(100):
                user = User(username=f"perfuser{i}", email=f"perf{i}@example.com")
                user.set_password("password123")
                users.append(user)

            db.session.add_all(users)
            db.session.commit()

            creation_time = time.time() - start_time

            # Test query performance
            start_time = time.time()

            # Various query operations
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            users_with_perf = User.query.filter(User.username.like("perf%")).all()
            ordered_users = User.query.order_by(User.created_at.desc()).limit(10).all()

            query_time = time.time() - start_time

            # Assertions
            assert total_users == 100
            assert active_users == 100  # All users are active by default
            assert len(users_with_perf) == 100
            assert len(ordered_users) == 10

            # Performance assertions (adjust thresholds as needed)
            assert creation_time < 5.0  # Should create 100 users in less than 5 seconds
            assert query_time < 1.0  # Should perform queries in less than 1 second

    def test_database_connection_handling(self, app):
        """Test database connection handling and recovery."""
        with app.app_context():
            # Test basic connection
            result = db.session.execute("SELECT 1").scalar()
            assert result == 1

            # Test connection after operations
            user = DatabaseTestHelper.create_user()
            assert user.id is not None

            # Test connection is still valid
            result = db.session.execute("SELECT COUNT(*) FROM user").scalar()
            assert result >= 1

    def test_database_migration_compatibility(self, app):
        """Test database schema compatibility."""
        with app.app_context():
            # Test that all expected tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            assert "user" in tables

            # Test that all expected columns exist in user table
            columns = inspector.get_columns("user")
            column_names = [col["name"] for col in columns]

            expected_columns = [
                "id",
                "username",
                "email",
                "password_hash",
                "is_active",
                "created_at",
                "updated_at",
            ]
            for col in expected_columns:
                assert col in column_names

    def test_database_data_integrity(self, app):
        """Test data integrity across operations."""
        with app.app_context():
            # Create user with specific data
            original_data = {
                "username": "integrityuser",
                "email": "integrity@example.com",
                "password": "password123",
            }

            user = User(
                username=original_data["username"], email=original_data["email"]
            )
            user.set_password(original_data["password"])
            db.session.add(user)
            db.session.commit()

            user_id = user.id

            # Perform various operations
            user.email = "updated@example.com"
            db.session.commit()

            # Verify data integrity
            retrieved_user = User.query.get(user_id)
            assert retrieved_user.username == original_data["username"]
            assert retrieved_user.email == "updated@example.com"
            assert retrieved_user.check_password(original_data["password"])
            assert retrieved_user.is_active is True
            assert retrieved_user.created_at is not None
            assert retrieved_user.updated_at is not None
            assert retrieved_user.updated_at >= retrieved_user.created_at

    def test_database_cleanup_operations(self, app):
        """Test database cleanup and maintenance operations."""
        with app.app_context():
            # Create test data
            users = DatabaseTestHelper.create_users(5)
            initial_count = User.query.count()
            assert initial_count == 5

            # Test selective cleanup
            User.query.filter(User.username.like("testuser%")).delete()
            db.session.commit()

            # Verify cleanup
            remaining_count = User.query.count()
            assert remaining_count < initial_count

            # Test complete cleanup
            DatabaseTestHelper.clean_database()

            # Verify complete cleanup
            final_count = User.query.count()
            assert final_count == 0
