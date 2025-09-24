"""
Authentication API Routes
"""

from flask import Blueprint, request, jsonify, session
import uuid
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user store for development
# In production, this would be a proper database
users_db = {}


@auth_bp.route('/guest', methods=['POST'])
def create_guest_session():
    """Create a guest user session"""
    user_id = str(uuid.uuid4())
    session['user_id'] = user_id
    session['user_type'] = 'guest'
    session['created_at'] = datetime.utcnow().isoformat()
    
    return jsonify({
        'user_id': user_id,
        'user_type': 'guest',
        'session_created': True
    }), 201


@auth_bp.route('/session', methods=['GET'])
def get_session_info():
    """Get current session information"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 401
    
    return jsonify({
        'authenticated': True,
        'user_id': user_id,
        'user_type': session.get('user_type', 'guest'),
        'created_at': session.get('created_at')
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'})