"""
Test configuration and utilities.

This module provides configuration and utility functions specifically for testing.
"""

import os
import tempfile
from datetime import timedelta

from app.config.base import BaseConfig


class TestConfig(BaseConfig):
    """Enhanced test configuration."""

    # Basic test settings
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging

    # JWT configuration for testing
    JWT_SECRET_KEY = "test-jwt-secret-key-for-testing-only"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
    JWT_ALGORITHM = "HS256"

    # Security settings
    SECRET_KEY = "test-secret-key-for-testing-only"
    BCRYPT_LOG_ROUNDS = 4  # Faster hashing for tests

    # Error handling configuration
    ERROR_INCLUDE_MESSAGE = True
    ERROR_INCLUDE_DETAILS = True
    ERROR_INCLUDE_TRACEBACK = False
    ERROR_MONITORING_ENABLED = False

    # Performance settings
    SLOW_REQUEST_THRESHOLD = 1.0

    # Logging configuration
    LOG_LEVEL = "WARNING"
    LOG_TO_STDOUT = False

    # Email configuration (mock)
    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = "test@example.com"

    # Rate limiting (disabled for tests)
    RATELIMIT_ENABLED = False

    # External services (mock)
    EXTERNAL_API_BASE_URL = "http://mock-api.test"
    EXTERNAL_API_TIMEOUT = 1

    @staticmethod
    def init_app(app):
        """Initialize test application."""
        BaseConfig.init_app(app)

        # Disable logging during tests
        import logging

        logging.disable(logging.CRITICAL)


class IntegrationTestConfig(TestConfig):
    """Configuration for integration tests."""

    # Use file-based database for integration tests
    @classmethod
    def get_db_uri(cls):
        """Get database URI for integration tests."""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        return f"sqlite:///{db_path}"

    SQLALCHEMY_DATABASE_URI = get_db_uri()

    # Enable more detailed logging for integration tests
    LOG_LEVEL = "INFO"
    ERROR_INCLUDE_TRACEBACK = True


class PerformanceTestConfig(TestConfig):
    """Configuration for performance tests."""

    # Performance monitoring enabled
    SLOW_REQUEST_THRESHOLD = 0.1
    ERROR_MONITORING_ENABLED = True

    # Database optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }


# Test database utilities
class TestDatabaseManager:
    """Utility class for managing test databases."""

    @staticmethod
    def create_test_db(app):
        """Create test database with all tables."""
        from app.extensions import db

        with app.app_context():
            db.create_all()

    @staticmethod
    def drop_test_db(app):
        """Drop test database."""
        from app.extensions import db

        with app.app_context():
            db.drop_all()

    @staticmethod
    def clean_test_db(app):
        """Clean all data from test database."""
        from app.extensions import db

        with app.app_context():
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
    def seed_test_data(app):
        """Seed database with test data."""
        from app.extensions import db
        from app.models.user import User

        with app.app_context():
            # Create test users
            users = [
                User(username="testuser1", email="test1@example.com"),
                User(username="testuser2", email="test2@example.com"),
                User(username="admin", email="admin@example.com"),
            ]

            for user in users:
                user.set_password("testpassword123")
                db.session.add(user)

            db.session.commit()


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def generate_user_data(count=1, **overrides):
        """Generate user data for testing."""
        users = []
        for i in range(count):
            user_data = {
                "username": f"testuser{i}",
                "email": f"test{i}@example.com",
                "password": "testpassword123",
                "is_active": True,
            }
            user_data.update(overrides)
            users.append(user_data)

        return users[0] if count == 1 else users

    @staticmethod
    def generate_invalid_user_data():
        """Generate various invalid user data scenarios."""
        return {
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
            "missing_fields": {
                "username": "testuser"
                # Missing email and password
            },
        }

    @staticmethod
    def generate_login_data(username_or_email="testuser", password="testpassword123"):
        """Generate login data."""
        return {"username_or_email": username_or_email, "password": password}


# Test environment utilities
class TestEnvironment:
    """Utilities for managing test environment."""

    @staticmethod
    def setup_test_env():
        """Set up test environment variables."""
        os.environ["FLASK_ENV"] = "testing"
        os.environ["TESTING"] = "True"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

    @staticmethod
    def cleanup_test_env():
        """Clean up test environment."""
        test_vars = ["FLASK_ENV", "TESTING", "JWT_SECRET_KEY"]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    @staticmethod
    def mock_external_services():
        """Mock external services for testing."""
        # This would typically use responses or similar mocking library
        pass


# Test markers and categories
TEST_CATEGORIES = {
    "unit": "Unit tests for individual components",
    "integration": "Integration tests for component interactions",
    "api": "API endpoint tests",
    "service": "Service layer tests",
    "model": "Model layer tests",
    "auth": "Authentication and authorization tests",
    "database": "Database related tests",
    "validation": "Data validation tests",
    "error_handling": "Error handling tests",
    "performance": "Performance tests",
    "slow": "Slow running tests",
}


# Test result analyzers
class TestResultAnalyzer:
    """Analyze test results and provide insights."""

    @staticmethod
    def analyze_coverage(coverage_data):
        """Analyze code coverage data."""
        # Implementation would analyze coverage.xml or coverage data
        pass

    @staticmethod
    def analyze_performance(test_durations):
        """Analyze test performance data."""
        # Implementation would analyze test durations
        pass

    @staticmethod
    def generate_test_report():
        """Generate comprehensive test report."""
        # Implementation would generate detailed test report
        pass
