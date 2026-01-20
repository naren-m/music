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
from dataclasses import dataclass, field
from collections import deque

# Import core managers and models
from core.managers.session_manager import session_manager
from core.models.shruti import (
    find_closest_shruti,
    analyze_pitch_deviation,
    SHRUTI_SYSTEM,
    ShrutiSystem
)

logger = logging.getLogger(__name__)

# Constants
MAX_HISTORY_SIZE = 1000  # Limit history to prevent memory leaks

# Swara name to shruti index mapping for validation
# Includes both short names (Sa, Ri, Ga) and full shruti names (Shadja, Rishaba, etc.)
# Default simple names (Ri, Ga, Da, Ni) map to Mayamalavagowla raga variants
# which is the standard raga for teaching Sarali Varisai
SWARA_TO_SHRUTI_INDEX = {
    # Shadja (Sa) - index 0
    'S': 0, 'Sa': 0, 'Shadja': 0,
    # Rishaba variants - indices 1-3
    # NOTE: Simple 'Ri' now maps to R₁ (Suddha Rishaba ≈ C#) for Mayamalavagowla
    'R1': 1, 'Ri1': 1, 'Ri': 1, 'SuddhaRishaba': 1, 'Suddha Rishaba': 1,
    'R2': 2, 'Ri2': 2, 'ChatussrutiRishaba': 2, 'Chatussruti Rishaba': 2,
    'R3': 3, 'Ri3': 3, 'ShatsrutiRishaba': 3, 'Shatsruti Rishaba': 3,
    # Gandhara variants - indices 4-6
    # NOTE: Simple 'Ga' maps to G₃ (Antara Gandhara ≈ E) for Mayamalavagowla
    'G1': 4, 'Ga1': 4, 'SuddhaGandhara': 4, 'Suddha Gandhara': 4,
    'G2': 5, 'Ga2': 5, 'SadharanaGandhara': 5, 'Sadharana Gandhara': 5,
    'G3': 6, 'Ga3': 6, 'Ga': 6, 'AntaraGandhara': 6, 'Antara Gandhara': 6,
    # Madhyama variants - indices 7-8
    'M1': 7, 'Ma1': 7, 'Ma': 7, 'SuddhaMadhyama': 7, 'Suddha Madhyama': 7,
    'M2': 8, 'Ma2': 8, 'PratiMadhyama': 8, 'Prati Madhyama': 8,
    # Panchama - index 9
    'P': 9, 'Pa': 9, 'Panchama': 9,
    # Dhaivata variants - indices 10-12
    # NOTE: Simple 'Da' now maps to D₁ (Suddha Dhaivata) for Mayamalavagowla
    'D1': 10, 'Da1': 10, 'Da': 10, 'SuddhaDhaivata': 10, 'Suddha Dhaivata': 10,
    'D2': 11, 'Da2': 11, 'ChatussrutiDhaivata': 11, 'Chatussruti Dhaivata': 11,
    'D3': 12, 'Da3': 12, 'ShatsrutiDhaivata': 12, 'Shatsruti Dhaivata': 12,
    # Nishada variants - indices 13-15
    # NOTE: Simple 'Ni' maps to N₃ (Kakali Nishada) for Mayamalavagowla
    'N1': 13, 'Ni1': 13, 'SuddhaNishada': 13, 'Suddha Nishada': 13,
    'N2': 14, 'Ni2': 14, 'KaisikaNishada': 14, 'Kaisika Nishada': 14,
    'N3': 15, 'Ni3': 15, 'Ni': 15, 'KakaliNishada': 15, 'Kakali Nishada': 15,
    # Upper Sa
    'Ṡ': 16, 'S\'': 16, 'Sa\'': 16,
}


@dataclass
class ExerciseResult:
    """Result of completing a single exercise."""
    exercise_index: int
    exercise_name: str
    total_notes: int
    correct_notes: int
    incorrect_notes: int
    accuracy_percentage: float
    grade: str


class PracticeSession:
    """
    Manages a session of multiple exercises for continuous practice.
    Tracks progress across all exercises and cumulative accuracy.
    """
    def __init__(self, exercises: List[Dict[str, Any]]):
        """
        Initialize a practice session with multiple exercises.

        Args:
            exercises: List of exercise dicts with 'name', 'arohanam', 'avarohanam' keys
        """
        self.exercises = exercises
        self.current_exercise_index = 0
        self.exercise_results: List[ExerciseResult] = []
        self.current_sequence: Optional['ExerciseSequence'] = None
        self.session_start_time = datetime.utcnow()
        self.is_active = True

        # Cumulative stats
        self.total_notes_played = 0
        self.total_correct_notes = 0
        self.total_incorrect_notes = 0

        # Start first exercise
        if exercises:
            self._load_current_exercise()

    def _load_current_exercise(self) -> None:
        """Load the current exercise into the sequence."""
        if self.current_exercise_index >= len(self.exercises):
            return

        exercise = self.exercises[self.current_exercise_index]
        arohanam = exercise.get('arohanam', [])
        avarohanam = exercise.get('avarohanam', [])

        # Build full sequence (arohanam + avarohanam)
        full_sequence = list(arohanam) + list(avarohanam)
        self.current_sequence = ExerciseSequence(full_sequence)

    def get_current_exercise(self) -> Optional[Dict[str, Any]]:
        """Get the current exercise details."""
        if self.current_exercise_index >= len(self.exercises):
            return None
        return self.exercises[self.current_exercise_index]

    def get_current_exercise_name(self) -> str:
        """Get the name of the current exercise."""
        exercise = self.get_current_exercise()
        return exercise.get('name', f'Exercise {self.current_exercise_index + 1}') if exercise else ''

    def is_current_exercise_completed(self) -> bool:
        """Check if the current exercise is completed."""
        return self.current_sequence is not None and self.current_sequence.completed

    def record_exercise_result(self) -> Optional[ExerciseResult]:
        """Record the result of the current exercise."""
        if not self.current_sequence:
            return None

        result = ExerciseResult(
            exercise_index=self.current_exercise_index,
            exercise_name=self.get_current_exercise_name(),
            total_notes=len(self.current_sequence.pattern_sequence),
            correct_notes=self.current_sequence.correct_notes,
            incorrect_notes=self.current_sequence.incorrect_notes,
            accuracy_percentage=self._calc_accuracy(
                self.current_sequence.correct_notes,
                self.current_sequence.incorrect_notes
            ),
            grade=self._calc_grade(
                self.current_sequence.correct_notes,
                self.current_sequence.incorrect_notes
            )
        )

        # Update cumulative stats
        self.total_notes_played += len(self.current_sequence.pattern_sequence)
        self.total_correct_notes += self.current_sequence.correct_notes
        self.total_incorrect_notes += self.current_sequence.incorrect_notes

        self.exercise_results.append(result)
        return result

    def retry_current_exercise(self) -> bool:
        """Reset and retry the current exercise."""
        if self.current_sequence:
            self.current_sequence.reset()
            return True
        return False

    def advance_to_next_exercise(self) -> bool:
        """
        Move to the next exercise in the session.
        Returns True if there's a next exercise, False if session is complete.
        """
        # Record current result if not already recorded
        if self.current_sequence and self.current_sequence.completed:
            # Check if result was already recorded
            if len(self.exercise_results) <= self.current_exercise_index:
                self.record_exercise_result()

        self.current_exercise_index += 1

        if self.current_exercise_index >= len(self.exercises):
            self.is_active = False
            return False

        self._load_current_exercise()
        return True

    def get_session_progress(self) -> Dict[str, Any]:
        """Get current session progress."""
        return {
            'current_exercise_index': self.current_exercise_index,
            'total_exercises': len(self.exercises),
            'exercises_completed': len(self.exercise_results),
            'current_exercise_name': self.get_current_exercise_name(),
            'is_current_completed': self.is_current_exercise_completed(),
            'session_active': self.is_active
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """Get complete session summary."""
        session_duration = (datetime.utcnow() - self.session_start_time).total_seconds()

        return {
            'total_exercises': len(self.exercises),
            'exercises_completed': len(self.exercise_results),
            'total_notes_played': self.total_notes_played,
            'total_correct_notes': self.total_correct_notes,
            'total_incorrect_notes': self.total_incorrect_notes,
            'session_accuracy': self._calc_accuracy(
                self.total_correct_notes,
                self.total_incorrect_notes
            ),
            'session_grade': self._calc_grade(
                self.total_correct_notes,
                self.total_incorrect_notes
            ),
            'session_duration_seconds': round(session_duration, 1),
            'exercise_results': [
                {
                    'index': r.exercise_index,
                    'name': r.exercise_name,
                    'total_notes': r.total_notes,
                    'correct': r.correct_notes,
                    'incorrect': r.incorrect_notes,
                    'accuracy': r.accuracy_percentage,
                    'grade': r.grade
                }
                for r in self.exercise_results
            ]
        }

    def _calc_accuracy(self, correct: int, incorrect: int) -> float:
        """Calculate accuracy percentage."""
        total = correct + incorrect
        return round((correct / total * 100), 1) if total > 0 else 0.0

    def _calc_grade(self, correct: int, incorrect: int) -> str:
        """Calculate grade based on accuracy."""
        accuracy = self._calc_accuracy(correct, incorrect)
        if accuracy >= 90: return 'A'
        if accuracy >= 80: return 'B'
        if accuracy >= 70: return 'C'
        if accuracy >= 60: return 'D'
        return 'F'


class ExerciseSequence:
    """
    Tracks the expected note sequence for an exercise and validates student's playing.
    """
    def __init__(self, pattern_sequence: List[str], tolerance_cents: float = 50.0):
        self.pattern_sequence = pattern_sequence  # e.g., ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', ...]
        self.current_position = 0
        self.tolerance_cents = tolerance_cents
        self.correct_notes = 0
        self.incorrect_notes = 0
        self.completed = False
        self.note_history = []  # Track all attempts

    def get_expected_note(self) -> Optional[str]:
        """Get the currently expected note."""
        if self.completed or self.current_position >= len(self.pattern_sequence):
            return None
        return self.pattern_sequence[self.current_position]

    def get_expected_shruti_index(self) -> Optional[int]:
        """Get shruti index for expected note."""
        expected = self.get_expected_note()
        if expected:
            return SWARA_TO_SHRUTI_INDEX.get(expected, 0)
        return None

    def validate_note(self, detected_shruti_name: str, accuracy_score: float) -> Dict[str, Any]:
        """
        Validate a detected note against the expected sequence.
        Returns validation result with feedback.
        """
        if self.completed:
            return {
                'valid': False,
                'message': 'Exercise completed',
                'completed': True,
                'position': self.current_position
            }

        expected_note = self.get_expected_note()
        if not expected_note:
            return {
                'valid': False,
                'message': 'No expected note',
                'completed': True
            }

        # Normalize names for comparison
        detected_normalized = detected_shruti_name.replace(' ', '')
        expected_normalized = expected_note.replace(' ', '')

        # Check if detected note matches expected
        # We consider a match if both map to same shruti index
        detected_index = SWARA_TO_SHRUTI_INDEX.get(detected_normalized)
        expected_index = SWARA_TO_SHRUTI_INDEX.get(expected_normalized, 0)

        # Separate note matching from accuracy check
        note_matches = (detected_index is not None and detected_index == expected_index)
        is_correct = note_matches and accuracy_score >= 0.70

        result = {
            'expected_note': expected_note,
            'detected_note': detected_shruti_name,
            'position': self.current_position,
            'total_notes': len(self.pattern_sequence),
            'is_correct': is_correct,
            'note_matches': note_matches,
            'accuracy_score': accuracy_score
        }

        # Record attempt
        self.note_history.append({
            'expected': expected_note,
            'detected': detected_shruti_name,
            'correct': is_correct,
            'accuracy': accuracy_score
        })

        if is_correct:
            self.correct_notes += 1
            self.current_position += 1
            result['message'] = f'Correct! {expected_note} ✓'
            result['next_note'] = self.get_expected_note()

            # Check if completed
            if self.current_position >= len(self.pattern_sequence):
                self.completed = True
                result['completed'] = True
                result['message'] = 'Exercise completed! 🎉'
                result['final_score'] = self._calculate_final_score()
        else:
            self.incorrect_notes += 1
            if note_matches:
                # Right note but pitch accuracy too low
                result['message'] = f'Good note ({expected_note}), but improve pitch accuracy'
                result['feedback_type'] = 'pitch_accuracy'
            else:
                # Wrong note entirely
                result['message'] = f'Expected {expected_note}, heard {detected_shruti_name}'
                result['feedback_type'] = 'wrong_note'
            result['completed'] = False

        result['progress'] = {
            'current': self.current_position,
            'total': len(self.pattern_sequence),
            'percentage': round((self.current_position / len(self.pattern_sequence)) * 100, 1),
            'correct': self.correct_notes,
            'incorrect': self.incorrect_notes
        }

        return result

    def _calculate_final_score(self) -> Dict[str, Any]:
        """Calculate final exercise score."""
        total_attempts = self.correct_notes + self.incorrect_notes
        accuracy = (self.correct_notes / total_attempts * 100) if total_attempts > 0 else 0
        return {
            'total_notes': len(self.pattern_sequence),
            'correct': self.correct_notes,
            'incorrect': self.incorrect_notes,
            'accuracy_percentage': round(accuracy, 1),
            'grade': 'A' if accuracy >= 90 else 'B' if accuracy >= 80 else 'C' if accuracy >= 70 else 'D' if accuracy >= 60 else 'F'
        }

    def reset(self):
        """Reset exercise to start."""
        self.current_position = 0
        self.correct_notes = 0
        self.incorrect_notes = 0
        self.completed = False
        self.note_history = []


class DetectionTracker:
    """
    Tracks detection results for a practice session with memory limits.
    Stored in SessionData.current_context.
    """
    def __init__(self, base_sa: float = 261.63):
        self.base_sa = base_sa
        self.target_shruti_index = 0
        self.exercise_type = "free_practice"
        self.start_time = datetime.utcnow()
        
        # Use deque with maxlen for automatic memory management
        self.detection_results = deque(maxlen=MAX_HISTORY_SIZE)
        self.accuracy_scores = deque(maxlen=MAX_HISTORY_SIZE)
        self.deviation_history = deque(maxlen=MAX_HISTORY_SIZE)
        self.notes_detected = deque(maxlen=MAX_HISTORY_SIZE)
        
        # Cumulative stats (counters don't leak memory)
        self.total_detections = 0
        self.correct_detections = 0

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
        # Calculate averages safely
        avg_accuracy = sum(self.accuracy_scores) / len(self.accuracy_scores) if self.accuracy_scores else 0.0
        avg_deviation = sum(abs(d) for d in self.deviation_history) / len(self.deviation_history) if self.deviation_history else 0.0
        accuracy_rate = (self.correct_detections / self.total_detections * 100) if self.total_detections > 0 else 0.0

        return {
            'total_detections': self.total_detections,
            'correct_detections': self.correct_detections,
            'accuracy_rate': round(accuracy_rate, 2),
            'average_accuracy_score': round(avg_accuracy, 4),
            'average_deviation_cents': round(avg_deviation, 2),
            'unique_notes_detected': list(set(self.notes_detected)), # Convert to set to deduplicate
            'duration_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }
        
    def reset(self):
        """Reset statistics for a new exercise"""
        self.detection_results.clear()
        self.accuracy_scores.clear()
        self.deviation_history.clear()
        self.notes_detected.clear()
        self.total_detections = 0
        self.correct_detections = 0
        self.start_time = datetime.utcnow()


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
        feedback['suggestion'] = f"Adjust pitch ({direction}). Listen to the drone."
    else:
        feedback['message'] = f"Keep practicing {target_shruti_name}."
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
        try:
            base_sa = float(base_sa)
        except (ValueError, TypeError):
            base_sa = 261.63

        logger.info(f"Client connected: {session_id}, User: {user_id}")
        join_room('audio_detection')
        if user_id:
            join_room(f'user_{user_id}')

        # Create managed session
        session = session_manager.create_session(session_id, user_id)
        
        # Initialize tracker in context
        session.current_context['tracker'] = DetectionTracker(base_sa=base_sa)
        
        # Update engine config if needed
        session.audio_engine.set_base_frequency(base_sa)

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
        session = session_manager.get_session(session_id)
        if session and 'tracker' in session.current_context:
            stats = session.current_context['tracker'].get_statistics()
            logger.info(f"Session {session_id} stats: {stats}")
            # In production, save session data to database here
        
        session_manager.remove_session(session_id)
        leave_room('audio_detection')

    @socketio.on('set_base_frequency')
    def handle_set_base_frequency(data):
        """Set the base Sa frequency for the user's practice session."""
        session_id = request.sid
        frequency = data.get('frequency', 261.63)
        try:
            frequency = float(frequency)
        except (ValueError, TypeError):
             emit('error', {'message': 'Invalid frequency format'})
             return

        # Validate frequency range (reasonable singing range)
        if not (100 <= frequency <= 500):
            emit('error', {
                'type': 'invalid_frequency',
                'message': f'Base frequency must be between 100Hz and 500Hz, got {frequency}Hz'
            })
            return

        session = session_manager.get_session(session_id)
        if session:
            tracker = session.current_context.get('tracker')
            if tracker:
                tracker.base_sa = frequency
            session.audio_engine.set_base_frequency(frequency)
            
            logger.info(f"Session {session_id} set base frequency to {frequency}Hz")

            emit('base_frequency_set', {
                'frequency': frequency,
                'status': 'success',
                'message': f'Base Sa set to {frequency:.2f}Hz'
            })
        else:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})

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

        session = session_manager.get_session(session_id)
        if session:
            tracker = session.current_context.get('tracker')
            if tracker:
                tracker.target_shruti_index = shruti_index
                target_freq = target_shruti.calculate_frequency(tracker.base_sa)

                emit('target_shruti_set', {
                    'shruti_index': shruti_index,
                    'shruti_name': target_shruti.name,
                    'western_note': target_shruti.get_western_note_name(tracker.base_sa),
                    'western_equiv': target_shruti.western_equiv,
                    'target_frequency': round(target_freq, 2),
                    'cent_value': target_shruti.cent_value,
                    'raga_usage': target_shruti.raga_usage[:5]
                })
        else:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})

    @socketio.on('start_exercise')
    def handle_start_exercise(data):
        """Start a specific exercise type."""
        session_id = request.sid
        exercise_type = data.get('exercise_type', 'free_practice')
        target_notes = data.get('target_notes', [])

        session = session_manager.get_session(session_id)
        if session:
            tracker = session.current_context.get('tracker')
            if tracker:
                tracker.reset()
                tracker.exercise_type = exercise_type

                emit('exercise_started', {
                    'exercise_type': exercise_type,
                    'target_notes': target_notes,
                    'start_time': tracker.start_time.isoformat(),
                    'base_sa': tracker.base_sa
                })
        else:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})

    @socketio.on('start_practice_session')
    def handle_start_practice_session(data):
        """
        Start a practice session with a specific exercise pattern.
        The system will validate each note the student plays against the expected sequence.

        Args:
            pattern_name: Name of the exercise (e.g., 'Sarali Varisai 1')
            arohanam: Ascending sequence (e.g., ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa\''])
            avarohanam: Descending sequence (e.g., ['Sa\'', 'Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'])
            include_avarohanam: Whether to include descending (default: True)
        """
        session_id = request.sid
        pattern_name = data.get('pattern_name', 'Practice')
        arohanam = data.get('arohanam', [])
        avarohanam = data.get('avarohanam', [])
        include_avarohanam = data.get('include_avarohanam', True)

        # Build the full sequence
        full_sequence = list(arohanam)
        if include_avarohanam and avarohanam:
            full_sequence.extend(avarohanam)

        if not full_sequence:
            emit('error', {
                'type': 'invalid_pattern',
                'message': 'Pattern must have at least one note'
            })
            return

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        tracker = session.current_context.get('tracker')
        if tracker:
            tracker.reset()
            tracker.exercise_type = pattern_name

        # Create exercise sequence for validation
        exercise = ExerciseSequence(full_sequence)
        session.current_context['exercise_sequence'] = exercise

        logger.info(f"Practice session started: {pattern_name} with {len(full_sequence)} notes (session_id={session_id})")

        emit('practice_session_started', {
            'pattern_name': pattern_name,
            'sequence': full_sequence,
            'total_notes': len(full_sequence),
            'first_note': exercise.get_expected_note(),
            'base_sa': tracker.base_sa if tracker else 261.63,
            'message': f'Play the first note: {exercise.get_expected_note()}'
        })

    # =========================================================================
    # SESSION MODE: Practice multiple exercises in sequence
    # =========================================================================

    @socketio.on('start_session_mode')
    def handle_start_session_mode(data):
        """
        Start a multi-exercise practice session.
        The student will practice all exercises in sequence with the option to
        retry or advance after each exercise completion.

        Args:
            exercises: List of exercise dicts, each with:
                - name: Exercise name (e.g., 'Sarali Varisai 1')
                - arohanam: Ascending note sequence
                - avarohanam: Descending note sequence
        """
        session_id = request.sid
        exercises = data.get('exercises', [])

        if not exercises:
            emit('error', {
                'type': 'invalid_session',
                'message': 'Session must have at least one exercise'
            })
            return

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        # Create and store the practice session
        practice_session = PracticeSession(exercises)
        session.current_context['practice_session'] = practice_session

        # Also set up the exercise sequence for validation
        if practice_session.current_sequence:
            session.current_context['exercise_sequence'] = practice_session.current_sequence

        tracker = session.current_context.get('tracker')
        if tracker:
            tracker.reset()
            tracker.exercise_type = f"Session: {practice_session.get_current_exercise_name()}"

        current_exercise = practice_session.get_current_exercise()
        first_note = practice_session.current_sequence.get_expected_note() if practice_session.current_sequence else None

        logger.info(f"Session mode started with {len(exercises)} exercises")

        emit('session_mode_started', {
            'total_exercises': len(exercises),
            'current_exercise_index': 0,
            'current_exercise_name': practice_session.get_current_exercise_name(),
            'current_exercise': current_exercise,
            'first_note': first_note,
            'base_sa': tracker.base_sa if tracker else 261.63,
            'message': f'Session started! Play the first note: {first_note}'
        })

    @socketio.on('session_retry_exercise')
    def handle_session_retry():
        """
        Retry the current exercise in session mode.
        Resets the exercise progress but keeps the session stats intact.
        """
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        practice_session = session.current_context.get('practice_session')
        if not practice_session:
            emit('error', {'type': 'no_session', 'message': 'No active practice session'})
            return

        # Retry the exercise
        practice_session.retry_current_exercise()

        # Update the exercise sequence reference
        session.current_context['exercise_sequence'] = practice_session.current_sequence

        first_note = practice_session.current_sequence.get_expected_note() if practice_session.current_sequence else None

        logger.info(f"Retrying exercise: {practice_session.get_current_exercise_name()}")

        emit('session_exercise_retried', {
            'current_exercise_index': practice_session.current_exercise_index,
            'current_exercise_name': practice_session.get_current_exercise_name(),
            'first_note': first_note,
            'session_progress': practice_session.get_session_progress(),
            'message': f'Retrying {practice_session.get_current_exercise_name()}. Play: {first_note}'
        })

    @socketio.on('session_next_exercise')
    def handle_session_next():
        """
        Advance to the next exercise in session mode.
        Records the current exercise result and moves to the next one.
        If all exercises are done, ends the session and returns summary.
        """
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        practice_session = session.current_context.get('practice_session')
        if not practice_session:
            emit('error', {'type': 'no_session', 'message': 'No active practice session'})
            return

        # Record the current exercise result if completed
        exercise_result = None
        if practice_session.is_current_exercise_completed():
            exercise_result = practice_session.record_exercise_result()

        # Try to advance to next exercise
        has_next = practice_session.advance_to_next_exercise()

        if has_next:
            # Update the exercise sequence reference
            session.current_context['exercise_sequence'] = practice_session.current_sequence

            # Reset tracker for new exercise
            tracker = session.current_context.get('tracker')
            if tracker:
                tracker.reset()
                tracker.exercise_type = f"Session: {practice_session.get_current_exercise_name()}"

            current_exercise = practice_session.get_current_exercise()
            first_note = practice_session.current_sequence.get_expected_note() if practice_session.current_sequence else None

            logger.info(f"Advanced to exercise: {practice_session.get_current_exercise_name()}")

            emit('session_exercise_advanced', {
                'current_exercise_index': practice_session.current_exercise_index,
                'current_exercise_name': practice_session.get_current_exercise_name(),
                'current_exercise': current_exercise,
                'first_note': first_note,
                'session_progress': practice_session.get_session_progress(),
                'previous_result': {
                    'name': exercise_result.exercise_name,
                    'accuracy': exercise_result.accuracy_percentage,
                    'grade': exercise_result.grade
                } if exercise_result else None,
                'message': f'Starting {practice_session.get_current_exercise_name()}. Play: {first_note}'
            })
        else:
            # Session complete!
            summary = practice_session.get_session_summary()
            logger.info(f"Session completed! Accuracy: {summary['session_accuracy']}%")

            # Clear the session data
            session.current_context.pop('practice_session', None)
            session.current_context.pop('exercise_sequence', None)

            emit('session_completed', {
                'summary': summary,
                'message': f"🎉 Session completed! Overall accuracy: {summary['session_accuracy']}%"
            })

    @socketio.on('session_end')
    def handle_session_end():
        """
        End the current practice session early.
        Returns the session summary with all completed exercises.
        """
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        practice_session = session.current_context.get('practice_session')
        if not practice_session:
            emit('error', {'type': 'no_session', 'message': 'No active practice session'})
            return

        # Record current exercise if it was completed
        if practice_session.is_current_exercise_completed():
            practice_session.record_exercise_result()

        # Get summary
        summary = practice_session.get_session_summary()
        logger.info(f"Session ended early. Completed {summary['exercises_completed']} exercises.")

        # Clear the session data
        session.current_context.pop('practice_session', None)
        session.current_context.pop('exercise_sequence', None)

        emit('session_ended', {
            'summary': summary,
            'message': f"Session ended. Completed {summary['exercises_completed']} of {summary['total_exercises']} exercises."
        })

    @socketio.on('session_get_progress')
    def handle_session_get_progress():
        """Get current session progress."""
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired or not found'})
            return

        practice_session = session.current_context.get('practice_session')
        if not practice_session:
            emit('session_progress', {'active': False})
            return

        emit('session_progress', {
            'active': True,
            'progress': practice_session.get_session_progress(),
            'current_exercise_progress': practice_session.current_sequence.current_position if practice_session.current_sequence else 0,
            'current_exercise_total': len(practice_session.current_sequence.pattern_sequence) if practice_session.current_sequence else 0
        })

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
            return

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'type': 'no_session', 'message': 'Session expired'})
            return

        tracker = session.current_context.get('tracker')
        if not tracker:
            # Should not happen if connected properly, but safety fallback
            tracker = DetectionTracker()
            session.current_context['tracker'] = tracker

        base_sa = tracker.base_sa
        target_shruti_index = tracker.target_shruti_index

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
            'western_note': target_shruti.get_western_note_name(base_sa),
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
        tracker.add_detection(result)

        # Add session stats to result
        result['session_stats'] = {
            'total_detections': tracker.total_detections,
            'accuracy_rate': round(
                (tracker.correct_detections / tracker.total_detections * 100)
                if tracker.total_detections > 0 else 0, 2
            )
        }

        # Only log occasional debug to reduce noise
        if tracker.total_detections % 50 == 0:
            logger.debug(f"Detection from {session_id}: {detected_frequency}Hz (Accuracy: {analysis['accuracy_score']:.2f})")

        emit('detection_feedback', result)
        
    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        """
        Handle raw audio chunk for server-side processing.
        This is the main listening mode where the server detects what note
        the student is playing and validates it against the expected sequence.
        """
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if not session:
            emit('error', {'message': 'Session expired'})
            return

        try:
            import numpy as np
            # Convert list/buffer to numpy array
            audio_data = np.array(data.get('audio_data', []), dtype=np.float32)

            # Use the engine to detect pitch
            result = session.audio_engine.detect_shruti(audio_data)

            if result and result.shruti:
                detected_shruti = result.shruti.name
                confidence = result.confidence
                frequency = result.detected_frequency
                cent_deviation = result.cent_deviation

                # Build base response
                response = {
                    'shruti_name': detected_shruti,
                    'frequency': round(frequency, 2),
                    'cent_deviation': round(cent_deviation, 1),
                    'confidence': round(confidence, 3),
                    'timestamp': result.timestamp
                }

                # Check if there's an active exercise sequence to validate against
                exercise = session.current_context.get('exercise_sequence')
                logger.info(f"Exercise check (sid={session_id}): exercise={exercise is not None}, "
                           f"completed={exercise.completed if exercise else 'N/A'}, "
                           f"context_keys={list(session.current_context.keys())}")

                if exercise and not exercise.completed:
                    # Validate the detected note against expected sequence
                    # Convert confidence to accuracy score (0-1)
                    accuracy_score = min(1.0, confidence) if abs(cent_deviation) < 50 else 0.5

                    expected_note = exercise.get_expected_note()
                    logger.info(f"Validating: detected={detected_shruti}, expected={expected_note}, "
                               f"accuracy={accuracy_score:.2f}, deviation={cent_deviation:.1f}¢")

                    validation = exercise.validate_note(detected_shruti, accuracy_score)
                    response['validation'] = validation
                    response['expected_note'] = exercise.get_expected_note()

                    logger.info(f"Validation result: is_correct={validation.get('is_correct')}, "
                               f"note_matches={validation.get('note_matches')}, "
                               f"position={validation.get('position')}/{validation.get('total_notes')}")

                    # If note was correct, tell frontend what's next
                    if validation.get('is_correct'):
                        response['next_note'] = exercise.get_expected_note()
                        response['feedback_type'] = 'correct'
                    else:
                        response['feedback_type'] = 'incorrect'

                    # Include progress
                    response['progress'] = validation.get('progress', {})

                    # Emit exercise-specific feedback
                    emit('practice_feedback', response)

                    # Check if exercise just completed during session mode
                    if validation.get('completed'):
                        practice_session = session.current_context.get('practice_session')
                        if practice_session:
                            # Mark that the current exercise in session is completed
                            practice_session.current_sequence = exercise  # Sync the sequence
                            exercise_name = practice_session.get_current_exercise_name()
                            logger.info(f"Exercise completed in session: {exercise_name}")
                            emit('exercise_completed_in_session', {
                                'exercise_name': exercise_name,
                                'final_score': validation.get('final_score', {}),
                            })
                else:
                    # Free practice mode - just emit detection
                    emit('shruti_detected', response)

                # Update tracker stats
                tracker = session.current_context.get('tracker')
                if tracker:
                    tracker.add_detection({
                        'shruti_name': detected_shruti,
                        'frequency': frequency,
                        'deviation_cents': cent_deviation,
                        'accuracy_score': confidence
                    })

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            # Don't crash on bad audio data

    @socketio.on('end_exercise')
    def handle_end_exercise(data=None):
        """End the current exercise and return comprehensive results."""
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if session and 'tracker' in session.current_context:
            tracker = session.current_context['tracker']
            stats = tracker.get_statistics()

            # Calculate performance grade
            accuracy_rate = stats['accuracy_rate']
            grade = _calculate_grade(accuracy_rate)
            message = _get_grade_message(grade)

            result = {
                'exercise_type': tracker.exercise_type,
                'duration_seconds': stats['duration_seconds'],
                'statistics': stats,
                'grade': grade,
                'message': message,
                'recommendations': _get_recommendations(stats, tracker.exercise_type)
            }

            emit('exercise_completed', result)
            tracker.reset()
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('get_session_stats')
    def handle_get_session_stats():
        """Get current session statistics."""
        session_id = request.sid
        session = session_manager.get_session(session_id)

        if session and 'tracker' in session.current_context:
            tracker = session.current_context['tracker']
            emit('session_stats', {
                'statistics': tracker.get_statistics(),
                'base_sa': tracker.base_sa,
                'exercise_type': tracker.exercise_type,
                'target_shruti': SHRUTI_SYSTEM[tracker.target_shruti_index].name
            })
        else:
            emit('error', {'type': 'no_session', 'message': 'No active session found'})

    @socketio.on('get_shruti_list')
    def handle_get_shruti_list():
        """Get the complete list of 22 shrutis with their properties."""
        session_id = request.sid
        session = session_manager.get_session(session_id)
        
        base_sa = 261.63
        if session and 'tracker' in session.current_context:
            base_sa = session.current_context['tracker'].base_sa

        shruti_list = []
        for idx, shruti in enumerate(SHRUTI_SYSTEM):
            shruti_list.append({
                'index': idx,
                'name': shruti.name,
                'western_note': shruti.get_western_note_name(base_sa),
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

def _calculate_grade(accuracy_rate: float) -> str:
    if accuracy_rate >= 90: return 'A'
    if accuracy_rate >= 80: return 'B'
    if accuracy_rate >= 70: return 'C'
    if accuracy_rate >= 60: return 'D'
    return 'F'

def _get_grade_message(grade: str) -> str:
    messages = {
        'A': 'Excellent performance!',
        'B': 'Good job! Keep practicing.',
        'C': 'Fair performance. Focus on pitch accuracy.',
        'D': 'Needs improvement. Practice with the tanpura.',
        'F': 'Keep practicing! Listen carefully to the drone.'
    }
    return messages.get(grade, 'Keep practicing!')

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