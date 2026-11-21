"""
Configuration module for the Carnatic Music Learning Platform.

Contains database configuration, application settings, and environment management.
"""

from .database import (
    DatabaseConfig,
    DatabaseManager,
    db_manager,
    get_db_session,
    init_db_with_flask,
)

__all__ = [
    "DatabaseConfig",
    "DatabaseManager",
    "db_manager",
    "init_db_with_flask",
    "get_db_session",
]
