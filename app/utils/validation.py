"""
Validation utilities and helper functions.

This module provides utility functions for data validation,
error handling, and schema processing.
"""

import logging
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError
from typing import Type, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


def validate_json(schema_class: Type, location: str = 'json') -> Callable:
    """
    Decorator for validating request data using Marshmallow schemas.
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        location: Where to get data from ('json', 'args', 'form')
        
    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                
                # Get data based on location
                if location == 'json':
                    data = request.get_json() or {}
                elif location == 'args':
                    data = request.args.to_dict()
                elif location == 'form':
                    data = request.form.to_dict()
                else:
                    raise ValueError(f"Invalid location: {location}")
                
                # Validate data
                validated_data = schema.load(data)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Validation error in {f.__name__}: {e.messages}")
                return jsonify({
                    'error': 'Validation failed',
                    'code': 'VALIDATION_ERROR',
                    'details': e.messages
                }), 400
            except Exception as e:
                logger.error(f"Unexpected error in validation decorator: {e}")
                return jsonify({
                    'error': 'Internal validation error',
                    'code': 'INTERNAL_ERROR'
                }), 500
        
        return decorated_function
    return decorator


def validate_query_params(schema_class: Type) -> Callable:
    """
    Decorator for validating query parameters.
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        
    Returns:
        Decorated function
    """
    return validate_json(schema_class, location='args')


def serialize_response(data: Any, schema_class: Type, many: bool = False) -> Dict[str, Any]:
    """
    Serialize response data using Marshmallow schema.
    
    Args:
        data: Data to serialize
        schema_class: Marshmallow schema class to use for serialization
        many: Whether to serialize multiple objects
        
    Returns:
        Serialized data
        
    Raises:
        ValidationError: If serialization fails
    """
    try:
        schema = schema_class()
        return schema.dump(data, many=many)
    except Exception as e:
        logger.error(f"Serialization error: {e}")
        raise ValidationError(f"Failed to serialize response: {str(e)}")


def handle_validation_error(error: ValidationError) -> tuple:
    """
    Handle marshmallow validation errors consistently.
    
    Args:
        error: ValidationError instance
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    logger.warning(f"Validation error: {error.messages}")
    return {
        'error': 'Validation failed',
        'code': 'VALIDATION_ERROR',
        'details': error.messages
    }, 400


def validate_pagination_params(page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number
        per_page: Items per page
        
    Returns:
        Dictionary with validated pagination parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Set defaults
    page = page or 1
    per_page = per_page or 20
    
    # Validate page
    if page < 1:
        raise ValidationError("Page must be at least 1")
    
    # Validate per_page
    if per_page < 1:
        raise ValidationError("Per page must be at least 1")
    if per_page > 100:
        raise ValidationError("Per page cannot exceed 100")
    
    return {
        'page': page,
        'per_page': per_page
    }


def validate_sort_params(sort_by: Optional[str] = None, sort_order: Optional[str] = None) -> Dict[str, str]:
    """
    Validate and normalize sorting parameters.
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        
    Returns:
        Dictionary with validated sorting parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Set defaults
    sort_by = sort_by or 'created_at'
    sort_order = sort_order or 'desc'
    
    # Validate sort_by
    valid_sort_fields = ['created_at', 'updated_at', 'username', 'email', 'first_name', 'last_name']
    if sort_by not in valid_sort_fields:
        raise ValidationError(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
    
    # Validate sort_order
    if sort_order not in ['asc', 'desc']:
        raise ValidationError("Sort order must be 'asc' or 'desc'")
    
    return {
        'sort_by': sort_by,
        'sort_order': sort_order
    }


def sanitize_search_term(search_term: Optional[str]) -> Optional[str]:
    """
    Sanitize search term for safe database queries.
    
    Args:
        search_term: Raw search term
        
    Returns:
        Sanitized search term or None
    """
    if not search_term:
        return None
    
    # Strip whitespace
    search_term = search_term.strip()
    
    # Return None if empty after stripping
    if not search_term:
        return None
    
    # Validate length
    if len(search_term) < 2:
        raise ValidationError("Search term must be at least 2 characters")
    if len(search_term) > 100:
        raise ValidationError("Search term cannot exceed 100 characters")
    
    # Remove potentially dangerous characters for SQL injection prevention
    # This is a basic sanitization - the ORM should handle SQL injection prevention
    dangerous_chars = ['%', '_', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        search_term = search_term.replace(char, '')
    
    return search_term


def validate_id_parameter(id_value: Any, parameter_name: str = 'id') -> int:
    """
    Validate ID parameter from URL.
    
    Args:
        id_value: ID value to validate
        parameter_name: Name of the parameter for error messages
        
    Returns:
        Validated integer ID
        
    Raises:
        ValidationError: If ID is invalid
    """
    try:
        id_int = int(id_value)
        if id_int < 1:
            raise ValidationError(f"{parameter_name} must be a positive integer")
        return id_int
    except (ValueError, TypeError):
        raise ValidationError(f"{parameter_name} must be a valid integer")


def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Standardized success response dictionary
    """
    response = {
        'success': True
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return response


def create_error_response(error_message: str, error_code: str = 'ERROR', details: Any = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Error message
        error_code: Error code
        details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        'error': error_message,
        'code': error_code
    }
    
    if details is not None:
        response['details'] = details
    
    return response


def validate_boolean_param(value: Any, default: bool = False) -> bool:
    """
    Validate and convert boolean parameter.
    
    Args:
        value: Value to convert to boolean
        default: Default value if conversion fails
        
    Returns:
        Boolean value
    """
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    
    if isinstance(value, int):
        return bool(value)
    
    return default


class ValidationMixin:
    """
    Mixin class for adding validation capabilities to controllers.
    """
    
    def validate_request_data(self, schema_class: Type, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate request data using schema.
        
        Args:
            schema_class: Marshmallow schema class
            data: Data to validate (defaults to request JSON)
            
        Returns:
            Validated data
            
        Raises:
            ValidationError: If validation fails
        """
        if data is None:
            data = request.get_json() or {}
        
        schema = schema_class()
        return schema.load(data)
    
    def serialize_data(self, data: Any, schema_class: Type, many: bool = False) -> Dict[str, Any]:
        """
        Serialize data using schema.
        
        Args:
            data: Data to serialize
            schema_class: Marshmallow schema class
            many: Whether to serialize multiple objects
            
        Returns:
            Serialized data
        """
        return serialize_response(data, schema_class, many=many)
    
    def create_response(self, data: Any = None, message: str = None, status_code: int = 200) -> tuple:
        """
        Create a standardized response.
        
        Args:
            data: Response data
            message: Response message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = create_success_response(data, message)
        return response, status_code
    
    def create_error_response(self, error_message: str, error_code: str = 'ERROR', 
                            details: Any = None, status_code: int = 400) -> tuple:
        """
        Create a standardized error response.
        
        Args:
            error_message: Error message
            error_code: Error code
            details: Additional error details
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = create_error_response(error_message, error_code, details)
        return response, status_code