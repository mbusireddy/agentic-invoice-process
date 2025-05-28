"""
Configuration module for invoice processing system
"""

from .settings import settings, create_directories
from .regional_rules import (
    get_regional_rules, get_validation_rules, validate_region,
    get_supported_currencies, get_tax_types, get_approval_limits
)

__all__ = [
    'settings',
    'create_directories',
    'get_regional_rules',
    'get_validation_rules',
    'validate_region',
    'get_supported_currencies',
    'get_tax_types',
    'get_approval_limits'
]