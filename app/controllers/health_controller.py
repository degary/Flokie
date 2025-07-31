"""
Health Check Controller Module

This module provides REST API endpoints for application health monitoring
including application status, database connectivity, and system resource monitoring.
"""

import logging
import os
import psutil
import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

from app.extensions import db

logger = logging.getLogger(__name__)

# Create health check blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/v1/health')


def get_database_status():
    """
    Check database connectivity and status.
    
    Returns:
        dict: Database status information
    """
    try:
        start_time = time.time()
        
        # Test database connection with a simple query
        result = db.session.execute(text('SELECT 1'))
        result.fetchone()
        
        response_time = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
        
        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'connection_pool': {
                'size': db.engine.pool.size(),
                'checked_in': db.engine.pool.checkedin(),
                'checked_out': db.engine.pool.checkedout(),
                'overflow': db.engine.pool.overflow(),
                'invalid': db.engine.pool.invalid()
            },
            'database_url': db.engine.url.database,
            'driver': db.engine.url.drivername
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }


def get_system_resources():
    """
    Get system resource usage information.
    
    Returns:
        dict: System resource information
    """
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_info = {
            'total_mb': round(memory.total / 1024 / 1024, 2),
            'available_mb': round(memory.available / 1024 / 1024, 2),
            'used_mb': round(memory.used / 1024 / 1024, 2),
            'percent': memory.percent
        }
        
        # Get disk usage for the current directory
        disk = psutil.disk_usage('.')
        disk_info = {
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
            'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
            'percent': round((disk.used / disk.total) * 100, 2)
        }
        
        # Get process information
        process = psutil.Process()
        process_info = {
            'pid': process.pid,
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads(),
            'create_time': datetime.fromtimestamp(process.create_time(), tz=timezone.utc).isoformat()
        }
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count
            },
            'memory': memory_info,
            'disk': disk_info,
            'process': process_info
        }
        
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        return {
            'error': str(e)
        }


def get_application_info():
    """
    Get application information and configuration.
    
    Returns:
        dict: Application information
    """
    try:
        return {
            'name': 'Flask API Template',
            'version': '1.0.0',
            'environment': current_app.config.get('ENV', 'unknown'),
            'debug': current_app.config.get('DEBUG', False),
            'testing': current_app.config.get('TESTING', False),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'flask_version': current_app.__class__.__module__.split('.')[0],
            'uptime_seconds': time.time() - psutil.Process().create_time(),
            'timezone': str(datetime.now().astimezone().tzinfo),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Application info check failed: {e}")
        return {
            'error': str(e)
        }


@health_bp.route('', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON: Basic application health status
        
    Status Codes:
        200: Application is healthy
        503: Application is unhealthy
    """
    logger.debug("Basic health check request received")
    
    try:
        # Get basic application info
        app_info = get_application_info()
        
        # Check database connectivity
        db_status = get_database_status()
        
        # Determine overall health status
        is_healthy = db_status['status'] == 'healthy'
        status_code = 200 if is_healthy else 503
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'application': {
                'name': app_info.get('name'),
                'version': app_info.get('version'),
                'environment': app_info.get('environment')
            },
            'database': {
                'status': db_status['status'],
                'response_time_ms': db_status.get('response_time_ms')
            }
        }
        
        if not is_healthy:
            response['errors'] = []
            if db_status['status'] != 'healthy':
                response['errors'].append({
                    'component': 'database',
                    'message': db_status.get('error', 'Database connectivity issue')
                })
        
        logger.debug(f"Health check completed with status: {response['status']}")
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'Health check failed due to server error'
        }), 503


@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check endpoint with comprehensive system information.
    
    Returns:
        JSON: Detailed application and system health status
        
    Status Codes:
        200: Application is healthy
        503: Application is unhealthy
    """
    logger.debug("Detailed health check request received")
    
    try:
        # Get all health information
        app_info = get_application_info()
        db_status = get_database_status()
        system_resources = get_system_resources()
        
        # Determine overall health status
        is_healthy = (
            db_status['status'] == 'healthy' and
            'error' not in system_resources and
            'error' not in app_info
        )
        
        status_code = 200 if is_healthy else 503
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'application': app_info,
            'database': db_status,
            'system': system_resources,
            'checks': {
                'database_connectivity': db_status['status'] == 'healthy',
                'system_resources_available': 'error' not in system_resources,
                'application_info_available': 'error' not in app_info
            }
        }
        
        # Add error details if unhealthy
        if not is_healthy:
            response['errors'] = []
            
            if db_status['status'] != 'healthy':
                response['errors'].append({
                    'component': 'database',
                    'message': db_status.get('error', 'Database connectivity issue')
                })
            
            if 'error' in system_resources:
                response['errors'].append({
                    'component': 'system_resources',
                    'message': system_resources['error']
                })
            
            if 'error' in app_info:
                response['errors'].append({
                    'component': 'application_info',
                    'message': app_info['error']
                })
        
        logger.debug(f"Detailed health check completed with status: {response['status']}")
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'Detailed health check failed due to server error'
        }), 503


@health_bp.route('/database', methods=['GET'])
def database_health_check():
    """
    Database-specific health check endpoint.
    
    Returns:
        JSON: Database connectivity and performance information
        
    Status Codes:
        200: Database is healthy
        503: Database is unhealthy
    """
    logger.debug("Database health check request received")
    
    try:
        db_status = get_database_status()
        
        is_healthy = db_status['status'] == 'healthy'
        status_code = 200 if is_healthy else 503
        
        response = {
            'status': db_status['status'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': db_status
        }
        
        if not is_healthy:
            response['error'] = db_status.get('error', 'Database connectivity issue')
        
        logger.debug(f"Database health check completed with status: {response['status']}")
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'Database health check failed due to server error'
        }), 503


@health_bp.route('/system', methods=['GET'])
def system_health_check():
    """
    System resources health check endpoint.
    
    Returns:
        JSON: System resource usage and performance information
        
    Status Codes:
        200: System resources are healthy
        503: System resources are unhealthy
    """
    logger.debug("System health check request received")
    
    try:
        system_resources = get_system_resources()
        
        # Define health thresholds
        cpu_threshold = 90.0  # CPU usage percentage
        memory_threshold = 90.0  # Memory usage percentage
        disk_threshold = 95.0  # Disk usage percentage
        
        # Check if system is healthy based on thresholds
        is_healthy = True
        warnings = []
        
        if 'error' in system_resources:
            is_healthy = False
        else:
            # Check CPU usage
            if system_resources['cpu']['percent'] > cpu_threshold:
                is_healthy = False
                warnings.append(f"High CPU usage: {system_resources['cpu']['percent']}%")
            
            # Check memory usage
            if system_resources['memory']['percent'] > memory_threshold:
                is_healthy = False
                warnings.append(f"High memory usage: {system_resources['memory']['percent']}%")
            
            # Check disk usage
            if system_resources['disk']['percent'] > disk_threshold:
                is_healthy = False
                warnings.append(f"High disk usage: {system_resources['disk']['percent']}%")
        
        status_code = 200 if is_healthy else 503
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': system_resources,
            'thresholds': {
                'cpu_percent': cpu_threshold,
                'memory_percent': memory_threshold,
                'disk_percent': disk_threshold
            }
        }
        
        if warnings:
            response['warnings'] = warnings
        
        if 'error' in system_resources:
            response['error'] = system_resources['error']
        
        logger.debug(f"System health check completed with status: {response['status']}")
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'System health check failed due to server error'
        }), 503


@health_bp.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint for container orchestration.
    
    This endpoint checks if the application is ready to serve traffic.
    It performs essential checks like database connectivity.
    
    Returns:
        JSON: Application readiness status
        
    Status Codes:
        200: Application is ready
        503: Application is not ready
    """
    logger.debug("Readiness check request received")
    
    try:
        # Check database connectivity (essential for readiness)
        db_status = get_database_status()
        
        is_ready = db_status['status'] == 'healthy'
        status_code = 200 if is_ready else 503
        
        response = {
            'ready': is_ready,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {
                'database': db_status['status'] == 'healthy'
            }
        }
        
        if not is_ready:
            response['message'] = 'Application is not ready to serve traffic'
            response['errors'] = []
            
            if db_status['status'] != 'healthy':
                response['errors'].append({
                    'component': 'database',
                    'message': db_status.get('error', 'Database not accessible')
                })
        else:
            response['message'] = 'Application is ready to serve traffic'
        
        logger.debug(f"Readiness check completed: ready={is_ready}")
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'ready': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'Readiness check failed due to server error',
            'error': str(e)
        }), 503


@health_bp.route('/liveness', methods=['GET'])
def liveness_check():
    """
    Liveness check endpoint for container orchestration.
    
    This endpoint checks if the application is alive and running.
    It performs minimal checks to avoid false positives.
    
    Returns:
        JSON: Application liveness status
        
    Status Codes:
        200: Application is alive
        503: Application is not alive
    """
    logger.debug("Liveness check request received")
    
    try:
        # Basic liveness check - just verify the application is responding
        response = {
            'alive': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'Application is alive and responding',
            'uptime_seconds': round(time.time() - psutil.Process().create_time(), 2)
        }
        
        logger.debug("Liveness check completed: alive=True")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'alive': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'Application liveness check failed',
            'error': str(e)
        }), 503


# Error handlers for the blueprint
@health_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Health check endpoint not found',
        'code': 'NOT_FOUND'
    }), 404


@health_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405


@health_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error in health controller: {error}")
    return jsonify({
        'status': 'unhealthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'error': 'Health check failed due to internal server error'
    }), 503