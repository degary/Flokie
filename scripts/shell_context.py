#!/usr/bin/env python3
"""
Flask shell context processor for development.

This script sets up a convenient shell environment with commonly used
objects pre-imported for interactive development and debugging.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv

    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from app import create_app
from app.extensions import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.user_service import UserService


def create_shell_context():
    """Create shell context with useful objects."""
    # Set development config if not specified
    if not os.environ.get("FLASK_CONFIG"):
        os.environ["FLASK_CONFIG"] = "development"

    app = create_app()

    with app.app_context():
        # Create some sample data for development
        def create_sample_data():
            """Create sample data for development."""
            try:
                # Check if admin user exists
                admin = User.query.filter_by(username="admin").first()
                if not admin:
                    print("Creating sample admin user...")
                    admin_data = {
                        "username": "admin",
                        "email": "admin@example.com",
                        "password": "admin123",
                        "first_name": "Admin",
                        "last_name": "User",
                    }
                    admin = AuthService.register(**admin_data)
                    admin.is_admin = True
                    admin.is_verified = True
                    db.session.commit()
                    print(f"✅ Created admin user: {admin.username}")

                # Check if test user exists
                test_user = User.query.filter_by(username="testuser").first()
                if not test_user:
                    print("Creating sample test user...")
                    user_data = {
                        "username": "testuser",
                        "email": "test@example.com",
                        "password": "test123",
                        "first_name": "Test",
                        "last_name": "User",
                    }
                    test_user = AuthService.register(**user_data)
                    test_user.is_verified = True
                    db.session.commit()
                    print(f"✅ Created test user: {test_user.username}")

                return admin, test_user

            except Exception as e:
                print(f"⚠️  Error creating sample data: {e}")
                return None, None

        def reset_database():
            """Reset database (drop and recreate all tables)."""
            print("⚠️  Resetting database...")
            db.drop_all()
            db.create_all()
            print("✅ Database reset complete")
            return create_sample_data()

        def show_users():
            """Show all users in the database."""
            users = User.query.all()
            if not users:
                print("No users found in database")
                return

            print(f"\n📋 Found {len(users)} users:")
            print("-" * 80)
            print(
                f"{'ID':<4} {'Username':<15} {'Email':<25} {'Name':<20} {'Admin':<6} {'Active':<6}"
            )
            print("-" * 80)
            for user in users:
                name = f"{user.first_name} {user.last_name}".strip()
                print(
                    f"{user.id:<4} {user.username:<15} {user.email:<25} {name:<20} {'Yes' if user.is_admin else 'No':<6} {'Yes' if user.is_active else 'No':<6}"
                )
            print("-" * 80)

        def login_user(username_or_email, password):
            """Helper function to test user login."""
            try:
                result = AuthService.login(username_or_email, password)
                print(f"✅ Login successful for: {result['user']['username']}")
                print(f"🔑 Access token: {result['access_token'][:50]}...")
                return result
            except Exception as e:
                print(f"❌ Login failed: {e}")
                return None

        # Create shell context dictionary
        context = {
            # Flask objects
            "app": app,
            "db": db,
            # Models
            "User": User,
            # Services
            "AuthService": AuthService,
            "UserService": UserService,
            # Helper functions
            "create_sample_data": create_sample_data,
            "reset_database": reset_database,
            "show_users": show_users,
            "login_user": login_user,
            # Common imports for convenience
            "datetime": __import__("datetime"),
            "json": __import__("json"),
        }

        return context


def main():
    """Main entry point for interactive shell."""
    print("🐚 Flask API Template - Interactive Shell")
    print("=" * 50)

    context = create_shell_context()

    print("📦 Available objects:")
    for name, obj in context.items():
        if callable(obj):
            print(
                f"   • {name}() - {obj.__doc__.split('.')[0] if obj.__doc__ else 'Function'}"
            )
        else:
            print(f"   • {name} - {type(obj).__name__}")

    print("\n🚀 Quick start commands:")
    print("   • show_users() - Display all users")
    print("   • create_sample_data() - Create sample users")
    print("   • reset_database() - Reset database with sample data")
    print("   • login_user('admin', 'admin123') - Test login")
    print("\n" + "=" * 50)

    # Start IPython shell if available, otherwise use standard Python shell
    try:
        from IPython import start_ipython

        start_ipython(argv=[], user_ns=context)
    except ImportError:
        import code

        code.interact(local=context)


if __name__ == "__main__":
    main()
