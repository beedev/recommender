"""
Agent state utilities and helper functions.

Provides utility functions for handling agent state transitions and enum conversions.
"""

from typing import Union, Any
from enum import Enum


def safe_enum_value(value: Union[str, Enum, Any]) -> str:
    """
    Safely extract string value from enum or string.
    
    Handles both enum objects and string values that may come from
    different sources (user input, enhanced orchestrator, etc.)
    
    Args:
        value: Value that could be an enum or string
        
    Returns:
        String representation of the value
    """
    if value is None:
        return ""
    
    if isinstance(value, Enum):
        return value.value
    
    if isinstance(value, str):
        return value
    
    # Handle other types by converting to string
    return str(value)


def normalize_enum_comparison(value1: Union[str, Enum, Any], value2: Union[str, Enum, Any]) -> bool:
    """
    Compare two values that might be enums or strings.
    
    Args:
        value1: First value to compare
        value2: Second value to compare
        
    Returns:
        True if the values are equivalent
    """
    normalized1 = safe_enum_value(value1).lower()
    normalized2 = safe_enum_value(value2).lower()
    
    return normalized1 == normalized2