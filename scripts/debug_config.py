#!/usr/bin/env python3
"""
Debug configuration utilities for Flask API Template.

This module provides debugging and profiling utilities for development.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_debug_toolbar(app):
    """Set up Flask Debug Toolbar for development."""
    try:
        from flask_debugtoolbar import DebugToolbarExtension

        # Configure debug toolbar
        app.config["DEBUG_TB_ENABLED"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        app.config["DEBUG_TB_PROFILER_ENABLED"] = True
        app.config["DEBUG_TB_TEMPLATE_EDITOR_ENABLED"] = True

        toolbar = DebugToolbarExtension(app)
        print("✅ Flask Debug Toolbar enabled")
        return toolbar

    except ImportError:
        print("⚠️  Flask Debug Toolbar not installed")
        print("   Install with: pip install flask-debugtoolbar")
        return None


def setup_profiling(app):
    """Set up request profiling for development."""
    if not app.config.get("ENABLE_PROFILING", False):
        return

    try:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        # Add profiler middleware
        app.wsgi_app = ProfilerMiddleware(
            app.wsgi_app,
            restrictions=[30],  # Show top 30 functions
            profile_dir="./profiles",
            filename_format="{method}.{path}.{elapsed:.0f}ms.{time:.0f}.prof",
        )

        # Create profiles directory
        profiles_dir = Path("./profiles")
        profiles_dir.mkdir(exist_ok=True)

        print("✅ Request profiling enabled")
        print(f"   Profiles will be saved to: {profiles_dir.absolute()}")

    except Exception as e:
        print(f"⚠️  Error setting up profiling: {e}")


def setup_memory_monitoring(app):
    """Set up memory monitoring for development."""
    try:
        import threading
        import time

        import psutil

        def monitor_memory():
            """Monitor memory usage in background thread."""
            process = psutil.Process()
            while True:
                try:
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024

                    # Log memory usage if it exceeds threshold
                    if memory_mb > 100:  # 100MB threshold
                        app.logger.warning(f"High memory usage: {memory_mb:.1f}MB")

                    time.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    app.logger.error(f"Memory monitoring error: {e}")
                    break

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()

        print("✅ Memory monitoring enabled")

    except ImportError:
        print("⚠️  psutil not installed for memory monitoring")
        print("   Install with: pip install psutil")


def setup_request_logging(app):
    """Set up detailed request logging for development."""
    import logging
    import time

    from flask import g, request

    # Create request logger
    request_logger = logging.getLogger("flask.request")
    request_logger.setLevel(logging.DEBUG)

    # Add file handler for request logs
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)

    handler = logging.FileHandler(log_dir / "requests.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(method)s %(path)s - %(status)s - %(duration)sms - %(remote_addr)s"
    )
    handler.setFormatter(formatter)
    request_logger.addHandler(handler)

    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        duration = int((time.time() - g.start_time) * 1000)

        # Log request details
        request_logger.info(
            "",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration": duration,
                "remote_addr": request.remote_addr,
            },
        )

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration}ms"

        return response

    print("✅ Request logging enabled")
    print(f"   Request logs: {log_dir / 'requests.log'}")


def configure_development_app(app):
    """Configure app with all development tools."""
    print("🔧 Configuring development tools...")

    # Set up debug toolbar
    setup_debug_toolbar(app)

    # Set up profiling
    setup_profiling(app)

    # Set up memory monitoring
    setup_memory_monitoring(app)

    # Set up request logging
    setup_request_logging(app)

    # Add development routes
    @app.route("/dev/info")
    def dev_info():
        """Development information endpoint."""
        import platform

        import flask

        info = {
            "python_version": platform.python_version(),
            "flask_version": flask.__version__,
            "config": app.config["ENV"],
            "debug": app.debug,
            "testing": app.testing,
            "database_uri": app.config.get("SQLALCHEMY_DATABASE_URI", "Not configured"),
            "secret_key_set": bool(app.config.get("SECRET_KEY")),
            "jwt_secret_key_set": bool(app.config.get("JWT_SECRET_KEY")),
        }

        return info

    @app.route("/dev/routes")
    def dev_routes():
        """List all application routes."""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(
                {
                    "endpoint": rule.endpoint,
                    "methods": list(rule.methods),
                    "path": str(rule),
                }
            )

        return {"routes": sorted(routes, key=lambda x: x["path"])}

    print("✅ Development configuration complete")
    return app


if __name__ == "__main__":
    # Example usage
    from app import create_app

    app = create_app("development")
    app = configure_development_app(app)

    print("🚀 Starting development server with debug tools...")
    app.run(debug=True, host="0.0.0.0", port=5000)
