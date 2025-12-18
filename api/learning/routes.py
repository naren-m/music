"""
Learning API Routes
Handles swara training, progress tracking, and learning analytics
"""

from flask import Blueprint, request, jsonify, session
from flask_socketio import emit
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from core.models.user import UserProfile, SkillLevel, LearningGoal
from core.models.shruti import ShrutiSystem
from modules.swara.trainer import SwaraTrainer, ExerciseType, SwaraProgressTracker

learning_bp = Blueprint('learning', __name__)

# Global instances (in production, these would be dependency injected)
shruti_system = ShrutiSystem()
swara_trainer = SwaraTrainer()
progress_tracker = SwaraProgressTracker()

# In-memory user store (in production, this would be a database)
users_store: Dict[str, UserProfile] = {}
active_sessions: Dict[str, str] = {}  # session_id -> user_id


@learning_bp.route('/profile', methods=['GET'])
def get_user_profile():
    """Get current user profile"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_profile = users_store.get(user_id)
    if not user_profile:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user_profile.to_dict())


@learning_bp.route('/profile', methods=['POST'])
def create_user_profile():
    """Create or update user profile"""
    data = request.get_json()
    
    # Generate user ID if not provided
    user_id = data.get('user_id', str(uuid.uuid4()))
    session['user_id'] = user_id
    
    # Create user profile
    user_profile = UserProfile(
        user_id=user_id,
        email=data.get('email', f'user_{user_id}@example.com'),
        username=data.get('username', f'user_{user_id[:8]}'),
        full_name=data.get('full_name', 'Anonymous User'),
        created_at=datetime.utcnow(),
        overall_skill_level=SkillLevel(data.get('skill_level', 'beginner')),
        learning_goals=[LearningGoal(goal) for goal in data.get('learning_goals', ['beginner'])]
    )
    
    # Set preferences
    if 'preferences' in data:
        prefs = data['preferences']
        user_profile.preferences.language = prefs.get('language', 'en')
        user_profile.preferences.base_sa_frequency = prefs.get('base_sa_frequency', 261.63)
        user_profile.preferences.preferred_tempo = prefs.get('preferred_tempo', 120)
    
    users_store[user_id] = user_profile
    
    return jsonify(user_profile.to_dict()), 201


@learning_bp.route('/exercises/swara/start', methods=['POST'])
def start_swara_exercise():
    """Start a swara recognition exercise"""
    user_id = session.get('user_id')
    if not user_id or user_id not in users_store:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    exercise_type_str = data.get('exercise_type', 'single_swara')
    
    try:
        exercise_type = ExerciseType(exercise_type_str)
    except ValueError:
        return jsonify({'error': 'Invalid exercise type'}), 400
    
    # Set base Sa frequency from user preferences
    user_profile = users_store[user_id]
    # audio_engine.set_base_sa_frequency(user_profile.preferences.base_sa_frequency) # Client-side now
    
    # Start exercise
    exercise_config = swara_trainer.start_exercise(user_profile, exercise_type)
    
    # Store session
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = user_id
    session['exercise_session_id'] = session_id
    
    return jsonify({
        'session_id': session_id,
        'exercise_config': {
            'exercise_type': exercise_config.exercise_type.value,
            'difficulty': exercise_config.difficulty.value,
            'target_shrutis': exercise_config.target_shrutis,
            'duration_seconds': exercise_config.duration_seconds,
            'accuracy_threshold': exercise_config.accuracy_threshold,
            'cent_tolerance': exercise_config.cent_tolerance,
            'with_drone': exercise_config.with_drone,
            'with_metronome': exercise_config.with_metronome
        },
        'user_preferences': { # Provide user preferences for client-side audio setup
            'base_sa_frequency': user_profile.preferences.base_sa_frequency,
            # 'sample_rate': audio_config.sample_rate, # Client fetches from /api/v1/audio/config
            # 'buffer_size': audio_config.buffer_size
        }
    })


@learning_bp.route('/exercises/swara/stop', methods=['POST'])
def stop_swara_exercise():
    """Stop current swara exercise and get results"""
    user_id = session.get('user_id')
    session_id = session.get('exercise_session_id')
    
    if not user_id or not session_id or session_id not in active_sessions:
        return jsonify({'error': 'No active exercise session'}), 400
    
    # Stop exercise and get results
    result = swara_trainer.stop_exercise()
    
    if result:
        # Record session for progress tracking
        progress_tracker.record_session(result, user_id)
        
        # Update user profile
        user_profile = users_store[user_id]
        practice_session = create_practice_session_from_result(result, user_id)
        user_profile.add_practice_session(practice_session)
        
        # Clean up session
        del active_sessions[session_id]
        session.pop('exercise_session_id', None)
        
        return jsonify({
            'result': {
                'overall_accuracy': result.overall_accuracy,
                'consistency_score': result.consistency_score,
                'average_cent_deviation': result.average_cent_deviation,
                'total_correct': result.total_correct,
                'total_attempts': len(result.attempts),
                'feedback': result.feedback,
                'recommendations': result.recommendations,
                'achieved_milestones': result.achieved_milestones,
                'duration_minutes': (result.end_time - result.start_time).total_seconds() / 60
            }
        })
    else:
        return jsonify({'error': 'No exercise result available'}), 400


@learning_bp.route('/exercises/swara/feedback', methods=['GET'])
def get_real_time_feedback():
    """Get real-time feedback for current exercise"""
    session_id = session.get('exercise_session_id')
    
    if not session_id or session_id not in active_sessions:
        return jsonify({'error': 'No active exercise session'}), 400
    
    feedback = swara_trainer.get_real_time_feedback()
    
    if feedback:
        return jsonify(feedback)
    else:
        return jsonify({'error': 'No feedback available'}), 400


@learning_bp.route('/progress/analytics', methods=['GET'])
def get_progress_analytics():
    """Get user progress analytics"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    days = request.args.get('days', 30, type=int)
    analytics = progress_tracker.get_progress_analytics(user_id, days)
    
    # Add user-specific analytics
    user_profile = users_store.get(user_id)
    if user_profile:
        analytics.update({
            'overall_skill_level': user_profile.overall_skill_level.value,
            'total_practice_time': user_profile.total_practice_time,
            'practice_streak': user_profile.practice_streak,
            'total_sessions': user_profile.total_sessions,
            'weekly_practice_time': user_profile.get_weekly_practice_time(),
            'skill_distribution': user_profile.get_learning_recommendations(),
            'recommendations': user_profile.get_learning_recommendations()
        })
    
    return jsonify(analytics)


@learning_bp.route('/shruti/info/<shruti_name>', methods=['GET'])
def get_shruti_info(shruti_name: str):
    """Get detailed information about a specific shruti"""
    user_id = session.get('user_id')
    base_sa = 261.63
    
    if user_id and user_id in users_store:
        base_sa = users_store[user_id].preferences.base_sa_frequency
    
    shruti = shruti_system.get_shruti(shruti_name)
    if not shruti:
        return jsonify({'error': 'Shruti not found'}), 404
    
    return jsonify({
        'name': shruti.name,
        'western_equiv': shruti.western_equiv,
        'cent_value': shruti.cent_value,
        'frequency_ratio': shruti.frequency_ratio,
        'frequency_hz': shruti.calculate_frequency(base_sa),
        'raga_usage': shruti.raga_usage,
        'gamaka_patterns': shruti.gamaka_patterns or []
    })


@learning_bp.route('/ragas', methods=['GET'])
def get_ragas():
    """Get list of supported ragas"""
    from ...core.models.shruti import MELAKARTA_RAGAS, JANYA_RAGAS
    
    ragas = {}
    
    # Add melakarta ragas
    for raga_num, raga_data in MELAKARTA_RAGAS.items():
        ragas[raga_data['name']] = {
            'type': 'melakarta',
            'number': raga_num,
            'arohanam': raga_data['arohanam'],
            'avarohanam': raga_data.get('avarohanam', raga_data['arohanam'][::-1])
        }
    
    # Add janya ragas
    for raga_name, raga_data in JANYA_RAGAS.items():
        ragas[raga_name] = {
            'type': 'janya',
            'parent': raga_data['parent'],
            'arohanam': raga_data['arohanam'],
            'avarohanam': raga_data['avarohanam'],
            'vakra': raga_data.get('vakra', False)
        }
    
    return jsonify(ragas)


@learning_bp.route('/settings/sa-frequency', methods=['POST'])
def set_sa_frequency():
    """Set base Sa frequency for user"""
    user_id = session.get('user_id')
    if not user_id or user_id not in users_store:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    frequency = data.get('frequency')
    
    if not frequency or not (100 <= frequency <= 500):
        return jsonify({'error': 'Invalid frequency (must be 100-500 Hz)'}), 400
    
    # Update user preferences
    user_profile = users_store[user_id]
    user_profile.preferences.base_sa_frequency = frequency
    
    # Update audio engine
    # audio_engine.set_base_sa_frequency(frequency)
    
    return jsonify({
        'message': 'Sa frequency updated successfully',
        'frequency': frequency
    })


def create_practice_session_from_result(result, user_id: str):
    """Convert ExerciseResult to PracticeSession"""
    from ...core.models.user import PracticeSession
    
    return PracticeSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        module='swara',
        exercise_type=result.exercise_config.exercise_type.value,
        start_time=result.start_time,
        end_time=result.end_time,
        duration_minutes=(result.end_time - result.start_time).total_seconds() / 60,
        accuracy_score=result.overall_accuracy,
        consistency_score=result.consistency_score,
        notes_practiced=result.exercise_config.target_shrutis,
        achievements_earned=result.achieved_milestones
    )