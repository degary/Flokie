"""
Base model module for Flask API Template.

This module provides the BaseModel abstract class that serves as the foundation
for all database models in the application. It includes common fields, methods
for serialization/deserialization, and validation functionality.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABCMeta
import logging

from sqlalchemy import Column, Integer, DateTime, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from flask_sqlalchemy import SQLAlchemy

from app.extensions import db

logger = logging.getLogger(__name__)


class BaseModelMeta(db.Model.__class__, ABCMeta):
    """
    Metaclass that resolves the conflict between SQLAlchemy's Model metaclass
    and ABC's metaclass.
    """
    pass


class BaseModel(db.Model, metaclass=BaseModelMeta):
    """
    Abstract base model class for all database models.
    
    Provides common fields and methods that all models should have:
    - id: Primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    - Serialization/deserialization methods
    - Validation framework
    """
    
    __abstract__ = True
    
    # Common fields for all models
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @declared_attr
    def __tablename__(cls):
        """
        Generate table name from class name.
        Converts CamelCase to snake_case and adds 's' for plural.
        """
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name + 's' if not name.endswith('s') else name
    
    def __init__(self, **kwargs):
        """
        Initialize model instance with provided keyword arguments.
        
        Args:
            **kwargs: Field values to set on the model
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Attempted to set unknown attribute '{key}' on {self.__class__.__name__}")
    
    def __repr__(self):
        """
        String representation of the model instance.
        
        Returns:
            str: String representation showing class name and id
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.
        
        Args:
            include_relationships (bool): Whether to include relationship data
            exclude_fields (List[str], optional): Fields to exclude from serialization
            
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        # Get all columns
        mapper = inspect(self.__class__)
        for column in mapper.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        # Include relationships if requested
        if include_relationships:
            for relationship in mapper.relationships:
                if relationship.key not in exclude_fields:
                    related_obj = getattr(self, relationship.key)
                    if related_obj is not None:
                        if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                            # One-to-many or many-to-many relationship
                            result[relationship.key] = [
                                obj.to_dict(include_relationships=False) if hasattr(obj, 'to_dict') else str(obj)
                                for obj in related_obj
                            ]
                        else:
                            # One-to-one or many-to-one relationship
                            result[relationship.key] = (
                                related_obj.to_dict(include_relationships=False) 
                                if hasattr(related_obj, 'to_dict') else str(related_obj)
                            )
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], exclude_fields: Optional[List[str]] = None):
        """
        Create model instance from dictionary data.
        
        Args:
            data (Dict[str, Any]): Dictionary containing model data
            exclude_fields (List[str], optional): Fields to exclude from deserialization
            
        Returns:
            BaseModel: New model instance
            
        Raises:
            ValueError: If required fields are missing or invalid data is provided
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        filtered_data = {k: v for k, v in data.items() if k not in exclude_fields}
        
        try:
            instance = cls(**filtered_data)
            instance.validate()
            return instance
        except Exception as e:
            logger.error(f"Failed to create {cls.__name__} from dict: {e}")
            raise ValueError(f"Invalid data for {cls.__name__}: {e}")
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> None:
        """
        Update model instance from dictionary data.
        
        Args:
            data (Dict[str, Any]): Dictionary containing updated data
            exclude_fields (List[str], optional): Fields to exclude from update
            
        Raises:
            ValueError: If invalid data is provided
        """
        exclude_fields = exclude_fields or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
        
        # Update the updated_at timestamp
        self.updated_at = datetime.utcnow()
        
        try:
            self.validate()
        except Exception as e:
            logger.error(f"Failed to update {self.__class__.__name__} from dict: {e}")
            raise ValueError(f"Invalid update data for {self.__class__.__name__}: {e}")
    
    def validate(self) -> None:
        """
        Validate model instance data.
        
        This method should be overridden by subclasses to implement
        specific validation logic. The base implementation performs
        basic validation of required fields.
        
        Raises:
            ValueError: If validation fails
        """
        # Basic validation - check for None values in non-nullable columns
        # Skip columns that have default values or are auto-generated
        mapper = inspect(self.__class__)
        for column in mapper.columns:
            if not column.nullable and column.name not in ['id']:
                value = getattr(self, column.name)
                # Skip validation if column has a default value and current value is None
                if value is None and column.default is None and column.server_default is None:
                    raise ValueError(f"Field '{column.name}' cannot be None")
        
        # Call custom validation method if implemented
        if hasattr(self, '_validate_custom'):
            self._validate_custom()
    
    def save(self) -> 'BaseModel':
        """
        Save model instance to database.
        
        Returns:
            BaseModel: The saved model instance
            
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        try:
            self.validate()
            db.session.add(self)
            db.session.commit()
            logger.info(f"Saved {self.__class__.__name__} with id {self.id}")
            return self
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save {self.__class__.__name__}: {e}")
            raise
    
    def delete(self) -> bool:
        """
        Delete model instance from database.
        
        Returns:
            bool: True if deletion was successful
            
        Raises:
            Exception: If database operation fails
        """
        try:
            db.session.delete(self)
            db.session.commit()
            logger.info(f"Deleted {self.__class__.__name__} with id {self.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete {self.__class__.__name__} with id {self.id}: {e}")
            raise
    
    @classmethod
    def get_by_id(cls, id: int):
        """
        Get model instance by ID.
        
        Args:
            id (int): The ID to search for
            
        Returns:
            BaseModel or None: The model instance if found, None otherwise
        """
        try:
            return cls.query.get(id)
        except Exception as e:
            logger.error(f"Failed to get {cls.__name__} by id {id}: {e}")
            return None
    
    @classmethod
    def get_all(cls, limit: Optional[int] = None, offset: Optional[int] = None):
        """
        Get all model instances with optional pagination.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            List[BaseModel]: List of model instances
        """
        try:
            query = cls.query
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get all {cls.__name__} records: {e}")
            return []
    
    @classmethod
    def count(cls) -> int:
        """
        Get total count of records for this model.
        
        Returns:
            int: Total number of records
        """
        try:
            return cls.query.count()
        except Exception as e:
            logger.error(f"Failed to count {cls.__name__} records: {e}")
            return 0
    
    @classmethod
    def exists(cls, **filters) -> bool:
        """
        Check if a record exists with the given filters.
        
        Args:
            **filters: Field filters to apply
            
        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            query = cls.query
            for field, value in filters.items():
                if hasattr(cls, field):
                    query = query.filter(getattr(cls, field) == value)
            return query.first() is not None
        except Exception as e:
            logger.error(f"Failed to check existence of {cls.__name__}: {e}")
            return False


class ValidationMixin:
    """
    Mixin class providing additional validation utilities.
    
    This mixin can be used by models that need more sophisticated
    validation beyond the basic validation provided by BaseModel.
    """
    
    def validate_required_fields(self, required_fields: List[str]) -> None:
        """
        Validate that required fields are not None or empty.
        
        Args:
            required_fields (List[str]): List of field names that are required
            
        Raises:
            ValueError: If any required field is missing or empty
        """
        for field in required_fields:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Field '{field}' is required and cannot be empty")
    
    def validate_field_length(self, field_name: str, min_length: Optional[int] = None, 
                            max_length: Optional[int] = None) -> None:
        """
        Validate field length constraints.
        
        Args:
            field_name (str): Name of the field to validate
            min_length (int, optional): Minimum allowed length
            max_length (int, optional): Maximum allowed length
            
        Raises:
            ValueError: If field length is outside allowed range
        """
        value = getattr(self, field_name, None)
        if value is not None and isinstance(value, str):
            if min_length is not None and len(value) < min_length:
                raise ValueError(f"Field '{field_name}' must be at least {min_length} characters long")
            if max_length is not None and len(value) > max_length:
                raise ValueError(f"Field '{field_name}' must be no more than {max_length} characters long")
    
    def validate_email_format(self, field_name: str) -> None:
        """
        Validate email format using basic regex.
        
        Args:
            field_name (str): Name of the email field to validate
            
        Raises:
            ValueError: If email format is invalid
        """
        import re
        
        value = getattr(self, field_name, None)
        if value is not None:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValueError(f"Field '{field_name}' must be a valid email address")
    
    def validate_unique_field(self, field_name: str, exclude_id: Optional[int] = None) -> None:
        """
        Validate that a field value is unique in the database.
        
        Args:
            field_name (str): Name of the field to check for uniqueness
            exclude_id (int, optional): ID to exclude from uniqueness check (for updates)
            
        Raises:
            ValueError: If field value is not unique
        """
        value = getattr(self, field_name, None)
        if value is not None:
            query = self.__class__.query.filter(getattr(self.__class__, field_name) == value)
            if exclude_id:
                query = query.filter(self.__class__.id != exclude_id)
            
            if query.first() is not None:
                raise ValueError(f"Field '{field_name}' must be unique. Value '{value}' already exists")