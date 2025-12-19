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


# ============================================================================
# Swara Detection API (REST endpoints for non-WebSocket clients)
# ============================================================================

from core.models.shruti import (
    find_closest_shruti,
    analyze_pitch_deviation,
    SHRUTI_SYSTEM,
    calculate_shruti_frequency
)


@learning_bp.route('/detect/shruti', methods=['POST'])
def detect_shruti():
    """
    Detect which shruti matches a given frequency.
    REST endpoint for clients that don't use WebSocket.

    Request Body:
        frequency (float): Detected frequency in Hz
        base_sa (float, optional): Base Sa frequency (default: user preference or 261.63)
        target_shruti_index (int, optional): Expected shruti index for accuracy analysis

    Returns:
        JSON with shruti detection, deviation, and accuracy analysis
    """
    data = request.get_json()

    if not data or 'frequency' not in data:
        return jsonify({'error': 'frequency is required'}), 400

    detected_freq = data['frequency']

    # Validate frequency
    if not isinstance(detected_freq, (int, float)) or detected_freq <= 0:
        return jsonify({'error': 'Invalid frequency value'}), 400

    # Get base Sa from user preferences or request
    base_sa = data.get('base_sa')
    if not base_sa:
        user_id = session.get('user_id')
        if user_id and user_id in users_store:
            base_sa = users_store[user_id].preferences.base_sa_frequency
        else:
            base_sa = 261.63  # Default C4

    # Find closest shruti
    closest = find_closest_shruti(detected_freq, base_sa)

    # Analyze against target if provided
    target_index = data.get('target_shruti_index', 0)
    analysis = analyze_pitch_deviation(detected_freq, base_sa, target_index)

    # Build response
    response = {
        'detected_frequency': round(detected_freq, 2),
        'base_sa': base_sa,
        'closest_shruti': {
            'index': closest['shruti_index'],
            'name': closest['shruti_name'],
            'frequency': round(closest['frequency'], 2),
            'deviation_cents': round(closest['deviation_cents'], 2)
        },
        'target_analysis': {
            'target_index': target_index,
            'target_shruti': analysis['target_shruti'],
            'target_frequency': round(analysis['target_frequency'], 2),
            'deviation_cents': round(analysis['deviation_cents'], 2),
            'accuracy_score': round(analysis['accuracy_score'], 4),
            'direction': analysis['direction']
        }
    }

    return jsonify(response)


@learning_bp.route('/detect/batch', methods=['POST'])
def detect_shruti_batch():
    """
    Batch detection of multiple frequencies.
    Useful for analyzing recorded audio segments.

    Request Body:
        frequencies (list): List of frequency values in Hz
        base_sa (float, optional): Base Sa frequency
        target_shruti_index (int, optional): Expected shruti index

    Returns:
        JSON with array of detection results and summary statistics
    """
    data = request.get_json()

    if not data or 'frequencies' not in data:
        return jsonify({'error': 'frequencies array is required'}), 400

    frequencies = data['frequencies']
    if not isinstance(frequencies, list) or len(frequencies) == 0:
        return jsonify({'error': 'frequencies must be a non-empty array'}), 400

    if len(frequencies) > 1000:
        return jsonify({'error': 'Maximum 1000 frequencies per batch'}), 400

    # Get base Sa
    base_sa = data.get('base_sa')
    if not base_sa:
        user_id = session.get('user_id')
        if user_id and user_id in users_store:
            base_sa = users_store[user_id].preferences.base_sa_frequency
        else:
            base_sa = 261.63

    target_index = data.get('target_shruti_index', 0)

    # Process each frequency
    results = []
    accuracy_scores = []
    deviations = []
    shruti_counts = {}

    for freq in frequencies:
        if not isinstance(freq, (int, float)) or freq <= 0:
            results.append({'error': 'Invalid frequency', 'frequency': freq})
            continue

        closest = find_closest_shruti(freq, base_sa)
        analysis = analyze_pitch_deviation(freq, base_sa, target_index)

        results.append({
            'frequency': round(freq, 2),
            'shruti_index': closest['shruti_index'],
            'shruti_name': closest['shruti_name'],
            'deviation_cents': round(closest['deviation_cents'], 2),
            'accuracy_score': round(analysis['accuracy_score'], 4),
            'direction': analysis['direction']
        })

        accuracy_scores.append(analysis['accuracy_score'])
        deviations.append(abs(closest['deviation_cents']))

        # Count shruti occurrences
        shruti_name = closest['shruti_name']
        shruti_counts[shruti_name] = shruti_counts.get(shruti_name, 0) + 1

    # Calculate summary statistics
    summary = {
        'total_detections': len(results),
        'average_accuracy': round(sum(accuracy_scores) / len(accuracy_scores), 4) if accuracy_scores else 0,
        'average_deviation_cents': round(sum(deviations) / len(deviations), 2) if deviations else 0,
        'shruti_distribution': shruti_counts,
        'most_common_shruti': max(shruti_counts, key=shruti_counts.get) if shruti_counts else None
    }

    return jsonify({
        'base_sa': base_sa,
        'target_shruti_index': target_index,
        'results': results,
        'summary': summary
    })


@learning_bp.route('/shruti/all', methods=['GET'])
def get_all_shrutis():
    """
    Get all 22 shrutis with their frequencies for the current user's base Sa.

    Query Parameters:
        base_sa (float, optional): Base Sa frequency (default: user preference or 261.63)

    Returns:
        JSON array of all shrutis with calculated frequencies
    """
    # Get base Sa
    base_sa = request.args.get('base_sa', type=float)
    if not base_sa:
        user_id = session.get('user_id')
        if user_id and user_id in users_store:
            base_sa = users_store[user_id].preferences.base_sa_frequency
        else:
            base_sa = 261.63

    shrutis = []
    for idx, shruti in enumerate(SHRUTI_SYSTEM):
        shrutis.append({
            'index': idx,
            'name': shruti.name,
            'western_equiv': shruti.western_equiv,
            'cent_value': shruti.cent_value,
            'frequency_ratio': round(shruti.frequency_ratio, 6),
            'frequency_hz': round(shruti.calculate_frequency(base_sa), 2),
            'raga_usage': shruti.raga_usage[:5]  # Limit for response size
        })

    return jsonify({
        'base_sa': base_sa,
        'shruti_count': len(shrutis),
        'shrutis': shrutis
    })


@learning_bp.route('/exercises/history', methods=['GET'])
def get_exercise_history():
    """
    Get user's exercise history with pagination.

    Query Parameters:
        limit (int, optional): Number of records to return (default: 20, max: 100)
        offset (int, optional): Number of records to skip (default: 0)
        module (str, optional): Filter by module (swara, raga, tala)

    Returns:
        JSON with exercise history and pagination info
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user_profile = users_store.get(user_id)
    if not user_profile:
        return jsonify({'error': 'User not found'}), 404

    # Pagination parameters
    limit = min(request.args.get('limit', 20, type=int), 100)
    offset = request.args.get('offset', 0, type=int)
    module_filter = request.args.get('module')

    # Filter practice history
    history = user_profile.practice_history
    if module_filter:
        history = [s for s in history if s.module == module_filter]

    # Apply pagination
    total = len(history)
    paginated = history[offset:offset + limit]

    # Convert to dict format
    sessions = []
    for s in paginated:
        sessions.append({
            'session_id': s.session_id,
            'module': s.module,
            'exercise_type': s.exercise_type,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'duration_minutes': round(s.duration_minutes, 2),
            'accuracy_score': round(s.accuracy_score, 4),
            'consistency_score': round(s.consistency_score, 4),
            'notes_practiced': s.notes_practiced,
            'achievements_earned': s.achievements_earned
        })

    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'sessions': sessions,
        'has_more': offset + limit < total
    })


@learning_bp.route('/exercises/session/<session_id>', methods=['GET'])
def get_exercise_session(session_id: str):
    """
    Get detailed information about a specific exercise session.

    Path Parameters:
        session_id: The session ID to retrieve

    Returns:
        JSON with detailed session information
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user_profile = users_store.get(user_id)
    if not user_profile:
        return jsonify({'error': 'User not found'}), 404

    # Find the session
    target_session = None
    for s in user_profile.practice_history:
        if s.session_id == session_id:
            target_session = s
            break

    if not target_session:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify({
        'session_id': target_session.session_id,
        'user_id': target_session.user_id,
        'module': target_session.module,
        'exercise_type': target_session.exercise_type,
        'start_time': target_session.start_time.isoformat(),
        'end_time': target_session.end_time.isoformat() if target_session.end_time else None,
        'duration_minutes': round(target_session.duration_minutes, 2),
        'accuracy_score': round(target_session.accuracy_score, 4),
        'consistency_score': round(target_session.consistency_score, 4),
        'notes_practiced': target_session.notes_practiced,
        'achievements_earned': target_session.achievements_earned,
        'recordings': target_session.recordings,
        'notes': target_session.notes
    })


@learning_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """
    Get user's achievements.

    Query Parameters:
        category (str, optional): Filter by category (skill, streak, social, milestone)

    Returns:
        JSON with achievements list and summary
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user_profile = users_store.get(user_id)
    if not user_profile:
        return jsonify({'error': 'User not found'}), 404

    category_filter = request.args.get('category')

    achievements = user_profile.achievements
    if category_filter:
        achievements = [a for a in achievements if a.category == category_filter]

    # Convert to dict format
    achievement_list = []
    total_points = 0
    for a in achievements:
        achievement_list.append({
            'achievement_id': a.achievement_id,
            'name': a.name,
            'description': a.description,
            'category': a.category,
            'icon': a.icon,
            'points': a.points,
            'earned_date': a.earned_date.isoformat(),
            'rarity': a.rarity
        })
        total_points += a.points

    # Count by category
    category_counts = {}
    for a in achievements:
        category_counts[a.category] = category_counts.get(a.category, 0) + 1

    # Count by rarity
    rarity_counts = {}
    for a in achievements:
        rarity_counts[a.rarity] = rarity_counts.get(a.rarity, 0) + 1

    return jsonify({
        'total_achievements': len(achievements),
        'total_points': total_points,
        'by_category': category_counts,
        'by_rarity': rarity_counts,
        'achievements': achievement_list
    })