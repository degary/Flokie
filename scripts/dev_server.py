#!/usr/bin/env python3
"""
Enhanced development server script for Flask API Template.

This script provides additional development features like:
- Environment variable loading
- Database initialization
- Development middleware setup
- Hot reloading configuration
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("   Consider copying .env.example to .env and updating the values")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

from app import create_app
from app.extensions import db


def setup_development_environment():
    """Set up development-specific environment variables."""
    # Set default development environment variables
    dev_defaults = {
        "FLASK_CONFIG": "development",
        "FLASK_DEBUG": "true",
        "FLASK_HOST": "0.0.0.0",
        "FLASK_PORT": "5000",
        "FLASK_USE_RELOADER": "true",
        "FLASK_USE_DEBUGGER": "true",
        "LOG_LEVEL": "DEBUG",
        "ERROR_INCLUDE_DETAILS": "true",
        "ERROR_INCLUDE_TRACEBACK": "true",
        "ERROR_MONITORING_ENABLED": "true",
    }

    for key, default_value in dev_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value


def initialize_database_if_needed(app):
    """Initialize database if it doesn't exist."""
    try:
        with app.app_context():
            # Check if database exists and has tables
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if not tables:
                print("🗄️  Database appears to be empty. Initializing...")
                db.create_all()
                print("✅ Database initialized successfully")
            else:
                print(f"✅ Database found with {len(tables)} tables")

    except Exception as e:
        print(f"⚠️  Database initialization check failed: {e}")
        print("   You may need to run: python scripts/init_db.py")


def print_development_info(app):
    """Print useful development information."""
    config_name = os.environ.get("FLASK_CONFIG", "development")
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    print("\n" + "=" * 60)
    print("🚀 Flask API Template - Development Server")
    print("=" * 60)
    print(f"📋 Configuration: {config_name}")
    print(f"🌐 Server URL: http://{host}:{port}")
    print(f"🐛 Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(
        f"🔄 Auto-reload: {'Enabled' if os.environ.get('FLASK_USE_RELOADER', 'true').lower() == 'true' else 'Disabled'}"
    )
    print(f"📊 Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("\n📚 Available endpoints:")
    print("   • Health Check: GET /health")
    print("   • API Documentation: GET /docs")
    print("   • Authentication: POST /auth/login")
    print("   • User Management: GET /users")
    print("\n🛠️  Development commands:")
    print("   • Format code: make format")
    print("   • Run tests: make test")
    print("   • Check code quality: make lint")
    print("=" * 60)
    print("Press Ctrl+C to stop the server\n")


def main():
    """Main development server entry point."""
    print("🔧 Setting up development environment...")

    # Setup development environment
    setup_development_environment()

    # Get configuration
    config_name = os.environ.get("FLASK_CONFIG", "development")

    # Create application
    print(f"🏗️  Creating Flask application with config: {config_name}")
    app = create_app(config_name)

    # Initialize database if needed
    initialize_database_if_needed(app)

    # Print development information
    print_development_info(app)

    # Start development server
    try:
        app.run(
            host=os.environ.get("FLASK_HOST", "0.0.0.0"),
            port=int(os.environ.get("FLASK_PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
            use_reloader=os.environ.get("FLASK_USE_RELOADER", "true").lower() == "true",
            use_debugger=os.environ.get("FLASK_USE_DEBUGGER", "true").lower() == "true",
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"❌ Error starting development server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
