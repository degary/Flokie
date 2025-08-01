#!/usr/bin/env python3
"""
Configuration validation script for Flask API Template.

This script validates environment configurations and checks for required
environment variables and security settings.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Color codes for output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def log(message: str, color: str = Colors.GREEN) -> None:
    """Log a message with color."""
    print(f"{color}[CONFIG] {message}{Colors.NC}")


def error(message: str) -> None:
    """Log an error message."""
    log(f"ERROR: {message}", Colors.RED)


def warn(message: str) -> None:
    """Log a warning message."""
    log(f"WARNING: {message}", Colors.YELLOW)


def info(message: str) -> None:
    """Log an info message."""
    log(f"INFO: {message}", Colors.BLUE)


class ConfigValidator:
    """Configuration validator for different environments."""

    def __init__(self, environment: str):
        self.environment = environment
        self.config = {}
        self.errors = []
        self.warnings = []

    def load_env_file(self, env_file: str) -> bool:
        """Load environment file and parse variables."""
        env_path = project_root / env_file

        if not env_path.exists():
            error(f"Environment file not found: {env_file}")
            return False

        try:
            with open(env_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE format
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Handle environment variable substitution
                        if value.startswith("${") and value.endswith("}"):
                            env_var = value[2:-1]
                            value = os.environ.get(env_var, value)

                        self.config[key] = value
                    else:
                        warn(f"Invalid line format in {env_file}:{line_num}: {line}")

            info(f"Loaded configuration from {env_file}")
            return True

        except Exception as e:
            error(f"Failed to load {env_file}: {e}")
            return False

    def validate_required_vars(self) -> None:
        """Validate required environment variables."""
        required_vars = {
            "dev": ["FLASK_CONFIG", "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"],
            "test": ["FLASK_CONFIG", "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"],
            "acc": [
                "FLASK_CONFIG",
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "POSTGRES_PASSWORD",
                "REDIS_PASSWORD",
            ],
            "prod": [
                "FLASK_CONFIG",
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "POSTGRES_PASSWORD",
                "REDIS_PASSWORD",
                "CORS_ORIGINS",
            ],
        }

        env_required = required_vars.get(self.environment, required_vars["dev"])

        for var in env_required:
            if var not in self.config or not self.config[var]:
                self.errors.append(f"Required variable missing or empty: {var}")

    def validate_security_settings(self) -> None:
        """Validate security-related settings."""
        # Check secret key strength
        secret_key = self.config.get("SECRET_KEY", "")
        if secret_key:
            if len(secret_key) < 32:
                self.errors.append("SECRET_KEY should be at least 32 characters long")

            if secret_key in [
                "dev-secret-key-change-in-production",
                "test-secret-key-for-testing-only",
            ]:
                if self.environment in ["acc", "prod"]:
                    self.errors.append(
                        "Using default SECRET_KEY in production environment"
                    )
                else:
                    self.warnings.append(
                        "Using default SECRET_KEY (acceptable for dev/test)"
                    )

        # Check JWT secret key
        jwt_secret = self.config.get("JWT_SECRET_KEY", "")
        if jwt_secret:
            if len(jwt_secret) < 32:
                self.errors.append(
                    "JWT_SECRET_KEY should be at least 32 characters long"
                )

            if jwt_secret in [
                "dev-jwt-secret-key-change-in-production",
                "test-jwt-secret-key-for-testing-only",
            ]:
                if self.environment in ["acc", "prod"]:
                    self.errors.append(
                        "Using default JWT_SECRET_KEY in production environment"
                    )
                else:
                    self.warnings.append(
                        "Using default JWT_SECRET_KEY (acceptable for dev/test)"
                    )

        # Check debug settings
        flask_debug = self.config.get("FLASK_DEBUG", "0")
        if self.environment in ["acc", "prod"] and flask_debug != "0":
            self.errors.append(
                "FLASK_DEBUG should be disabled in production environments"
            )

        # Check CORS settings for production
        if self.environment == "prod":
            cors_origins = self.config.get("CORS_ORIGINS", "")
            if cors_origins == "*":
                self.errors.append("CORS_ORIGINS should not be '*' in production")

    def validate_database_config(self) -> None:
        """Validate database configuration."""
        database_url = self.config.get("DATABASE_URL", "")

        if not database_url:
            self.errors.append("DATABASE_URL is required")
            return

        try:
            parsed = urlparse(database_url)

            if not parsed.scheme:
                self.errors.append("Invalid DATABASE_URL format")
                return

            if parsed.scheme == "sqlite":
                if self.environment in ["acc", "prod"]:
                    self.warnings.append(
                        "Using SQLite in production environment (consider PostgreSQL)"
                    )
            elif parsed.scheme == "postgresql":
                if not parsed.hostname:
                    self.errors.append("PostgreSQL DATABASE_URL missing hostname")
                if not parsed.username:
                    self.errors.append("PostgreSQL DATABASE_URL missing username")
                if not parsed.password and "${" not in database_url:
                    self.warnings.append("PostgreSQL DATABASE_URL missing password")

        except Exception as e:
            self.errors.append(f"Invalid DATABASE_URL format: {e}")

    def validate_redis_config(self) -> None:
        """Validate Redis configuration."""
        redis_url = self.config.get("REDIS_URL", "")

        if redis_url:
            try:
                parsed = urlparse(redis_url)

                if parsed.scheme != "redis":
                    self.errors.append("REDIS_URL should use redis:// scheme")

                if self.environment in ["acc", "prod"]:
                    if not parsed.password and "${" not in redis_url:
                        self.warnings.append(
                            "Redis password not set for production environment"
                        )

            except Exception as e:
                self.errors.append(f"Invalid REDIS_URL format: {e}")

    def validate_logging_config(self) -> None:
        """Validate logging configuration."""
        log_level = self.config.get("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if log_level not in valid_levels:
            self.errors.append(
                f"Invalid LOG_LEVEL: {log_level}. Valid levels: {', '.join(valid_levels)}"
            )

        # Check log level appropriateness for environment
        if self.environment == "prod" and log_level == "DEBUG":
            self.warnings.append("DEBUG log level in production may impact performance")

    def validate_email_config(self) -> None:
        """Validate email configuration."""
        mail_server = self.config.get("MAIL_SERVER", "")

        if mail_server and mail_server != "localhost":
            mail_username = self.config.get("MAIL_USERNAME", "")
            mail_password = self.config.get("MAIL_PASSWORD", "")

            if not mail_username:
                self.warnings.append(
                    "MAIL_USERNAME not set but MAIL_SERVER is configured"
                )

            if not mail_password and "${" not in self.config.get("MAIL_PASSWORD", ""):
                self.warnings.append(
                    "MAIL_PASSWORD not set but MAIL_SERVER is configured"
                )

    def validate_monitoring_config(self) -> None:
        """Validate monitoring configuration."""
        if self.environment in ["acc", "prod"]:
            sentry_dsn = self.config.get("SENTRY_DSN", "")
            if not sentry_dsn:
                self.warnings.append(
                    "SENTRY_DSN not configured for production environment"
                )

            if self.environment == "prod":
                new_relic_key = self.config.get("NEW_RELIC_LICENSE_KEY", "")
                if not new_relic_key:
                    self.warnings.append(
                        "NEW_RELIC_LICENSE_KEY not configured for production"
                    )

    def validate_all(self) -> Tuple[List[str], List[str]]:
        """Run all validations and return errors and warnings."""
        self.validate_required_vars()
        self.validate_security_settings()
        self.validate_database_config()
        self.validate_redis_config()
        self.validate_logging_config()
        self.validate_email_config()
        self.validate_monitoring_config()

        return self.errors, self.warnings


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py <environment>")
        print("Environments: dev, test, acc, prod")
        sys.exit(1)

    environment = sys.argv[1]
    valid_envs = ["dev", "test", "acc", "prod"]

    if environment not in valid_envs:
        error(f"Invalid environment: {environment}")
        error(f"Valid environments: {', '.join(valid_envs)}")
        sys.exit(1)

    info(f"Validating configuration for {environment} environment")

    validator = ConfigValidator(environment)

    # Load environment file
    env_file = f".env.{environment}"
    if not validator.load_env_file(env_file):
        sys.exit(1)

    # Run validations
    errors, warnings = validator.validate_all()

    # Report results
    if warnings:
        warn(f"Found {len(warnings)} warnings:")
        for warning in warnings:
            warn(f"  - {warning}")

    if errors:
        error(f"Found {len(errors)} errors:")
        for error_msg in errors:
            error(f"  - {error_msg}")

        error("Configuration validation failed!")
        sys.exit(1)
    else:
        log("Configuration validation passed!")

        if warnings:
            warn("Configuration has warnings but is valid")
        else:
            log("Configuration is valid with no warnings")


if __name__ == "__main__":
    main()
