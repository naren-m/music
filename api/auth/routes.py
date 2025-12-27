"""
Authentication API Routes - Security Hardened
"""

from flask import Blueprint, request, jsonify, session
import uuid
import logging
from datetime import datetime

from .middleware import (
    require_valid_session, validate_guest_session_creation,
    create_secure_session, get_current_user, AuthenticationError, RateLimitError
)
from api.rate_limiting import guest_creation_rate_limit, auth_rate_limit, standard_rate_limit

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user store for development
# In production, this would be a proper database
users_db = {}


@auth_bp.route('/guest', methods=['POST'])
@guest_creation_rate_limit
def create_guest_session():
    """Create a guest user session with security validation"""
    try:
        # Validate request and detect bots
        validation_data = validate_guest_session_creation()

        # Generate secure user ID
        user_id = str(uuid.uuid4())

        # Create secure session
        session_data = create_secure_session(
            user_id=user_id,
            user_type='guest',
            duration_hours=24
        )

        logger.info(f"Guest session created: {user_id} from {request.remote_addr}")

        return jsonify(session_data), 201

    except AuthenticationError as e:
        logger.warning(f"Guest session creation failed: {e.message} from {request.remote_addr}")
        return jsonify({
            'error': e.message,
            'code': 'AUTH_FAILED'
        }), e.status_code

    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded for guest session from {request.remote_addr}")
        return jsonify({
            'error': e.message,
            'code': 'RATE_LIMIT'
        }), e.status_code

    except Exception as e:
        logger.error(f"Unexpected error in guest session creation: {str(e)}")
        return jsonify({
            'error': 'Session creation failed',
            'message': 'Please try again',
            'code': 'CREATION_ERROR'
        }), 500


@auth_bp.route('/session', methods=['GET'])
@standard_rate_limit
def get_session_info():
    """Get current session information with validation"""
    try:
        user_info = get_current_user()

        if not user_info:
            return jsonify({
                'authenticated': False,
                'message': 'No valid session found'
            }), 401

        # Return session information
        return jsonify({
            'authenticated': True,
            'user_id': user_info['user_id'],
            'user_type': user_info['user_type'],
            'created_at': user_info['created_at'],
            'last_activity': user_info['last_activity']
        })

    except Exception as e:
        logger.error(f"Session info error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': 'Session check failed'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@standard_rate_limit
def verify_session():
    """Verify if the current session is valid - alias for /session"""
    try:
        user_info = get_current_user()

        if not user_info:
            return jsonify({
                'authenticated': False,
                'message': 'No valid session found'
            }), 401

        return jsonify({
            'authenticated': True,
            'user_id': user_info['user_id'],
            'user_type': user_info['user_type']
        })

    except Exception as e:
        logger.error(f"Session verify error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': 'Session verification failed'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@auth_rate_limit
def logout():
    """Clear user session securely"""
    try:
        user_id = session.get('user_id')

        # Clear session
        session.clear()

        logger.info(f"User logged out: {user_id} from {request.remote_addr}")

        return jsonify({
            'message': 'Logged out successfully',
            'logged_out': True
        })

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still clear session on error
        session.clear()
        return jsonify({
            'message': 'Logged out',
            'logged_out': True
        })