"""
Logging and monitoring middleware for request/response logging and performance monitoring.

This middleware provides structured logging, request/response tracking, and performance
monitoring capabilities for the Flask API.
"""

import json
import logging
import time
from datetime import datetime

from flask import current_app, g, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Logging middleware class for structured request/response logging.
    """

    def __init__(self, app=None):
        """
        Initialize logging middleware.

        Args:
            app (Flask, optional): Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize middleware with Flask application.

        Args:
            app (Flask): Flask application instance
        """
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
        logger.info("Logging middleware initialized")

    def before_request(self):
        """
        Process request before route handler execution.
        Records request start time and logs request details.
        """
        # Record request start time
        g.start_time = time.time()
        g.request_id = self._generate_request_id()

        # Log request details
        self._log_request()

    def after_request(self, response):
        """
        Process response after route handler execution.
        Logs response details and performance metrics.

        Args:
            response: Flask response object

        Returns:
            Flask response object
        """
        # Calculate request duration
        duration = time.time() - getattr(g, "start_time", time.time())

        # Log response details
        self._log_response(response, duration)

        # Add request ID to response headers
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id

        return response

    def teardown_request(self, exception=None):
        """
        Clean up after request processing.

        Args:
            exception: Exception that occurred during request processing
        """
        if exception:
            self._log_exception(exception)

    def _generate_request_id(self):
        """
        Generate unique request ID.

        Returns:
            str: Unique request identifier
        """
        import uuid

        return str(uuid.uuid4())[:8]

    def _log_request(self):
        """
        Log structured request information.
        """
        # Skip logging for health check and static files
        if self._should_skip_logging():
            return

        request_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(g, "request_id", "unknown"),
            "method": request.method,
            "url": request.url,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "content_type": request.content_type,
            "content_length": request.content_length,
            "args": dict(request.args),
            "form": dict(request.form) if request.form else None,
            "headers": dict(request.headers),
        }

        # Remove sensitive headers
        self._sanitize_headers(request_data["headers"])

        # Log JSON body for POST/PUT requests (if not too large)
        if request.method in ["POST", "PUT", "PATCH"] and request.is_json:
            try:
                if (
                    request.content_length and request.content_length < 10000
                ):  # 10KB limit
                    request_data["json"] = request.get_json()
            except Exception as e:
                request_data["json_error"] = str(e)

        logger.info(f"[INFO] REQUEST: {json.dumps(request_data, default=str)}")

    def _log_response(self, response, duration):
        """
        Log structured response information.

        Args:
            response: Flask response object
            duration (float): Request processing duration in seconds
        """
        # Skip logging for health check and static files
        if self._should_skip_logging():
            return

        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(g, "request_id", "unknown"),
            "status_code": response.status_code,
            "status": response.status,
            "content_type": response.content_type,
            "content_length": response.content_length,
            "duration_ms": round(duration * 1000, 2),
            "headers": dict(response.headers),
        }

        # Remove sensitive headers
        self._sanitize_headers(response_data["headers"])

        # Log response body for errors (if not too large)
        if response.status_code >= 400:
            try:
                if (
                    response.content_length and response.content_length < 5000
                ):  # 5KB limit
                    response_data["data"] = response.get_data(as_text=True)
            except Exception as e:
                response_data["data_error"] = str(e)

        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error(f"[ERROR] RESPONSE: {json.dumps(response_data, default=str)}")
        elif response.status_code >= 400:
            logger.warning(
                f"[WARNING] RESPONSE: {json.dumps(response_data, default=str)}"
            )
        else:
            logger.info(f"[INFO] RESPONSE: {json.dumps(response_data, default=str)}")

    def _log_exception(self, exception):
        """
        Log exception information.

        Args:
            exception: Exception that occurred
        """
        from flask import has_request_context

        exception_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(g, "request_id", "unknown")
            if has_request_context()
            else "no-request",
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        }

        # Only add request-specific data if we're in a request context
        if has_request_context():
            exception_data.update(
                {
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                }
            )
        else:
            exception_data.update(
                {"method": "N/A", "path": "N/A", "remote_addr": "N/A"}
            )

        if isinstance(exception, HTTPException):
            exception_data["status_code"] = exception.code
            logger.warning(
                f"[WARNING] HTTP_EXCEPTION: {json.dumps(exception_data, default=str)}"
            )
        else:
            logger.error(
                f"[ERROR] EXCEPTION: {json.dumps(exception_data, default=str)}",
                exc_info=True,
            )

    def _should_skip_logging(self):
        """
        Determine if logging should be skipped for current request.

        Returns:
            bool: True if logging should be skipped
        """
        skip_paths = ["/health", "/favicon.ico", "/static/"]
        return any(request.path.startswith(path) for path in skip_paths)

    def _sanitize_headers(self, headers):
        """
        Remove sensitive information from headers.

        Args:
            headers (dict): Headers dictionary to sanitize
        """
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"
            # Handle case-insensitive header names
            for key in list(headers.keys()):
                if key.lower() == header:
                    headers[key] = "[REDACTED]"


class PerformanceMiddleware:
    """
    Performance monitoring middleware for tracking application metrics.
    """

    def __init__(self, app=None):
        """
        Initialize performance middleware.

        Args:
            app (Flask, optional): Flask application instance
        """
        self.app = app
        self.metrics = {
            "request_count": 0,
            "total_duration": 0.0,
            "error_count": 0,
            "slow_requests": 0,
        }
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize middleware with Flask application.

        Args:
            app (Flask): Flask application instance
        """
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        logger.info("Performance middleware initialized")

    def before_request(self):
        """
        Record request start time for performance tracking.
        """
        if not hasattr(g, "start_time"):
            g.start_time = time.time()

    def after_request(self, response):
        """
        Track performance metrics after request processing.

        Args:
            response: Flask response object

        Returns:
            Flask response object
        """
        # Calculate request duration
        duration = time.time() - getattr(g, "start_time", time.time())

        # Update metrics
        self.metrics["request_count"] += 1
        self.metrics["total_duration"] += duration

        # Track errors
        if response.status_code >= 400:
            self.metrics["error_count"] += 1

        # Track slow requests (> 1 second)
        if duration > 1.0:
            self.metrics["slow_requests"] += 1
            logger.warning(
                f"[WARNING] Slow request detected: {request.path} took {duration:.2f}s"
            )

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Log performance warning for very slow requests
        if duration > 5.0:
            logger.error(
                f"[ERROR] Very slow request: {request.method} {request.path} took {duration:.2f}s"
            )

        return response

    def get_metrics(self):
        """
        Get current performance metrics.

        Returns:
            dict: Performance metrics
        """
        avg_duration = (
            self.metrics["total_duration"] / self.metrics["request_count"]
            if self.metrics["request_count"] > 0
            else 0
        )

        return {
            "request_count": self.metrics["request_count"],
            "average_duration_ms": round(avg_duration * 1000, 2),
            "error_count": self.metrics["error_count"],
            "error_rate": (
                self.metrics["error_count"] / self.metrics["request_count"]
                if self.metrics["request_count"] > 0
                else 0
            ),
            "slow_requests": self.metrics["slow_requests"],
            "slow_request_rate": (
                self.metrics["slow_requests"] / self.metrics["request_count"]
                if self.metrics["request_count"] > 0
                else 0
            ),
        }

    def reset_metrics(self):
        """
        Reset performance metrics.
        """
        self.metrics = {
            "request_count": 0,
            "total_duration": 0.0,
            "error_count": 0,
            "slow_requests": 0,
        }
        logger.info("[INFO] Performance metrics reset")


# Create middleware instances
logging_middleware = LoggingMiddleware()
performance_middleware = PerformanceMiddleware()
