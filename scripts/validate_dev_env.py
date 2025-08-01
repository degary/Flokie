#!/usr/bin/env python3
"""
Development environment validation script.

This script checks if the development environment is properly configured.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info

    if version.major == 3 and version.minor >= 8:
        print(
            f"   ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)"
        )
        return True
    else:
        print(
            f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires Python 3.8+)"
        )
        return False


def check_virtual_environment():
    """Check if virtual environment is active."""
    print("🏠 Checking virtual environment...")

    if os.environ.get("VIRTUAL_ENV"):
        venv_path = os.environ["VIRTUAL_ENV"]
        print(f"   ✅ Virtual environment active: {venv_path}")
        return True
    else:
        print("   ⚠️  No virtual environment detected")
        print("      Consider using: python -m venv venv && source venv/bin/activate")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("📦 Checking dependencies...")

    required_packages = [
        "flask",
        "flask_sqlalchemy",
        "flask_migrate",
        "flask_jwt_extended",
        "flask_restx",
        "flask_cors",
        "marshmallow",
        "werkzeug",
        "sqlalchemy",
    ]

    dev_packages = [
        "pytest",
        "black",
        "flake8",
        "isort",
        "pre_commit",
        "python_dotenv",
    ]

    missing_required = []
    missing_dev = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing_required.append(package)

    for package in dev_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} (dev)")
        except ImportError:
            print(f"   ⚠️  {package} (dev, missing)")
            missing_dev.append(package)

    if missing_required:
        print(f"   ❌ Missing required packages: {', '.join(missing_required)}")
        print("      Install with: pip install -r requirements.txt")
        return False

    if missing_dev:
        print(f"   ⚠️  Missing dev packages: {', '.join(missing_dev)}")
        print("      Install with: pip install -r requirements/development.txt")

    return True


def check_environment_file():
    """Check if .env file exists and has required variables."""
    print("⚙️  Checking environment configuration...")

    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists():
        print("   ⚠️  .env file not found")
        if env_example.exists():
            print("      Copy .env.example to .env and update the values")
        return False

    print("   ✅ .env file exists")

    # Check for required environment variables
    required_vars = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "FLASK_CONFIG",
    ]

    # Load .env file
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"   ⚠️  Missing environment variables: {', '.join(missing_vars)}")
            return False

        print("   ✅ Required environment variables are set")
        return True

    except ImportError:
        print("   ⚠️  python-dotenv not installed, cannot validate .env file")
        return False


def check_database():
    """Check database configuration."""
    print("🗄️  Checking database configuration...")

    try:
        from app import create_app
        from app.extensions import db

        app = create_app("development")
        with app.app_context():
            # Try to connect to database
            db.engine.execute("SELECT 1")
            print("   ✅ Database connection successful")

            # Check if tables exist
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if tables:
                print(f"   ✅ Database has {len(tables)} tables")
            else:
                print("   ⚠️  Database has no tables - run: python scripts/init_db.py")

            return True

    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False


def check_directories():
    """Check if required directories exist."""
    print("📁 Checking directories...")

    required_dirs = [
        "logs",
        "profiles",
        "uploads",
        "temp",
        "migrations",
        "tests",
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ (missing)")
            all_exist = False

    return all_exist


def check_git_hooks():
    """Check if pre-commit hooks are installed."""
    print("🔧 Checking Git hooks...")

    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("   ⚠️  Not a Git repository")
        return False

    pre_commit_hook = git_dir / "hooks" / "pre-commit"
    if pre_commit_hook.exists():
        print("   ✅ Pre-commit hooks installed")
        return True
    else:
        print("   ⚠️  Pre-commit hooks not installed")
        print("      Install with: pre-commit install")
        return False


def main():
    """Main validation function."""
    print("🔍 Flask API Template - Development Environment Validation")
    print("=" * 60)

    checks = [
        check_python_version,
        check_virtual_environment,
        check_dependencies,
        check_environment_file,
        check_database,
        check_directories,
        check_git_hooks,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Error during check: {e}")
            results.append(False)
        print()

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 60)
    print(f"📊 Validation Summary: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Development environment is ready!")
        print("🚀 Start developing with: make run-dev")
    else:
        print("⚠️  Some issues found. Please address them before developing.")
        print("💡 Run: ./scripts/setup_dev.sh to fix common issues")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
