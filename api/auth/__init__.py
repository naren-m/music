"""
Authentication API module for the Carnatic Music Learning Platform.

Provides authentication, session management, and authorization.
"""

from .middleware import (
    require_valid_session,
    validate_guest_session_creation,
    create_secure_session,
    get_current_user,
    AuthenticationError,
    RateLimitError,
)
from .routes import auth_bp

__all__ = [
    'require_valid_session',
    'validate_guest_session_creation',
    'create_secure_session',
    'get_current_user',
    'AuthenticationError',
    'RateLimitError',
    'auth_bp',
]
