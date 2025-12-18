"""
Swara Recognition and Training Module
Implements progressive exercises for mastering the 7 basic swaras and their variations
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import numpy as np
import random
import time
from datetime import datetime, timedelta

from core.models.shruti import ShrutiSystem, Shruti
from core.models.user import UserProfile, PracticeSession, SkillLevel

@dataclass
class ShrutiDetectionResult:
    """Represents a single shruti detection result from the client."""
    shruti_name: Optional[str]
    detected_frequency: float
    cent_deviation: float
    confidence: float
    timestamp: float


class ExerciseType(Enum):
    """Types of swara exercises"""
    SINGLE_SWARA = "single_swara"
    SEQUENTIAL_PATTERN = "sequential_pattern"
    RANDOM_RECOGNITION = "random_recognition"
    GAMAKA_DETECTION = "gamaka_detection"
    RELATIVE_PITCH = "relative_pitch"


class DifficultyLevel(Enum):
    """Exercise difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class ExerciseConfig:
    """Configuration for swara exercises"""
    exercise_type: ExerciseType
    difficulty: DifficultyLevel
    target_shrutis: List[str]
    duration_seconds: int = 60
    accuracy_threshold: float = 0.8
    consistency_threshold: float = 0.7
    tempo_bpm: int = 120
    with_drone: bool = True
    with_metronome: bool = False
    cent_tolerance: float = 25.0


@dataclass
class ExerciseAttempt:
    """Single attempt at hitting a target shruti"""
    target_shruti: str
    detected_shruti: Optional[str]
    target_frequency: float
    detected_frequency: Optional[float]
    cent_deviation: float
    confidence: float
    timestamp: float
    is_correct: bool
    
    
@dataclass
class ExerciseResult:
    """Complete result of an exercise session"""
    exercise_config: ExerciseConfig
    start_time: datetime
    end_time: datetime
    attempts: List[ExerciseAttempt]
    overall_accuracy: float
    consistency_score: float
    average_cent_deviation: float
    total_correct: int
    feedback: str
    recommendations: List[str]
    achieved_milestones: List[str]


class SwaraExerciseGenerator:
    """Generates progressive swara exercises based on user skill level"""
    
    def __init__(self, shruti_system: ShrutiSystem):
        self.shruti_system = shruti_system
        
        # Basic swaras for beginners
        self.basic_swaras = ["Sa", "R₂", "G₃", "M₁", "Pa", "D₂", "N₃"]
        
        # Extended swaras for intermediate
        self.extended_swaras = ["Sa", "R₁", "R₂", "G₂", "G₃", "M₁", "M₂", 
                               "Pa", "D₁", "D₂", "N₂", "N₃"]
        
        # All 22 shrutis for advanced
        self.all_shrutis = [s.western_equiv for s in shruti_system.shrutis]
    
    def generate_exercise(self, user_profile: UserProfile, 
                         exercise_type: ExerciseType) -> ExerciseConfig:
        """Generate appropriate exercise based on user skill and type"""
        
        skill_level = user_profile.overall_skill_level
        swara_progress = user_profile.module_progress.get("swara")
        
        # Determine difficulty
        if skill_level in [SkillLevel.NOVICE, SkillLevel.BEGINNER]:
            difficulty = DifficultyLevel.BEGINNER
            target_shrutis = self.basic_swaras[:5]  # Start with 5 basic swaras
        elif skill_level in [SkillLevel.STUDENT, SkillLevel.PRACTITIONER]:
            difficulty = DifficultyLevel.INTERMEDIATE
            target_shrutis = self.basic_swaras
        elif skill_level == SkillLevel.INTERMEDIATE:
            difficulty = DifficultyLevel.INTERMEDIATE
            target_shrutis = self.extended_swaras
        else:
            difficulty = DifficultyLevel.ADVANCED
            target_shrutis = self.all_shrutis
        
        # Adjust based on recent performance
        if swara_progress and swara_progress.average_accuracy < 0.6:
            # Reduce difficulty if struggling
            if len(target_shrutis) > 5:
                target_shrutis = target_shrutis[:5]
            difficulty = DifficultyLevel.BEGINNER
        
        # Configure exercise parameters
        duration = self._get_exercise_duration(exercise_type, difficulty)
        accuracy_threshold = self._get_accuracy_threshold(difficulty)
        cent_tolerance = self._get_cent_tolerance(difficulty)
        
        return ExerciseConfig(
            exercise_type=exercise_type,
            difficulty=difficulty,
            target_shrutis=target_shrutis,
            duration_seconds=duration,
            accuracy_threshold=accuracy_threshold,
            cent_tolerance=cent_tolerance,
            with_drone=True,
            with_metronome=(exercise_type == ExerciseType.SEQUENTIAL_PATTERN)
        )
    
    def _get_exercise_duration(self, exercise_type: ExerciseType, 
                              difficulty: DifficultyLevel) -> int:
        """Get appropriate exercise duration"""
        base_durations = {
            ExerciseType.SINGLE_SWARA: 30,
            ExerciseType.SEQUENTIAL_PATTERN: 60,
            ExerciseType.RANDOM_RECOGNITION: 90,
            ExerciseType.GAMAKA_DETECTION: 45,
            ExerciseType.RELATIVE_PITCH: 75
        }
        
        duration = base_durations[exercise_type]
        
        # Adjust for difficulty
        if difficulty == DifficultyLevel.BEGINNER:
            duration = int(duration * 0.7)
        elif difficulty == DifficultyLevel.ADVANCED:
            duration = int(duration * 1.3)
            
        return duration
    
    def _get_accuracy_threshold(self, difficulty: DifficultyLevel) -> float:
        """Get accuracy threshold for difficulty level"""
        thresholds = {
            DifficultyLevel.BEGINNER: 0.6,
            DifficultyLevel.INTERMEDIATE: 0.75,
            DifficultyLevel.ADVANCED: 0.85,
            DifficultyLevel.EXPERT: 0.9
        }
        return thresholds[difficulty]
    
    def _get_cent_tolerance(self, difficulty: DifficultyLevel) -> float:
        """Get cent tolerance for difficulty level"""
        tolerances = {
            DifficultyLevel.BEGINNER: 40.0,
            DifficultyLevel.INTERMEDIATE: 25.0,
            DifficultyLevel.ADVANCED: 15.0,
            DifficultyLevel.EXPERT: 10.0
        }
        return tolerances[difficulty]


class SwaraTrainer:
    """Main swara training engine with real-time feedback"""
    
    def __init__(self):
        self.shruti_system = ShrutiSystem()
        self.exercise_generator = SwaraExerciseGenerator(self.shruti_system)
        
        # Current exercise state
        self.current_exercise: Optional[ExerciseConfig] = None
        self.current_target: Optional[str] = None
        self.exercise_start_time: Optional[datetime] = None
        self.attempts: List[ExerciseAttempt] = []
        self.is_active = False

        # Callbacks for real-time feedback
        self.callbacks: Dict[str, List[Callable]] = {
            'target_changed': [],
            'attempt_recorded': [],
            'exercise_completed': [],
            'milestone_achieved': []
        }
    
    def process_detection_result(self, detection_data: Dict[str, any], user_base_sa_frequency: float) -> None:
        """
        Processes a raw detection result from the client and feeds it into the trainer.
        """
        # Convert raw dict to dataclass (or validate and use directly)
        detection = ShrutiDetectionResult(
            shruti_name=detection_data.get('shruti_name'),
            detected_frequency=detection_data['detected_frequency'],
            cent_deviation=detection_data['cent_deviation'],
            confidence=detection_data['confidence'],
            timestamp=detection_data['timestamp']
        )
        self._on_shruti_detected(detection, user_base_sa_frequency)
    

    
    def start_exercise(self, user_profile: UserProfile, 
                      exercise_type: ExerciseType) -> ExerciseConfig:
        """Start a new swara exercise"""
        if self.is_active:
            self.stop_exercise()
        
        # Generate exercise
        self.current_exercise = self.exercise_generator.generate_exercise(
            user_profile, exercise_type
        )
        
        # Initialize state
        self.exercise_start_time = datetime.utcnow()
        self.attempts = []
        self.is_active = True
        
        # Set first target
        self._set_next_target()
        
        # Trigger callbacks
        self._trigger_callbacks('exercise_started', self.current_exercise)
        
        return self.current_exercise
    
    def stop_exercise(self) -> Optional[ExerciseResult]:
        """Stop current exercise and return results"""
        if not self.is_active or not self.current_exercise:
            return None
        
        self.is_active = False
        end_time = datetime.utcnow()
        
        # Calculate results
        result = self._calculate_exercise_result(end_time)
        
        # Trigger callbacks
        self._trigger_callbacks('exercise_completed', result)
        
        # Reset state
        self.current_exercise = None
        self.current_target = None
        self.exercise_start_time = None
        self.attempts = []
        
        return result
    
    def _set_next_target(self) -> None:
        """Set the next target shruti for the exercise"""
        if not self.current_exercise:
            return
        
        if self.current_exercise.exercise_type == ExerciseType.SINGLE_SWARA:
            # Cycle through all target swaras
            if not hasattr(self, '_swara_cycle_index'):
                self._swara_cycle_index = 0
            
            self.current_target = self.current_exercise.target_shrutis[
                self._swara_cycle_index % len(self.current_exercise.target_shrutis)
            ]
            self._swara_cycle_index += 1
            
        elif self.current_exercise.exercise_type == ExerciseType.SEQUENTIAL_PATTERN:
            # Follow ascending/descending pattern
            if not hasattr(self, '_pattern_index'):
                self._pattern_index = 0
                self._ascending = True
            
            shrutis = self.current_exercise.target_shrutis
            if self._ascending:
                self.current_target = shrutis[self._pattern_index]
                self._pattern_index += 1
                if self._pattern_index >= len(shrutis):
                    self._ascending = False
                    self._pattern_index = len(shrutis) - 2
            else:
                self.current_target = shrutis[self._pattern_index]
                self._pattern_index -= 1
                if self._pattern_index < 0:
                    self._ascending = True
                    self._pattern_index = 1
                    
        elif self.current_exercise.exercise_type == ExerciseType.RANDOM_RECOGNITION:
            # Random selection
            self.current_target = random.choice(self.current_exercise.target_shrutis)
        
        # Trigger callback
        self._trigger_callbacks('target_changed', self.current_target)
    
    def _on_shruti_detected(self, detection: ShrutiDetectionResult, user_base_sa_frequency: float) -> None:
        """Handle shruti detection from audio engine"""
        if not self.is_active or not self.current_target:
            return
        
        # Get target shruti details
        target_shruti = None
        for shruti in self.shruti_system.shrutis:
            if shruti.western_equiv == self.current_target:
                target_shruti = shruti
                break
        
        if not target_shruti:
            return
        
        # Calculate target frequency
        target_frequency = target_shruti.calculate_frequency(
            user_base_sa_frequency
        )
        
        # Determine if attempt is correct
        cent_deviation = abs(detection.cent_deviation)
        is_correct = (cent_deviation <= self.current_exercise.cent_tolerance and
                     detection.confidence >= 0.6)
        
        # Record attempt
        attempt = ExerciseAttempt(
            target_shruti=self.current_target,
            detected_shruti=detection.shruti.western_equiv if detection.shruti else None,
            target_frequency=target_frequency,
            detected_frequency=detection.detected_frequency,
            cent_deviation=detection.cent_deviation,
            confidence=detection.confidence,
            timestamp=detection.timestamp,
            is_correct=is_correct
        )
        
        self.attempts.append(attempt)
        
        # Trigger callback
        self._trigger_callbacks('attempt_recorded', attempt)
        
        # Check if target was hit correctly
        if is_correct:
            # Brief pause before next target
            time.sleep(0.5)
            self._set_next_target()
        
        # Check if exercise should end
        elapsed_time = (datetime.utcnow() - self.exercise_start_time).total_seconds()
        if elapsed_time >= self.current_exercise.duration_seconds:
            self.stop_exercise()
    
    def _calculate_exercise_result(self, end_time: datetime) -> ExerciseResult:
        """Calculate comprehensive exercise results"""
        if not self.attempts:
            return ExerciseResult(
                exercise_config=self.current_exercise,
                start_time=self.exercise_start_time,
                end_time=end_time,
                attempts=[],
                overall_accuracy=0.0,
                consistency_score=0.0,
                average_cent_deviation=0.0,
                total_correct=0,
                feedback="No attempts recorded. Try singing closer to the microphone.",
                recommendations=["Check microphone setup", "Ensure clear pronunciation"],
                achieved_milestones=[]
            )
        
        # Calculate accuracy
        correct_attempts = [a for a in self.attempts if a.is_correct]
        overall_accuracy = len(correct_attempts) / len(self.attempts)
        
        # Calculate consistency (variance in cent deviation)
        cent_deviations = [abs(a.cent_deviation) for a in self.attempts]
        average_deviation = np.mean(cent_deviations)
        consistency_score = max(0.0, 1.0 - (np.std(cent_deviations) / 50.0))
        
        # Generate feedback and recommendations
        feedback, recommendations = self._generate_feedback(
            overall_accuracy, average_deviation, consistency_score
        )
        
        # Check for milestones
        milestones = self._check_milestones(overall_accuracy, consistency_score)
        
        return ExerciseResult(
            exercise_config=self.current_exercise,
            start_time=self.exercise_start_time,
            end_time=end_time,
            attempts=self.attempts,
            overall_accuracy=overall_accuracy,
            consistency_score=consistency_score,
            average_cent_deviation=average_deviation,
            total_correct=len(correct_attempts),
            feedback=feedback,
            recommendations=recommendations,
            achieved_milestones=milestones
        )
    
    def _generate_feedback(self, accuracy: float, avg_deviation: float, 
                          consistency: float) -> Tuple[str, List[str]]:
        """Generate personalized feedback and recommendations"""
        feedback = ""
        recommendations = []
        
        # Accuracy feedback
        if accuracy >= 0.9:
            feedback = "Excellent accuracy! Your pitch control is very strong."
        elif accuracy >= 0.75:
            feedback = "Good accuracy. Continue practicing to improve consistency."
        elif accuracy >= 0.6:
            feedback = "Fair accuracy. Focus on listening carefully to the target pitch."
        else:
            feedback = "Needs improvement. Take time to hear each swara clearly before singing."
        
        # Cent deviation feedback
        if avg_deviation > 30:
            recommendations.append("Practice with a tanpura drone to improve intonation")
            recommendations.append("Slow down and focus on pitch accuracy over speed")
        elif avg_deviation > 20:
            recommendations.append("Use ear training exercises to refine pitch perception")
        
        # Consistency feedback
        if consistency < 0.5:
            recommendations.append("Work on maintaining steady pitch throughout notes")
            recommendations.append("Practice breathing techniques for better vocal stability")
        elif consistency < 0.7:
            recommendations.append("Focus on smooth transitions between swaras")
        
        # General recommendations based on difficulty
        if self.current_exercise.difficulty == DifficultyLevel.BEGINNER:
            recommendations.append("Practice basic Sa-Pa-Sa patterns daily")
            recommendations.append("Listen to classical recordings to internalize swaras")
        
        return feedback, recommendations
    
    def _check_milestones(self, accuracy: float, consistency: float) -> List[str]:
        """Check for achieved milestones"""
        milestones = []
        
        # Accuracy milestones
        if accuracy >= 0.95:
            milestones.append("Master Accuracy - 95%+ correct")
        elif accuracy >= 0.9:
            milestones.append("Expert Accuracy - 90%+ correct")
        elif accuracy >= 0.8:
            milestones.append("Advanced Accuracy - 80%+ correct")
        elif accuracy >= 0.7:
            milestones.append("Good Accuracy - 70%+ correct")
        
        # Consistency milestones
        if consistency >= 0.9:
            milestones.append("Rock Steady - Excellent consistency")
        elif consistency >= 0.8:
            milestones.append("Very Consistent - Strong pitch control")
        elif consistency >= 0.7:
            milestones.append("Consistent - Good pitch stability")
        
        # Combined milestones
        if accuracy >= 0.85 and consistency >= 0.8:
            milestones.append("Swara Master - High accuracy and consistency")
        
        return milestones
    
    def get_real_time_feedback(self) -> Optional[Dict[str, any]]:
        """Get current real-time feedback for UI"""
        if not self.is_active or not self.current_target:
            return None
        
        recent_attempts = self.attempts[-5:] if len(self.attempts) >= 5 else self.attempts
        
        if not recent_attempts:
            return {
                'current_target': self.current_target,
                'recent_accuracy': 0.0,
                'average_deviation': 0.0,
                'suggestions': ["Start singing the target swara"]
            }
        
        recent_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
        avg_deviation = np.mean([abs(a.cent_deviation) for a in recent_attempts])
        
        # Generate real-time suggestions
        suggestions = []
        if avg_deviation > 25:
            if recent_attempts[-1].cent_deviation > 0:
                suggestions.append("Pitch is too high - sing lower")
            else:
                suggestions.append("Pitch is too low - sing higher")
        
        if recent_accuracy < 0.5:
            suggestions.append("Listen carefully to the target pitch first")
        
        return {
            'current_target': self.current_target,
            'recent_accuracy': recent_accuracy,
            'average_deviation': avg_deviation,
            'last_attempt': recent_attempts[-1] if recent_attempts else None,
            'suggestions': suggestions,
            'total_attempts': len(self.attempts),
            'elapsed_time': (datetime.utcnow() - self.exercise_start_time).total_seconds()
        }
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for training events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, data: any) -> None:
        """Trigger all callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Callback error for {event}: {e}")


class SwaraProgressTracker:
    """Tracks user progress in swara training"""
    
    def __init__(self):
        self.session_history: List[ExerciseResult] = []
    
    def record_session(self, result: ExerciseResult, user_id: str) -> None:
        """Record a completed exercise session"""
        self.session_history.append(result)
        
        # Update user progress (this would normally update database)
        self._update_user_progress(result, user_id)
    
    def _update_user_progress(self, result: ExerciseResult, user_id: str) -> None:
        """Update user progress based on exercise result"""
        # This would typically update the user's ModuleProgress
        # For now, we'll just track statistics
        pass
    
    def get_progress_analytics(self, user_id: str, days: int = 30) -> Dict[str, any]:
        """Generate progress analytics for user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_sessions = [
            session for session in self.session_history
            if session.start_time >= cutoff_date
        ]
        
        if not recent_sessions:
            return {'message': 'No recent practice sessions found'}
        
        # Calculate trends
        accuracies = [s.overall_accuracy for s in recent_sessions]
        consistencies = [s.consistency_score for s in recent_sessions]
        deviations = [s.average_cent_deviation for s in recent_sessions]
        
        return {
            'total_sessions': len(recent_sessions),
            'average_accuracy': np.mean(accuracies),
            'accuracy_trend': self._calculate_trend(accuracies),
            'average_consistency': np.mean(consistencies),
            'consistency_trend': self._calculate_trend(consistencies),
            'average_deviation': np.mean(deviations),
            'deviation_trend': self._calculate_trend([-d for d in deviations]),  # Negative for improvement
            'milestones_achieved': sum(len(s.achieved_milestones) for s in recent_sessions),
            'practice_time': sum((s.end_time - s.start_time).total_seconds() for s in recent_sessions) / 60
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction (improving/declining/stable)"""
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear regression to determine trend
        x = np.arange(len(values))
        slope = np.corrcoef(x, values)[0, 1] * np.std(values) / np.std(x)
        
        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"