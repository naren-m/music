"""
Authentication and Session Validation Middleware
Secure session management with rate limiting and validation
"""

import time
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import session, request, jsonify, current_app

logger = logging.getLogger(__name__)

# Simple in-memory rate limiting (use Redis in production)
rate_limit_store: Dict[str, Dict[str, Any]] = {}


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, status_code: int = 429):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def require_valid_session(f):
    """
    Decorator to require a valid authenticated session

    Validates session existence, expiry, and authenticity
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check session exists
            user_id = session.get('user_id')
            if not user_id:
                logger.warning(f"Unauthenticated request to {request.endpoint} from {request.remote_addr}")
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please create a session first',
                    'code': 'AUTH_REQUIRED'
                }), 401

            # Check session expiry
            expires_at = session.get('expires_at')
            if expires_at:
                try:
                    expiry_time = datetime.fromisoformat(expires_at)
                    if datetime.utcnow() > expiry_time:
                        session.clear()
                        logger.info(f"Expired session cleared for user {user_id}")
                        return jsonify({
                            'error': 'Session expired',
                            'message': 'Please create a new session',
                            'code': 'SESSION_EXPIRED'
                        }), 401
                except ValueError:
                    # Invalid expiry format, clear session
                    session.clear()
                    return jsonify({
                        'error': 'Invalid session',
                        'code': 'SESSION_INVALID'
                    }), 401

            # Validate session integrity
            user_type = session.get('user_type', 'guest')
            created_at = session.get('created_at')

            if not created_at:
                logger.warning(f"Session missing creation timestamp for user {user_id}")
                session.clear()
                return jsonify({
                    'error': 'Invalid session format',
                    'code': 'SESSION_INVALID'
                }), 401

            # Check for session hijacking (basic)
            user_agent = request.headers.get('User-Agent', '')
            session_agent = session.get('user_agent', '')

            if session_agent and user_agent != session_agent:
                logger.warning(f"User-Agent mismatch for session {user_id}: {user_agent} vs {session_agent}")
                # Don't clear session automatically, but log for monitoring
                # In high-security apps, you might want to clear the session

            # Update last activity
            session['last_activity'] = datetime.utcnow().isoformat()

            # Log successful authentication for monitoring
            logger.debug(f"Authenticated request: user={user_id}, type={user_type}, endpoint={request.endpoint}")

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}")
            return jsonify({
                'error': 'Authentication system error',
                'code': 'AUTH_ERROR'
            }), 500

    return decorated_function


def rate_limit(requests_per_minute: int = 60, per_user: bool = True):
    """
    Rate limiting decorator

    Args:
        requests_per_minute: Maximum requests allowed per minute
        per_user: If True, limit per user; if False, limit per IP
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Determine rate limiting key
                if per_user and session.get('user_id'):
                    key = f"user:{session['user_id']}"
                else:
                    # Fallback to IP-based limiting
                    key = f"ip:{request.remote_addr}"

                current_time = time.time()

                # Clean old entries (simple cleanup)
                if key in rate_limit_store:
                    requests = rate_limit_store[key]['requests']
                    # Remove requests older than 1 minute
                    requests = [req_time for req_time in requests if current_time - req_time < 60]
                    rate_limit_store[key]['requests'] = requests
                else:
                    rate_limit_store[key] = {'requests': []}

                # Check rate limit
                request_count = len(rate_limit_store[key]['requests'])
                if request_count >= requests_per_minute:
                    logger.warning(f"Rate limit exceeded for {key}: {request_count} requests/minute")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {requests_per_minute} requests per minute',
                        'retry_after': 60,
                        'code': 'RATE_LIMIT_EXCEEDED'
                    }), 429

                # Record this request
                rate_limit_store[key]['requests'].append(current_time)

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Rate limiting error: {str(e)}")
                # Allow request if rate limiting fails (fail open)
                return f(*args, **kwargs)

        return decorated_function
    return decorator


def validate_guest_session_creation():
    """
    Validate guest session creation with enhanced security

    Returns validated session data or raises AuthenticationError
    """
    # Check if already has valid session
    if session.get('user_id') and not _is_session_expired():
        raise AuthenticationError("Session already exists", 400)

    # Basic bot detection
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent or len(user_agent) < 10:
        raise AuthenticationError("Invalid client", 400)

    # Check for suspicious patterns
    suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
    if any(pattern in user_agent.lower() for pattern in suspicious_agents):
        logger.warning(f"Suspicious user agent blocked: {user_agent}")
        raise AuthenticationError("Client not supported", 403)

    # Verify request format
    if not request.is_json:
        raise AuthenticationError("Content-Type must be application/json", 400)

    data = request.get_json()
    if not data:
        raise AuthenticationError("Request body required", 400)

    # Optional human verification check
    human_verification = data.get('human_verification', False)
    if not human_verification:
        logger.info("Guest session created without human verification")
        # You might want to require this in production

    return {
        'user_agent': user_agent,
        'verified': human_verification
    }


def create_secure_session(user_id: str, user_type: str = 'guest', duration_hours: int = 24) -> Dict[str, Any]:
    """
    Create a secure session with proper validation and logging

    Args:
        user_id: Unique user identifier
        user_type: Type of user (guest, registered, admin)
        duration_hours: Session duration in hours

    Returns:
        Dict containing session information
    """
    current_time = datetime.utcnow()
    expires_at = current_time + timedelta(hours=duration_hours)

    # Clear any existing session first
    session.clear()

    # Create new session
    session['user_id'] = user_id
    session['user_type'] = user_type
    session['created_at'] = current_time.isoformat()
    session['expires_at'] = expires_at.isoformat()
    session['last_activity'] = current_time.isoformat()

    # Store user agent for basic session hijacking detection
    session['user_agent'] = request.headers.get('User-Agent', '')

    # Log session creation
    logger.info(f"Session created: user={user_id}, type={user_type}, expires={expires_at.isoformat()}")

    return {
        'user_id': user_id,
        'user_type': user_type,
        'expires_at': expires_at.isoformat(),
        'session_created': True,
        'duration_hours': duration_hours
    }


def _is_session_expired() -> bool:
    """Check if current session is expired"""
    expires_at = session.get('expires_at')
    if not expires_at:
        return True

    try:
        expiry_time = datetime.fromisoformat(expires_at)
        return datetime.utcnow() > expiry_time
    except ValueError:
        return True


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current user information from session

    Returns:
        Dict with user information or None if not authenticated
    """
    user_id = session.get('user_id')
    if not user_id or _is_session_expired():
        return None

    return {
        'user_id': user_id,
        'user_type': session.get('user_type', 'guest'),
        'created_at': session.get('created_at'),
        'last_activity': session.get('last_activity')
    }


def cleanup_rate_limits():
    """Clean up old rate limit entries (call periodically)"""
    current_time = time.time()
    keys_to_remove = []

    for key, data in rate_limit_store.items():
        # Remove requests older than 1 minute
        requests = [req_time for req_time in data['requests'] if current_time - req_time < 60]

        if not requests:
            keys_to_remove.append(key)
        else:
            rate_limit_store[key]['requests'] = requests

    for key in keys_to_remove:
        del rate_limit_store[key]

    if keys_to_remove:
        logger.debug(f"Cleaned up {len(keys_to_remove)} rate limit entries")