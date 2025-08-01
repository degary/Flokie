"""
Unit tests for validation utilities.

This module tests validation utility functions in isolation.
"""

from unittest.mock import MagicMock

import pytest

from app.utils.exceptions import ValidationError
from app.utils.validation import (
    is_valid_email,
    is_valid_username,
    sanitize_input,
    validate_email,
    validate_field_length,
    validate_json_schema,
    validate_password,
    validate_required_fields,
    validate_username,
)


@pytest.mark.unit
@pytest.mark.validation
class TestValidationUtils:
    """Test cases for validation utility functions."""

    def test_validate_email_valid_formats(self):
        """Test email validation with valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example-domain.com",
            "test@subdomain.example.com",
            "a@b.co",
            "very.long.email.address@very.long.domain.name.com",
        ]

        for email in valid_emails:
            # Should not raise any exception
            validate_email(email)

    def test_validate_email_invalid_formats(self):
        """Test email validation with invalid email formats."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "test@.com",
            "test@example.",
            "",
            None,
            "test@example..com",
            "test space@example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                validate_email(email)

            error = exc_info.value
            assert "email" in error.message.lower()

    def test_validate_username_valid_formats(self):
        """Test username validation with valid formats."""
        valid_usernames = [
            "testuser",
            "user123",
            "user_name",
            "user-name",
            "User123",
            "a" * 3,  # Minimum length
            "a" * 50,  # Maximum length
        ]

        for username in valid_usernames:
            # Should not raise any exception
            validate_username(username)

    def test_validate_username_invalid_formats(self):
        """Test username validation with invalid formats."""
        invalid_usernames = [
            "ab",  # Too short
            "a" * 51,  # Too long
            "",  # Empty
            None,  # None
            "user name",  # Space
            "user@name",  # Special character
            "user.name",  # Dot (if not allowed)
            "123",  # Only numbers
            "user#name",  # Hash symbol
        ]

        for username in invalid_usernames:
            with pytest.raises(ValidationError) as exc_info:
                validate_username(username)

            error = exc_info.value
            assert "username" in error.message.lower()

    def test_validate_password_valid_formats(self):
        """Test password validation with valid formats."""
        valid_passwords = [
            "password123",
            "MySecurePassword1",
            "a" * 8,  # Minimum length
            "a" * 128,  # Maximum length
            "Pass123!@#",
            "simple_password_123",
        ]

        for password in valid_passwords:
            # Should not raise any exception
            validate_password(password)

    def test_validate_password_invalid_formats(self):
        """Test password validation with invalid formats."""
        invalid_passwords = [
            "123",  # Too short
            "a" * 129,  # Too long
            "",  # Empty
            None,  # None
            "       ",  # Only spaces
        ]

        for password in invalid_passwords:
            with pytest.raises(ValidationError) as exc_info:
                validate_password(password)

            error = exc_info.value
            assert "password" in error.message.lower()

    def test_validate_required_fields_success(self):
        """Test successful required fields validation."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        required_fields = ["username", "email", "password"]

        # Should not raise any exception
        validate_required_fields(data, required_fields)

    def test_validate_required_fields_missing_single(self):
        """Test required fields validation with single missing field."""
        data = {
            "username": "testuser",
            "email": "test@example.com"
            # Missing password
        }
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required_fields)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "password" in error.details["field_errors"]
        assert "username" not in error.details["field_errors"]
        assert "email" not in error.details["field_errors"]

    def test_validate_required_fields_missing_multiple(self):
        """Test required fields validation with multiple missing fields."""
        data = {
            "username": "testuser"
            # Missing email and password
        }
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required_fields)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "email" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]
        assert "username" not in error.details["field_errors"]

    def test_validate_required_fields_empty_values(self):
        """Test required fields validation with empty values."""
        data = {"username": "", "email": None, "password": "   "}  # Only whitespace
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required_fields)

        error = exc_info.value
        assert "field_errors" in error.details
        assert len(error.details["field_errors"]) == 3

    def test_validate_field_length_success(self):
        """Test successful field length validation."""
        data = {
            "username": "testuser",
            "password": "password123",
            "description": "A short description",
        }
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
            "description": {"min": 0, "max": 500},
        }

        # Should not raise any exception
        validate_field_length(data, constraints)

    def test_validate_field_length_too_short(self):
        """Test field length validation with too short values."""
        data = {"username": "ab", "password": "123"}  # Too short  # Too short
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_field_length(data, constraints)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "username" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]
        assert "at least" in error.details["field_errors"]["username"]

    def test_validate_field_length_too_long(self):
        """Test field length validation with too long values."""
        data = {"username": "a" * 51, "password": "a" * 129}  # Too long  # Too long
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_field_length(data, constraints)

        error = exc_info.value
        assert "field_errors" in error.details
        assert "username" in error.details["field_errors"]
        assert "password" in error.details["field_errors"]
        assert "no more than" in error.details["field_errors"]["username"]

    def test_validate_field_length_missing_field(self):
        """Test field length validation with missing field."""
        data = {
            "username": "testuser"
            # Missing password
        }
        constraints = {
            "username": {"min": 3, "max": 50},
            "password": {"min": 8, "max": 128},
        }

        # Should not raise exception for missing fields (handled by required validation)
        validate_field_length(data, constraints)

    def test_is_valid_email_true(self):
        """Test is_valid_email returns True for valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
        ]

        for email in valid_emails:
            assert is_valid_email(email) is True

    def test_is_valid_email_false(self):
        """Test is_valid_email returns False for invalid emails."""
        invalid_emails = ["invalid-email", "@example.com", "test@", None, ""]

        for email in invalid_emails:
            assert is_valid_email(email) is False

    def test_is_valid_username_true(self):
        """Test is_valid_username returns True for valid usernames."""
        valid_usernames = ["testuser", "user123", "user_name"]

        for username in valid_usernames:
            assert is_valid_username(username) is True

    def test_is_valid_username_false(self):
        """Test is_valid_username returns False for invalid usernames."""
        invalid_usernames = [
            "ab",  # Too short
            "a" * 51,  # Too long
            "user name",  # Space
            None,
            "",
        ]

        for username in invalid_usernames:
            assert is_valid_username(username) is False

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        test_cases = [
            ("  hello world  ", "hello world"),
            ("Hello World", "Hello World"),
            ("", ""),
            ("   ", ""),
            (None, ""),
            ("test\n\r\t", "test"),
            ("multiple   spaces", "multiple spaces"),
        ]

        for input_val, expected in test_cases:
            result = sanitize_input(input_val)
            assert result == expected

    def test_sanitize_input_html_tags(self):
        """Test input sanitization removes HTML tags."""
        test_cases = [
            ('<script>alert("xss")</script>', 'alert("xss")'),
            ("<b>bold text</b>", "bold text"),
            ("Normal text", "Normal text"),
            ("<div><p>nested</p></div>", "nested"),
        ]

        for input_val, expected in test_cases:
            result = sanitize_input(input_val)
            assert result == expected

    def test_sanitize_input_special_characters(self):
        """Test input sanitization handles special characters."""
        test_cases = [
            ("user@example.com", "user@example.com"),
            ("user-name_123", "user-name_123"),
            ("price: $19.99", "price: $19.99"),
            ("100% success", "100% success"),
        ]

        for input_val, expected in test_cases:
            result = sanitize_input(input_val)
            assert result == expected

    def test_validate_json_schema_valid(self):
        """Test JSON schema validation with valid data."""
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": 3},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["username", "email"],
        }

        valid_data = {"username": "testuser", "email": "test@example.com", "age": 25}

        # Should not raise any exception
        validate_json_schema(valid_data, schema)

    def test_validate_json_schema_invalid(self):
        """Test JSON schema validation with invalid data."""
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": 3},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["username", "email"],
        }

        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_json_schema(invalid_data, schema)

        error = exc_info.value
        assert "schema validation" in error.message.lower()

    def test_validate_json_schema_missing_required(self):
        """Test JSON schema validation with missing required fields."""
        schema = {
            "type": "object",
            "properties": {"username": {"type": "string"}, "email": {"type": "string"}},
            "required": ["username", "email"],
        }

        invalid_data = {
            "username": "testuser"
            # Missing email
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_json_schema(invalid_data, schema)

        error = exc_info.value
        assert "required" in error.message.lower()

    def test_validation_error_aggregation(self):
        """Test that multiple validation errors are properly aggregated."""
        data = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
            "password": "123",  # Too short
        }

        # Test multiple validations
        field_errors = {}

        try:
            validate_username(data["username"])
        except ValidationError as e:
            field_errors.update(e.details.get("field_errors", {}))

        try:
            validate_email(data["email"])
        except ValidationError as e:
            field_errors.update(e.details.get("field_errors", {}))

        try:
            validate_password(data["password"])
        except ValidationError as e:
            field_errors.update(e.details.get("field_errors", {}))

        assert len(field_errors) >= 2  # Should have multiple errors

    def test_validation_with_custom_messages(self):
        """Test validation with custom error messages."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid-email", custom_message="Custom email error")

        error = exc_info.value
        assert "Custom email error" in error.message

    def test_validation_case_insensitive_email(self):
        """Test that email validation handles case properly."""
        emails = ["Test@Example.Com", "USER@DOMAIN.COM", "MixedCase@Example.org"]

        for email in emails:
            # Should not raise exception
            validate_email(email)
