"""
WSGI entry point for Flask API Template.

This module provides the WSGI application object for production deployment.
"""

import os
from app import create_app

# Get configuration from environment variable
config_name = os.environ.get('FLASK_CONFIG', 'production')

# Create application instance
application = create_app(config_name)

if __name__ == "__main__":
    application.run()