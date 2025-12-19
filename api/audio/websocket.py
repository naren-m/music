"""
Audio WebSocket Events
Real-time audio detection and feedback for Carnatic music practice.
Handles shruti detection, accuracy analysis, and coaching feedback.
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field
import uuid

# Import shruti analysis functions
from core.models.shruti import (
    find_closest_shruti,
    analyze_pitch_deviation,
    SHRUTI_SYSTEM,
    ShrutiSystem
)

logger = logging.getLogger(__name__)

# Global shruti system instance
_shruti_system = ShrutiSystem()


@dataclass
class DetectionSession:
    """Tracks detection results for a practice session."""
    session_id: str
    user_id: Optional[str]
    base_sa: float = 261.63  # Default C4
    target_shruti_index: int = 0  # Default to Sa
    exercise_type: str = "free_practice"
    start_time: datetime = field(default_factory=datetime.utcnow)
    detection_results: List[Dict] = field(default_factory=list)
    accuracy_scores: List[float] = field(default_factory=list)
    deviation_history: List[float] = field(default_factory=list)
    notes_detected: List[str] = field(default_factory=list)
    total_detections: int = 0
    correct_detections: int = 0

    def add_detection(self, result: Dict) -> None:
        """Add a detection result and update statistics."""
        self.detection_results.append(result)
        self.total_detections += 1

        if 'accuracy_score' in result:
            self.accuracy_scores.append(result['accuracy_score'])
            if result['accuracy_score'] >= 0.85:
                self.correct_detections += 1

        if 'deviation_cents' in result:
            self.deviation_history.append(result['deviation_cents'])

        if 'shruti_name' in result and result['shruti_name']:
            self.notes_detected.append(result['shruti_name'])

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        avg_accuracy = sum(self.accuracy_scores) / len(self.accuracy_scores) if self.accuracy_scores else 0.0
        avg_deviation = sum(abs(d) for d in self.deviation_history) / len(self.deviation_history) if self.deviation_history else 0.0
        accuracy_rate = (self.correct_detections / self.total_detections * 100) if self.total_detections > 0 else 0.0

        return {
            'total_detections': self.total_detections,
            'correct_detections': self.correct_detections,
            'accuracy_rate': round(accuracy_rate, 2),
            'average_accuracy_score': round(avg_accuracy, 4),
            'average_deviation_cents': round(avg_deviation, 2),
            'unique_notes_detected': list(set(self.notes_detected)),
            'duration_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }


# Active sessions storage (in production, use Redis or database)
_active_sessions: Dict[str, DetectionSession] = {}


def get_coaching_feedback(analysis: Dict, target_shruti_name: str) -> Dict[str, Any]:
    """Generate coaching feedback based on pitch analysis."""
    deviation = analysis['deviation_cents']
    accuracy = analysis['accuracy_score']
    direction = analysis['direction']

    feedback = {
        'accuracy_level': 'excellent' if accuracy >= 0.95 else 'good' if accuracy >= 0.85 else 'fair' if accuracy >= 0.70 else 'needs_work',
        'direction': direction,
        'deviation_cents': round(deviation, 2),
        'target_note': target_shruti_name,
        'detected_frequency': analysis.get('detected_frequency', 0),
        'target_frequency': analysis.get('target_frequency', 0)
    }

    # Generate coaching message
    if accuracy >= 0.95:
        feedback['message'] = f"Excellent! Perfect {target_shruti_name}."
        feedback['suggestion'] = "Maintain this precision."
    elif accuracy >= 0.85:
        feedback['message'] = f"Good {target_shruti_name}!"
        feedback['suggestion'] = f"Slightly {direction} by {abs(deviation):.1f} cents. Minor adjustment needed."
    elif accuracy >= 0.70:
        feedback['message'] = f"Fair attempt at {target_shruti_name}."
        if direction == 'sharp':
            feedback['suggestion'] = f"Lower your pitch by about {abs(deviation):.0f} cents."
        elif direction == 'flat':
            feedback['suggestion'] = f"Raise your pitch by about {abs(deviation):.0f} cents."
        else:
            feedback['suggestion'] = "Focus on the tanpura drone for reference."
    else:
        feedback['message'] = f"Keep practicing {target_shruti_name}."
        if direction == 'sharp':
            feedback['suggestion'] = f"Your pitch is too high by {abs(deviation):.0f} cents. Listen to the Sa drone."
        elif direction == 'flat':
            feedback['suggestion'] = f"Your pitch is too low by {abs(deviation):.0f} cents. Listen to the Sa drone."
        else:
            feedback['suggestion'] = "Try matching the tanpura drone more closely."

    return feedback


def register_audio_events(socketio):
    """Register real-time audio detection WebSocket events."""

    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection and initialize detection session."""
        session_id = request.sid
        user_id = auth.get('user_id') if auth else None
        base_sa = auth.get('base_sa', 261.63) if auth else 261.63

        logger.info(f"Client connected: {session_id}, User: {user_id}")
        join_room('audio_detection')
        if user_id:
            join_room(f'user_{user_id}')

        # Create detection session
        _active_sessions[session_id] = DetectionSession(
            session_id=session_id,
            user_id=user_id,
            base_sa=base_sa
        )

        emit('connected', {
            'message': 'Connected to real-time audio service.',
            'session_id': session_id,
            'base_sa': base_sa,
            'shruti_count': len(SHRUTI_SYSTEM)
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection and finalize session."""
        session_id = request.sid
        logger.info(f"Client disconnected: {session_id}")

        # Get session statistics before cleanup
        if session_id in _active_sessions:
            session = _active_sessions[session_id]
            stats = session.get_statistics()
            logger.info(f"Session {session_id} stats: {stats}")
            # In production, save session data to database here
            del _active_sessions[session_id]

        leave_room('audio_detection')

    @socketio.on('set_base_frequency')
    def handle_set_base_frequency(data):
        """Set the base Sa frequency for the user's practice session."""
        session_id = request.sid
        frequency = data.get('frequency', 261.63)

        # Validate frequency range (reasonable singing range)
        if not (100 <= frequency <= 500):
            emit('error', {
                'type': 'invalid_frequency',
                'message': f'Base frequency must be between 100Hz and 500Hz, got {frequency}Hz'
            })
            return

        logger.info(f"Session {session_id} set base frequency to {frequency}Hz")

        if session_id in _active_sessions:
            _active_sessions[session_id].base_sa = frequency

        emit('base_frequency_set', {
            'frequency': frequency,
            'status': 'success',
            'message': f'Base Sa set to {frequency:.2f}Hz'
        })

    @socketio.on('set_target_shruti')
    def handle_set_target_shruti(data):
        """Set the target shruti for practice."""
        session_id = request.sid
        shruti_index = data.get('shruti_index', 0)
        shruti_name = data.get('shruti_name')

        # Find shruti by name if provided
        if shruti_name:
            for idx, shruti in enumerate(SHRUTI_SYSTEM):
                if shruti.name == shruti_name:
                    shruti_index = idx
                    break

        # Validate shruti index
        if not (0 <= shruti_index < len(SHRUTI_SYSTEM)):
            emit('error', {
                'type': 'invalid_shruti',
                'message': f'Shruti index must be between 0 and {len(SHRUTI_SYSTEM)-1}'
            })
            return

        target_shruti = SHRUTI_SYSTEM[shruti_index]

        if session_id in _active_sessions:
            session = _active_sessions[session_id]
            session.target_shruti_index = shruti_index
            target_freq = target_shruti.calculate_frequency(session.base_sa)

            emit('target_shruti_set', {
                'shruti_index': shruti_index,
                'shruti_name': target_shruti.name,
                'western_equiv': target_shruti.western_equiv,
                'target_frequency': round(target_freq, 2),
                'cent_value': target_shruti.cent_value,
                'raga_usage': target_shruti.raga_usage[:5]  # Limit to 5 ragas
            })
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('start_exercise')
    def handle_start_exercise(data):
        """Start a specific exercise type."""
        session_id = request.sid
        exercise_type = data.get('exercise_type', 'free_practice')
        target_notes = data.get('target_notes', [])

        if session_id in _active_sessions:
            session = _active_sessions[session_id]
            session.exercise_type = exercise_type
            session.start_time = datetime.utcnow()
            session.detection_results = []
            session.accuracy_scores = []
            session.deviation_history = []
            session.notes_detected = []
            session.total_detections = 0
            session.correct_detections = 0

            emit('exercise_started', {
                'exercise_type': exercise_type,
                'target_notes': target_notes,
                'start_time': session.start_time.isoformat(),
                'base_sa': session.base_sa
            })
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('detection_result')
    def handle_detection_result(data):
        """
        Process shruti detection results from the client.
        Analyzes pitch accuracy, provides coaching feedback, and tracks progress.
        """
        session_id = request.sid
        detected_frequency = data.get('frequency')
        timestamp = data.get('timestamp', time.time())
        confidence = data.get('confidence', 1.0)

        if detected_frequency is None:
            emit('result_received', {
                'status': 'error',
                'message': 'No frequency provided'
            })
            return

        # Get session data
        session = _active_sessions.get(session_id)
        if not session:
            emit('result_received', {
                'status': 'error',
                'message': 'No active session'
            })
            return

        base_sa = session.base_sa
        target_shruti_index = session.target_shruti_index

        # Find closest shruti to detected frequency
        closest_match = find_closest_shruti(detected_frequency, base_sa)

        # Analyze pitch deviation from target
        analysis = analyze_pitch_deviation(detected_frequency, base_sa, target_shruti_index)

        # Generate coaching feedback
        target_shruti = SHRUTI_SYSTEM[target_shruti_index]
        feedback = get_coaching_feedback(analysis, target_shruti.name)

        # Build comprehensive result
        result = {
            'timestamp': timestamp,
            'detected_frequency': round(detected_frequency, 2),
            'confidence': confidence,
            'base_sa': base_sa,

            # Closest shruti detection
            'shruti_index': closest_match['shruti_index'],
            'shruti_name': closest_match['shruti_name'],
            'shruti_frequency': round(closest_match['frequency'], 2),
            'shruti_deviation_cents': round(closest_match['deviation_cents'], 2),

            # Target analysis
            'target_shruti_index': target_shruti_index,
            'target_shruti_name': target_shruti.name,
            'target_frequency': round(analysis['target_frequency'], 2),
            'deviation_cents': round(analysis['deviation_cents'], 2),
            'accuracy_score': round(analysis['accuracy_score'], 4),
            'direction': analysis['direction'],

            # Coaching feedback
            'feedback': feedback,

            # Status
            'status': 'ok'
        }

        # Update session statistics
        session.add_detection(result)

        # Add session stats to result
        result['session_stats'] = {
            'total_detections': session.total_detections,
            'accuracy_rate': round(
                (session.correct_detections / session.total_detections * 100)
                if session.total_detections > 0 else 0, 2
            )
        }

        logger.debug(f"Detection from {session_id}: {detected_frequency}Hz → {closest_match['shruti_name']} (accuracy: {analysis['accuracy_score']:.2f})")

        emit('detection_feedback', result)

    @socketio.on('end_exercise')
    def handle_end_exercise(data=None):
        """End the current exercise and return comprehensive results."""
        session_id = request.sid

        if session_id in _active_sessions:
            session = _active_sessions[session_id]
            stats = session.get_statistics()

            # Calculate performance grade
            accuracy_rate = stats['accuracy_rate']
            if accuracy_rate >= 90:
                grade = 'A'
                message = 'Excellent performance!'
            elif accuracy_rate >= 80:
                grade = 'B'
                message = 'Good job! Keep practicing.'
            elif accuracy_rate >= 70:
                grade = 'C'
                message = 'Fair performance. Focus on pitch accuracy.'
            elif accuracy_rate >= 60:
                grade = 'D'
                message = 'Needs improvement. Practice with the tanpura.'
            else:
                grade = 'F'
                message = 'Keep practicing! Listen carefully to the drone.'

            result = {
                'exercise_type': session.exercise_type,
                'duration_seconds': stats['duration_seconds'],
                'statistics': stats,
                'grade': grade,
                'message': message,
                'recommendations': _get_recommendations(stats, session.exercise_type)
            }

            emit('exercise_completed', result)

            # Reset for next exercise
            session.detection_results = []
            session.accuracy_scores = []
            session.deviation_history = []
            session.notes_detected = []
            session.total_detections = 0
            session.correct_detections = 0
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('get_session_stats')
    def handle_get_session_stats():
        """Get current session statistics."""
        session_id = request.sid

        if session_id in _active_sessions:
            session = _active_sessions[session_id]
            emit('session_stats', {
                'statistics': session.get_statistics(),
                'base_sa': session.base_sa,
                'exercise_type': session.exercise_type,
                'target_shruti': SHRUTI_SYSTEM[session.target_shruti_index].name
            })
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('get_shruti_list')
    def handle_get_shruti_list():
        """Get the complete list of 22 shrutis with their properties."""
        session_id = request.sid
        session = _active_sessions.get(session_id)
        base_sa = session.base_sa if session else 261.63

        shruti_list = []
        for idx, shruti in enumerate(SHRUTI_SYSTEM):
            shruti_list.append({
                'index': idx,
                'name': shruti.name,
                'western_equiv': shruti.western_equiv,
                'cent_value': shruti.cent_value,
                'frequency': round(shruti.calculate_frequency(base_sa), 2),
                'frequency_ratio': round(shruti.frequency_ratio, 6),
                'raga_usage': shruti.raga_usage[:3]  # Limit for response size
            })

        emit('shruti_list', {
            'base_sa': base_sa,
            'shrutis': shruti_list
        })

    @socketio.on('ping')
    def handle_ping():
        """Handle ping for latency measurement."""
        emit('pong', {'timestamp': time.time()})


def _get_recommendations(stats: Dict, exercise_type: str) -> List[str]:
    """Generate practice recommendations based on session statistics."""
    recommendations = []

    accuracy_rate = stats['accuracy_rate']
    avg_deviation = stats['average_deviation_cents']

    if accuracy_rate < 70:
        recommendations.append("Practice with the tanpura drone to improve pitch accuracy.")
        recommendations.append("Try slower, sustained notes to build muscle memory.")
    elif accuracy_rate < 85:
        recommendations.append("Good progress! Focus on consistency across all shrutis.")
        recommendations.append("Try practicing specific problematic notes in isolation.")
    else:
        recommendations.append("Excellent accuracy! Try increasing tempo or complexity.")
        recommendations.append("Consider practicing gamakas (ornaments) at this level.")

    if avg_deviation > 20:
        recommendations.append("Your pitch tends to drift. Focus on steady breath support.")
    elif avg_deviation > 10:
        recommendations.append("Minor pitch variations detected. Practice long tones.")

    if len(stats['unique_notes_detected']) < 5:
        recommendations.append("Expand your practice to include more shrutis.")

    return recommendations