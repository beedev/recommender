"""
Core application components for the Pconfig Recommender API.

This package contains configuration management, security utilities,
and other core functionality needed across the application.
"""

from .config import settings, get_settings, get_cors_config

__all__ = [
    "settings",
    "get_settings", 
    "get_cors_config"
]