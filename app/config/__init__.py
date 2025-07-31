"""
Configuration module for Flask API Template.

This module provides configuration classes for different environments.
"""

from .base import BaseConfig
from .development import DevelopmentConfig
from .testing import TestingConfig
from .acceptance import AcceptanceConfig
from .production import ProductionConfig

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'acceptance': AcceptanceConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

__all__ = [
    'config',
    'BaseConfig',
    'DevelopmentConfig', 
    'TestingConfig',
    'AcceptanceConfig',
    'ProductionConfig'
]