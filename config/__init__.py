"""
Configuration module for the Carnatic Music Learning Platform.

Contains database configuration, application settings, and environment management.
"""

from .database import (
    DatabaseConfig,
    DatabaseManager,
    db_manager,
    init_db_with_flask,
    get_db_session,
)

__all__ = [
    'DatabaseConfig',
    'DatabaseManager',
    'db_manager',
    'init_db_with_flask',
    'get_db_session',
]
