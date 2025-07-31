#!/usr/bin/env python3
"""
Development server entry point for Flask API Template.

This script is used to run the application in development mode.
"""

import os
from app import create_app

# Get configuration from environment variable
config_name = os.environ.get('FLASK_CONFIG', 'development')

# Create application instance
app = create_app(config_name)

if __name__ == '__main__':
    # Run development server
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=app.config.get('DEBUG', False),
        use_reloader=os.environ.get('FLASK_USE_RELOADER', 'true').lower() == 'true'
    )