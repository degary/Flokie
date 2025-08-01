"""
Configuration module for Flask API Template.

This module provides configuration classes for different environments.
"""

from .acceptance import AcceptanceConfig
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "acceptance": AcceptanceConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

__all__ = [
    "config",
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "AcceptanceConfig",
    "ProductionConfig",
]
