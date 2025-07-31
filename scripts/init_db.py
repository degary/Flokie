#!/usr/bin/env python3
"""
Database initialization script for Flask API Template.

This script initializes the database migration system and creates
the initial migration files for the application.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_migrate import init, migrate, upgrade
from app import create_app
from app.extensions import db
from app.models import User  # Import all models to ensure they're registered

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """
    Initialize database migration system.
    
    This function:
    1. Initializes Flask-Migrate if not already initialized
    2. Creates initial migration files
    3. Applies migrations to create database tables
    """
    # Create Flask app instance
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    
    with app.app_context():
        try:
            # Check if migrations directory exists
            migrations_dir = project_root / 'migrations'
            
            if not migrations_dir.exists():
                logger.info("Initializing Flask-Migrate...")
                init()
                logger.info("Flask-Migrate initialized successfully")
            else:
                logger.info("Flask-Migrate already initialized")
            
            # Create initial migration if no migrations exist
            versions_dir = migrations_dir / 'versions'
            if not versions_dir.exists() or not list(versions_dir.glob('*.py')):
                logger.info("Creating initial migration...")
                migrate(message='Initial migration with User model')
                logger.info("Initial migration created successfully")
            else:
                logger.info("Migrations already exist")
            
            # Apply migrations to create/update database tables
            logger.info("Applying migrations to database...")
            upgrade()
            logger.info("Database migrations applied successfully")
            
            # Verify database setup
            verify_database_setup()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise


def verify_database_setup():
    """
    Verify that database tables were created correctly.
    """
    try:
        # Check if User table exists and can be queried
        user_count = User.count()
        logger.info(f"Database verification successful. User table exists with {user_count} records.")
        
        # Test creating a sample user (will be rolled back)
        from app.extensions import db
        
        test_user = User(
            username='test_user',
            email='test@example.com',
            password='test_password123'
        )
        
        # Validate the user without saving
        test_user.validate()
        logger.info("User model validation test passed")
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise


def create_admin_user():
    """
    Create an admin user if one doesn't exist.
    This is useful for initial setup.
    """
    try:
        # Check if admin user already exists
        admin_user = User.get_by_username('admin')
        
        if not admin_user:
            logger.info("Creating default admin user...")
            
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='admin123',  # Should be changed in production
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True,
                is_verified=True
            )
            
            admin_user.save()
            logger.info("Default admin user created successfully")
            logger.warning("IMPORTANT: Change the default admin password in production!")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise


def reset_database():
    """
    Reset database by dropping all tables and recreating them.
    WARNING: This will delete all data!
    """
    logger.warning("RESETTING DATABASE - ALL DATA WILL BE LOST!")
    
    try:
        # Drop all tables
        db.drop_all()
        logger.info("All database tables dropped")
        
        # Recreate all tables
        db.create_all()
        logger.info("All database tables recreated")
        
        # Create admin user
        create_admin_user()
        
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database initialization script')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset database (WARNING: deletes all data)')
    parser.add_argument('--create-admin', action='store_true',
                       help='Create default admin user')
    
    args = parser.parse_args()
    
    # Create Flask app instance
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    
    with app.app_context():
        if args.reset:
            reset_database()
        else:
            init_database()
            
        if args.create_admin:
            create_admin_user()
    
    logger.info("Database initialization script completed successfully")