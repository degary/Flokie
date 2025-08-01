"""
Models package for Flask API Template.

This package contains all database models and related functionality.
"""

from .base import BaseModel, ValidationMixin
from .user import User

# Export all models and base classes
__all__ = ["BaseModel", "ValidationMixin", "User"]

# Additional models will be imported here as they are created in later tasks
