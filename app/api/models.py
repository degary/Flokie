"""
Flask-RESTX API models for request/response documentation.

This module defines the data models used in API documentation
for request validation and response serialization.
"""

from flask_restx import fields
from app.extensions import api

# Common response models
success_model = api.model('SuccessResponse', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'message': fields.String(description='Success message'),
    'data': fields.Raw(description='Response data')
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.String(required=True, description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

validation_error_model = api.model('ValidationErrorResponse', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.String(required=True, description='Error code'),
    'details': fields.Raw(required=True, description='Validation error details')
})

# User models
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'bio': fields.String(description='User biography'),
    'is_active': fields.Boolean(required=True, description='Whether user is active'),
    'is_verified': fields.Boolean(required=True, description='Whether email is verified'),
    'is_admin': fields.Boolean(required=True, description='Whether user is admin'),
    'created_at': fields.DateTime(required=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(required=True, description='Last update timestamp'),
    'last_login_at': fields.DateTime(description='Last login timestamp')
})

# Authentication models
login_request_model = api.model('LoginRequest', {
    'username_or_email': fields.String(required=True, description='Username or email address'),
    'password': fields.String(required=True, description='User password'),
    'remember_me': fields.Boolean(description='Whether to create longer-lived tokens', default=False)
})

register_request_model = api.model('RegisterRequest', {
    'username': fields.String(required=True, description='Desired username (3-80 characters)'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password (minimum 8 characters)'),
    'first_name': fields.String(description='First name (max 50 characters)'),
    'last_name': fields.String(description='Last name (max 50 characters)')
})

token_model = api.model('Token', {
    'access_token': fields.String(required=True, description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'token_type': fields.String(required=True, description='Token type', default='Bearer'),
    'expires_in': fields.Integer(required=True, description='Token expiration time in seconds')
})

login_response_model = api.model('LoginResponse', {
    'success': fields.Boolean(required=True, description='Login success status'),
    'message': fields.String(required=True, description='Login result message'),
    'data': fields.Nested(api.model('LoginData', {
        'user': fields.Nested(user_model, required=True, description='User information'),
        'tokens': fields.Nested(token_model, required=True, description='Authentication tokens')
    }), required=True, description='Login response data')
})

register_response_model = api.model('RegisterResponse', {
    'success': fields.Boolean(required=True, description='Registration success status'),
    'message': fields.String(required=True, description='Registration result message'),
    'data': fields.Nested(api.model('RegisterData', {
        'user': fields.Nested(user_model, required=True, description='User information'),
        'verification_token': fields.String(description='Email verification token')
    }), required=True, description='Registration response data')
})

refresh_token_response_model = api.model('RefreshTokenResponse', {
    'success': fields.Boolean(required=True, description='Token refresh success status'),
    'message': fields.String(required=True, description='Token refresh result message'),
    'data': fields.Nested(api.model('RefreshTokenData', {
        'access_token': fields.String(required=True, description='New JWT access token'),
        'token_type': fields.String(required=True, description='Token type'),
        'expires_in': fields.Integer(required=True, description='Token expiration time in seconds')
    }), required=True, description='Token refresh response data')
})

password_reset_request_model = api.model('PasswordResetRequest', {
    'email': fields.String(required=True, description='Email address for password reset')
})

password_reset_model = api.model('PasswordReset', {
    'token': fields.String(required=True, description='Password reset token'),
    'new_password': fields.String(required=True, description='New password (minimum 8 characters)')
})

change_password_model = api.model('ChangePassword', {
    'current_password': fields.String(required=True, description='Current password'),
    'new_password': fields.String(required=True, description='New password (minimum 8 characters)')
})

email_verification_model = api.model('EmailVerification', {
    'token': fields.String(required=True, description='Email verification token')
})

# User management models
create_user_request_model = api.model('CreateUserRequest', {
    'username': fields.String(required=True, description='Username (3-80 characters)'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(description='Password (minimum 8 characters, optional)'),
    'first_name': fields.String(description='First name (max 50 characters)'),
    'last_name': fields.String(description='Last name (max 50 characters)'),
    'is_admin': fields.Boolean(description='Whether user should be admin', default=False),
    'is_verified': fields.Boolean(description='Whether email should be pre-verified', default=False)
})

update_user_request_model = api.model('UpdateUserRequest', {
    'username': fields.String(description='Username (3-80 characters)'),
    'email': fields.String(description='Email address'),
    'first_name': fields.String(description='First name (max 50 characters)'),
    'last_name': fields.String(description='Last name (max 50 characters)'),
    'bio': fields.String(description='User biography (max 500 characters)'),
    'is_active': fields.Boolean(description='Whether user is active (admin only)'),
    'is_verified': fields.Boolean(description='Whether email is verified (admin only)'),
    'is_admin': fields.Boolean(description='Whether user is admin (admin only)')
})

user_list_response_model = api.model('UserListResponse', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'data': fields.Nested(api.model('UserListData', {
        'users': fields.List(fields.Nested(user_model), required=True, description='List of users'),
        'pagination': fields.Nested(api.model('Pagination', {
            'page': fields.Integer(required=True, description='Current page number'),
            'per_page': fields.Integer(required=True, description='Items per page'),
            'total': fields.Integer(required=True, description='Total number of items'),
            'pages': fields.Integer(required=True, description='Total number of pages'),
            'has_prev': fields.Boolean(required=True, description='Whether there is a previous page'),
            'has_next': fields.Boolean(required=True, description='Whether there is a next page')
        }), required=True, description='Pagination information')
    }), required=True, description='User list response data')
})

user_response_model = api.model('UserResponse', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'message': fields.String(description='Response message'),
    'data': fields.Nested(api.model('UserData', {
        'user': fields.Nested(user_model, required=True, description='User information')
    }), required=True, description='User response data')
})

set_admin_status_model = api.model('SetAdminStatus', {
    'is_admin': fields.Boolean(required=True, description='Whether user should be admin')
})

user_statistics_model = api.model('UserStatistics', {
    'total_users': fields.Integer(required=True, description='Total number of users'),
    'active_users': fields.Integer(required=True, description='Number of active users'),
    'inactive_users': fields.Integer(required=True, description='Number of inactive users'),
    'verified_users': fields.Integer(required=True, description='Number of verified users'),
    'unverified_users': fields.Integer(required=True, description='Number of unverified users'),
    'admin_users': fields.Integer(required=True, description='Number of admin users'),
    'locked_users': fields.Integer(required=True, description='Number of locked users'),
    'users_created_today': fields.Integer(required=True, description='Users created today'),
    'users_created_this_week': fields.Integer(required=True, description='Users created this week'),
    'users_created_this_month': fields.Integer(required=True, description='Users created this month')
})

user_statistics_response_model = api.model('UserStatisticsResponse', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'data': fields.Nested(api.model('UserStatisticsData', {
        'statistics': fields.Nested(user_statistics_model, required=True, description='User statistics')
    }), required=True, description='User statistics response data')
})

# Health check models
health_status_model = api.model('HealthStatus', {
    'status': fields.String(required=True, description='Health status', enum=['healthy', 'unhealthy']),
    'timestamp': fields.DateTime(required=True, description='Check timestamp'),
    'application': fields.Nested(api.model('ApplicationInfo', {
        'name': fields.String(description='Application name'),
        'version': fields.String(description='Application version'),
        'environment': fields.String(description='Environment name')
    }), description='Application information'),
    'database': fields.Nested(api.model('DatabaseStatus', {
        'status': fields.String(required=True, description='Database status'),
        'response_time_ms': fields.Float(description='Database response time in milliseconds')
    }), description='Database status'),
    'errors': fields.List(fields.Nested(api.model('HealthError', {
        'component': fields.String(required=True, description='Component name'),
        'message': fields.String(required=True, description='Error message')
    })), description='Health check errors')
})

detailed_health_status_model = api.model('DetailedHealthStatus', {
    'status': fields.String(required=True, description='Health status', enum=['healthy', 'unhealthy']),
    'timestamp': fields.DateTime(required=True, description='Check timestamp'),
    'application': fields.Nested(api.model('DetailedApplicationInfo', {
        'name': fields.String(description='Application name'),
        'version': fields.String(description='Application version'),
        'environment': fields.String(description='Environment name'),
        'debug': fields.Boolean(description='Debug mode status'),
        'testing': fields.Boolean(description='Testing mode status'),
        'python_version': fields.String(description='Python version'),
        'flask_version': fields.String(description='Flask version'),
        'uptime_seconds': fields.Float(description='Application uptime in seconds'),
        'timezone': fields.String(description='Application timezone')
    }), description='Detailed application information'),
    'database': fields.Nested(api.model('DetailedDatabaseStatus', {
        'status': fields.String(required=True, description='Database status'),
        'response_time_ms': fields.Float(description='Database response time in milliseconds'),
        'connection_pool': fields.Nested(api.model('ConnectionPool', {
            'size': fields.Integer(description='Connection pool size'),
            'checked_in': fields.Integer(description='Checked in connections'),
            'checked_out': fields.Integer(description='Checked out connections'),
            'overflow': fields.Integer(description='Overflow connections'),
            'invalid': fields.Integer(description='Invalid connections')
        }), description='Connection pool information'),
        'database_url': fields.String(description='Database name'),
        'driver': fields.String(description='Database driver')
    }), description='Detailed database status'),
    'system': fields.Nested(api.model('SystemResources', {
        'cpu': fields.Nested(api.model('CPUInfo', {
            'percent': fields.Float(description='CPU usage percentage'),
            'count': fields.Integer(description='Number of CPU cores')
        }), description='CPU information'),
        'memory': fields.Nested(api.model('MemoryInfo', {
            'total_mb': fields.Float(description='Total memory in MB'),
            'available_mb': fields.Float(description='Available memory in MB'),
            'used_mb': fields.Float(description='Used memory in MB'),
            'percent': fields.Float(description='Memory usage percentage')
        }), description='Memory information'),
        'disk': fields.Nested(api.model('DiskInfo', {
            'total_gb': fields.Float(description='Total disk space in GB'),
            'free_gb': fields.Float(description='Free disk space in GB'),
            'used_gb': fields.Float(description='Used disk space in GB'),
            'percent': fields.Float(description='Disk usage percentage')
        }), description='Disk information'),
        'process': fields.Nested(api.model('ProcessInfo', {
            'pid': fields.Integer(description='Process ID'),
            'memory_mb': fields.Float(description='Process memory usage in MB'),
            'cpu_percent': fields.Float(description='Process CPU usage percentage'),
            'threads': fields.Integer(description='Number of threads'),
            'create_time': fields.DateTime(description='Process creation time')
        }), description='Process information')
    }), description='System resource information'),
    'checks': fields.Nested(api.model('HealthChecks', {
        'database_connectivity': fields.Boolean(description='Database connectivity check'),
        'system_resources_available': fields.Boolean(description='System resources availability check'),
        'application_info_available': fields.Boolean(description='Application info availability check')
    }), description='Individual health checks'),
    'errors': fields.List(fields.Nested(api.model('DetailedHealthError', {
        'component': fields.String(required=True, description='Component name'),
        'message': fields.String(required=True, description='Error message')
    })), description='Health check errors')
})

readiness_status_model = api.model('ReadinessStatus', {
    'ready': fields.Boolean(required=True, description='Readiness status'),
    'timestamp': fields.DateTime(required=True, description='Check timestamp'),
    'message': fields.String(required=True, description='Readiness message'),
    'checks': fields.Nested(api.model('ReadinessChecks', {
        'database': fields.Boolean(required=True, description='Database connectivity check')
    }), required=True, description='Readiness checks'),
    'errors': fields.List(fields.Nested(api.model('ReadinessError', {
        'component': fields.String(required=True, description='Component name'),
        'message': fields.String(required=True, description='Error message')
    })), description='Readiness check errors')
})

liveness_status_model = api.model('LivenessStatus', {
    'alive': fields.Boolean(required=True, description='Liveness status'),
    'timestamp': fields.DateTime(required=True, description='Check timestamp'),
    'message': fields.String(required=True, description='Liveness message'),
    'uptime_seconds': fields.Float(description='Application uptime in seconds'),
    'error': fields.String(description='Error message if not alive')
})