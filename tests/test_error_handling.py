"""
Tests for error handling and exception management system.

This module tests the custom exception classes, error handlers, and error helpers
to ensure proper error handling throughout the application.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, request

from app.utils.error_handlers import (
    create_error_response,
    get_error_context,
    log_error_metrics,
    register_error_handlers,
    setup_error_monitoring,
)
from app.utils.error_helpers import (
    check_resource_exists,
    check_user_exists,
    safe_get_or_404,
    validate_business_rule,
    validate_field_length,
    validate_required_fields,
)
from app.utils.exceptions import (
    APIException,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    ConflictError,
    DatabaseError,
    DuplicateResourceError,
    ExternalServiceError,
    InvalidCredentialsError,
    NotFoundError,
    RateLimitError,
    TokenExpiredError,
    UserNotFoundError,
    ValidationError,
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_api_exception_base_class(self):
        """Test APIException base class functionality."""
        error = APIException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"field": "value"},
        )

        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.status_code == 400
        assert error.details == {"field": "value"}
        assert isinstance(error.timestamp, datetime)

        # Test to_dict method
        error_dict = error.to_dict()
        assert error_dict["error"] == "Test error"
        assert error_dict["code"] == "TEST_ERROR"
        assert error_dict["details"] == {"field": "value"}
        assert "timestamp" in error_dict

    def test_validation_error(self):
        """Test ValidationError with field errors."""
        field_errors = {"username": "Required field", "email": "Invalid format"}
        error = ValidationError(message="Validation failed", field_errors=field_errors)

        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field_errors"] == field_errors

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials")

        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.message == "Invalid credentials"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError("Access denied")

        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.message == "Access denied"

    def test_not_found_error(self):
        """Test NotFoundError with resource type."""
        error = NotFoundError(resource_type="User")

        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"
        assert error.message == "User not found"
        assert error.details["resource_type"] == "User"

    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Resource already exists")

        assert error.status_code == 409
        assert error.error_code == "CONFLICT_ERROR"
        assert error.message == "Resource already exists"

    def test_business_logic_error(self):
        """Test BusinessLogicError."""
        error = BusinessLogicError("Invalid operation")

        assert error.status_code == 400
        assert error.error_code == "BUSINESS_LOGIC_ERROR"
        assert error.message == "Invalid operation"

    def test_external_service_error(self):
        """Test ExternalServiceError with service name."""
        error = ExternalServiceError(service_name="PaymentService")

        assert error.status_code == 502
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.message == "PaymentService service unavailable"
        assert error.details["service_name"] == "PaymentService"

    def test_rate_limit_error(self):
        """Test RateLimitError with retry after."""
        error = RateLimitError(retry_after=60)

        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.details["retry_after"] == 60

    def test_database_error(self):
        """Test DatabaseError with operation."""
        error = DatabaseError(operation="INSERT")

        assert error.status_code == 500
        assert error.error_code == "DATABASE_ERROR"
        assert error.details["operation"] == "INSERT"

    def test_user_not_found_error(self):
        """Test UserNotFoundError with user ID."""
        error = UserNotFoundError(user_id="123")

        assert error.status_code == 404
        assert error.error_code == "USER_NOT_FOUND"
        assert error.message == "User not found"
        assert error.details["user_id"] == "123"

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError."""
        error = InvalidCredentialsError()

        assert error.status_code == 401
        assert error.error_code == "INVALID_CREDENTIALS"
        assert error.message == "Invalid username or password"

    def test_duplicate_resource_error(self):
        """Test DuplicateResourceError."""
        error = DuplicateResourceError("User", "email")

        assert error.status_code == 409
        assert error.error_code == "DUPLICATE_RESOURCE"
        assert error.message == "User with this email already exists"
        assert error.details["resource_type"] == "User"
        assert error.details["field"] == "email"


class TestErrorHelpers:
    """Test error helper functions."""

    def test_validate_required_fields_success(self):
        """Test successful required field validation."""
        data = {"username": "testuser", "email": "test@example.com"}
        required_fields = ["username", "email"]

        # Should not raise any exception
        validate_required_fields(data, required_fields)

    def test_validate_required_fields_missing(self):
        """Test required field validation with missing fields."""
        data = {"username": "testuser"}
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required_fields)

        error = exc_info.value
        assert "Missing required fields" in error.message
        assert "email" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]

    def test_validate_field_length_success(self):
        """Test successful field length validation."""
        data = {"username": "testuser", "password": "password123"}
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
        }

        # Should not raise any exception
        validate_field_length(data, constraints)

    def test_validate_field_length_too_short(self):
        """Test field length validation with too short field."""
        data = {"username": "ab", "password": "123"}
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_field_length(data, constraints)

        error = exc_info.value
        assert "username" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]
        assert "at least" in error.details["field_errors"]["username"]

    def test_validate_field_length_too_long(self):
        """Test field length validation with too long field."""
        data = {"username": "a" * 100}
        constraints = {"username": {"min": 3, "max": 50}}

        with pytest.raises(ValidationError) as exc_info:
            validate_field_length(data, constraints)

        error = exc_info.value
        assert "username" in error.details["field_errors"]
        assert "no more than" in error.details["field_errors"]["username"]

    def test_check_resource_exists_success(self):
        """Test successful resource existence check."""
        resource = {"id": 1, "name": "Test Resource"}

        # Should not raise any exception
        check_resource_exists(resource, "Resource")

    def test_check_resource_exists_not_found(self):
        """Test resource existence check with None resource."""
        with pytest.raises(NotFoundError) as exc_info:
            check_resource_exists(None, "User", "123")

        error = exc_info.value
        assert "User with identifier '123' not found" in error.message
        assert error.details["identifier"] == "123"

    def test_check_user_exists_success(self):
        """Test successful user existence check."""
        user = {"id": 1, "username": "testuser"}

        # Should not raise any exception
        check_user_exists(user)

    def test_check_user_exists_not_found(self):
        """Test user existence check with None user."""
        with pytest.raises(UserNotFoundError) as exc_info:
            check_user_exists(None, "123")

        error = exc_info.value
        assert error.details["user_id"] == "123"

    def test_validate_business_rule_success(self):
        """Test successful business rule validation."""
        # Should not raise any exception
        validate_business_rule(True, "Rule should pass")

    def test_validate_business_rule_failure(self):
        """Test business rule validation failure."""
        with pytest.raises(BusinessLogicError) as exc_info:
            validate_business_rule(False, "Rule failed", {"reason": "test"})

        error = exc_info.value
        assert error.message == "Rule failed"
        assert error.details["reason"] == "test"


class TestErrorHandlers:
    """Test error handler functions."""

    def test_get_error_context(self):
        """Test error context generation."""
        app = Flask(__name__)

        with app.test_request_context("/test", method="POST"):
            context = get_error_context()

            assert context["method"] == "POST"
            assert context["path"] == "/test"
            assert "timestamp" in context
            assert "remote_addr" in context

    def test_create_error_response_api_exception(self):
        """Test error response creation for API exceptions."""
        app = Flask(__name__)
        app.config["ERROR_INCLUDE_DETAILS"] = True
        app.config["ERROR_INCLUDE_TRACEBACK"] = False

        with app.app_context():
            with app.test_request_context("/test"):
                error = ValidationError(
                    "Test validation error", field_errors={"field": "error"}
                )
                response_data, status_code = create_error_response(error)

                assert status_code == 400
                assert response_data["error"] == "Test validation error"
                assert response_data["code"] == "VALIDATION_ERROR"
                assert "details" in response_data
                assert response_data["path"] == "/test"

    def test_create_error_response_generic_exception(self):
        """Test error response creation for generic exceptions."""
        app = Flask(__name__)
        app.config["ENV"] = "development"
        app.config["ERROR_INCLUDE_MESSAGE"] = True
        app.config["ERROR_INCLUDE_TRACEBACK"] = False

        with app.app_context():
            with app.test_request_context("/test"):
                error = ValueError("Generic error")
                response_data, status_code = create_error_response(error)

                assert status_code == 500
                assert response_data["code"] == "INTERNAL_ERROR"
                assert response_data["message"] == "Generic error"

    def test_create_error_response_production_mode(self):
        """Test error response creation in production mode."""
        app = Flask(__name__)
        app.config["ENV"] = "production"
        app.config["ERROR_INCLUDE_MESSAGE"] = True
        app.config["ERROR_INCLUDE_DETAILS"] = False
        app.config["ERROR_INCLUDE_TRACEBACK"] = False

        with app.app_context():
            with app.test_request_context("/test"):
                error = ValueError("Sensitive error")
                response_data, status_code = create_error_response(error)

                assert status_code == 500
                assert response_data["message"] == "An unexpected error occurred"
                assert "details" not in response_data or not response_data["details"]
                assert "traceback" not in response_data


class TestErrorHandlerIntegration:
    """Test error handler integration with Flask app."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with error handlers."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["ERROR_MONITORING_ENABLED"] = True
        app.config["SLOW_REQUEST_THRESHOLD"] = 0.1

        register_error_handlers(app)
        setup_error_monitoring(app)

        @app.route("/test-validation-error")
        def test_validation_error():
            raise ValidationError("Test validation", field_errors={"field": "error"})

        @app.route("/test-auth-error")
        def test_auth_error():
            raise AuthenticationError("Test auth error")

        @app.route("/test-not-found")
        def test_not_found():
            raise NotFoundError("Resource not found", resource_type="TestResource")

        @app.route("/test-generic-error")
        def test_generic_error():
            raise ValueError("Generic error")

        @app.route("/test-success")
        def test_success():
            return {"message": "success"}

        return app

    def test_validation_error_handler(self, app):
        """Test validation error handling."""
        with app.test_client() as client:
            response = client.get("/test-validation-error")

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["code"] == "VALIDATION_ERROR"
            assert data["error"] == "Test validation"
            assert "field_errors" in data["details"]

    def test_authentication_error_handler(self, app):
        """Test authentication error handling."""
        with app.test_client() as client:
            response = client.get("/test-auth-error")

            assert response.status_code == 401
            data = json.loads(response.data)
            assert data["code"] == "AUTHENTICATION_ERROR"
            assert data["error"] == "Test auth error"

    def test_not_found_error_handler(self, app):
        """Test not found error handling."""
        with app.test_client() as client:
            response = client.get("/test-not-found")

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["code"] == "NOT_FOUND"
            assert data["error"] == "Resource not found"

    def test_generic_error_handler(self, app):
        """Test generic error handling."""
        with app.test_client() as client:
            response = client.get("/test-generic-error")

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["code"] == "INTERNAL_ERROR"

    def test_error_monitoring(self, app):
        """Test error monitoring functionality."""
        with app.test_client() as client:
            # Make a successful request
            response = client.get("/test-success")
            assert response.status_code == 200

            # Make an error request
            response = client.get("/test-validation-error")
            assert response.status_code == 400

            # Check if error statistics endpoint works (in debug mode)
            app.config["DEBUG"] = True
            response = client.get("/internal/error-stats")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "error_stats" in data
            assert data["error_stats"]["total_requests"] > 0


class TestServiceIntegration:
    """Test integration with services using new exception system."""

    def test_auth_service_validation_errors(self):
        """Test auth service validation using new exceptions."""
        from app.services.auth_service import AuthService

        # Test missing required fields
        with pytest.raises(ValidationError) as exc_info:
            AuthService.login("", "")

        error = exc_info.value
        assert "field_errors" in error.details
        assert "username_or_email" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]

    def test_auth_service_registration_validation(self):
        """Test auth service registration validation."""
        from app.services.auth_service import AuthService

        # Test field length validation
        with pytest.raises(ValidationError) as exc_info:
            AuthService.register(
                "ab", "test@example.com", "123"
            )  # Short username and password

        error = exc_info.value
        assert "field_errors" in error.details
        assert "username" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
