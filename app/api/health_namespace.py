"""
Health Check API namespace for Flask-RESTX documentation.

This module defines the health check API endpoints with comprehensive
documentation using Flask-RESTX decorators and models.
"""

from flask_restx import Namespace, Resource

from app.api.models import (
    detailed_health_status_model,
    health_status_model,
    liveness_status_model,
    readiness_status_model,
)

# Create health check namespace
health_ns = Namespace("health", description="Health check operations", path="/health")

# Add models to namespace
health_ns.models[health_status_model.name] = health_status_model
health_ns.models[detailed_health_status_model.name] = detailed_health_status_model
health_ns.models[readiness_status_model.name] = readiness_status_model
health_ns.models[liveness_status_model.name] = liveness_status_model


@health_ns.route("")
class HealthCheckResource(Resource):
    @health_ns.doc("basic_health_check")
    @health_ns.marshal_with(
        health_status_model, code=200, description="Application is healthy"
    )
    @health_ns.response(503, "Application is unhealthy", health_status_model)
    def get(self):
        """
        Basic health check

        Perform a basic health check of the application.
        Checks application status and database connectivity.
        Returns 200 if healthy, 503 if unhealthy.
        """
        # This is handled by the actual controller
        pass


@health_ns.route("/detailed")
class DetailedHealthCheckResource(Resource):
    @health_ns.doc("detailed_health_check")
    @health_ns.marshal_with(
        detailed_health_status_model, code=200, description="Application is healthy"
    )
    @health_ns.response(503, "Application is unhealthy", detailed_health_status_model)
    def get(self):
        """
        Detailed health check

        Perform a comprehensive health check with detailed system information.
        Includes application info, database status, and system resource usage.
        Returns 200 if healthy, 503 if unhealthy.
        """
        # This is handled by the actual controller
        pass


@health_ns.route("/database")
class DatabaseHealthCheckResource(Resource):
    @health_ns.doc("database_health_check")
    @health_ns.marshal_with(
        health_status_model, code=200, description="Database is healthy"
    )
    @health_ns.response(503, "Database is unhealthy", health_status_model)
    def get(self):
        """
        Database health check

        Check database connectivity and performance.
        Tests database connection and measures response time.
        Returns 200 if healthy, 503 if unhealthy.
        """
        # This is handled by the actual controller
        pass


@health_ns.route("/system")
class SystemHealthCheckResource(Resource):
    @health_ns.doc("system_health_check")
    @health_ns.marshal_with(
        detailed_health_status_model,
        code=200,
        description="System resources are healthy",
    )
    @health_ns.response(
        503, "System resources are unhealthy", detailed_health_status_model
    )
    def get(self):
        """
        System resources health check

        Check system resource usage and performance.
        Monitors CPU, memory, and disk usage against defined thresholds.
        Returns 200 if healthy, 503 if unhealthy.
        """
        # This is handled by the actual controller
        pass


@health_ns.route("/readiness")
class ReadinessCheckResource(Resource):
    @health_ns.doc("readiness_check")
    @health_ns.marshal_with(
        readiness_status_model, code=200, description="Application is ready"
    )
    @health_ns.response(503, "Application is not ready", readiness_status_model)
    def get(self):
        """
        Readiness check

        Check if the application is ready to serve traffic.
        Used by container orchestration systems (Kubernetes, Docker Swarm).
        Performs essential checks like database connectivity.
        Returns 200 if ready, 503 if not ready.
        """
        # This is handled by the actual controller
        pass


@health_ns.route("/liveness")
class LivenessCheckResource(Resource):
    @health_ns.doc("liveness_check")
    @health_ns.marshal_with(
        liveness_status_model, code=200, description="Application is alive"
    )
    @health_ns.response(503, "Application is not alive", liveness_status_model)
    def get(self):
        """
        Liveness check

        Check if the application is alive and running.
        Used by container orchestration systems (Kubernetes, Docker Swarm).
        Performs minimal checks to avoid false positives.
        Returns 200 if alive, 503 if not alive.
        """
        # This is handled by the actual controller
        pass
