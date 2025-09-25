"""
Security Validators for Database Operations
Prevents SQL injection and validates input parameters
"""

import re
import logging

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    pass


def validate_db_name(db_name: str) -> str:
    """
    Validate database name to prevent SQL injection

    Args:
        db_name: Database name to validate

    Returns:
        str: Validated database name

    Raises:
        SecurityValidationError: If validation fails
    """
    if not db_name or not isinstance(db_name, str):
        raise SecurityValidationError("Database name must be a non-empty string")

    # Remove whitespace
    db_name = db_name.strip()

    if not db_name:
        raise SecurityValidationError("Database name cannot be empty or whitespace only")

    # PostgreSQL identifier rules:
    # - Must start with letter or underscore
    # - Can contain letters, digits, underscores
    # - Maximum 63 characters
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', db_name):
        raise SecurityValidationError(
            "Database name must start with letter or underscore and contain only "
            "letters, digits, and underscores"
        )

    if len(db_name) > 63:
        raise SecurityValidationError(
            f"Database name too long (max 63 characters, got {len(db_name)})"
        )

    # Prevent reserved words
    reserved_words = {
        'postgres', 'template0', 'template1', 'information_schema',
        'pg_catalog', 'public', 'user', 'admin', 'root', 'sys'
    }

    if db_name.lower() in reserved_words:
        raise SecurityValidationError(f"Database name '{db_name}' is reserved")

    logger.debug(f"Database name '{db_name}' validated successfully")
    return db_name


def validate_identifier(identifier: str, identifier_type: str = "identifier") -> str:
    """
    Validate PostgreSQL identifier (table name, column name, etc.)

    Args:
        identifier: Identifier to validate
        identifier_type: Type of identifier for error messages

    Returns:
        str: Validated identifier

    Raises:
        SecurityValidationError: If validation fails
    """
    if not identifier or not isinstance(identifier, str):
        raise SecurityValidationError(f"{identifier_type} must be a non-empty string")

    identifier = identifier.strip()

    if not identifier:
        raise SecurityValidationError(f"{identifier_type} cannot be empty")

    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise SecurityValidationError(
            f"{identifier_type} must start with letter or underscore and contain only "
            "letters, digits, and underscores"
        )

    if len(identifier) > 63:
        raise SecurityValidationError(
            f"{identifier_type} too long (max 63 characters, got {len(identifier)})"
        )

    return identifier