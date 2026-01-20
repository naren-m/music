"""
Janta Varisai Exercise Patterns

Implementation of traditional Carnatic double-note exercise patterns
with advanced transition analysis and smooth movement training.

Supports loading patterns from text files for easy content updates.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import json
from datetime import datetime
import logging

# Import the exercise loader
from modules.exercises.loader import (
    load_exercises_from_folder,
    get_level_config,
    extract_octave_shift,
    ParsedExercise,
    ExerciseConfig
)

logger = logging.getLogger(__name__)

class TransitionType(Enum):
    SMOOTH = "smooth"
    GLIDE = "glide"
    STACCATO = "staccato"
    LEGATO = "legato"

class MovementQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class DoubleNotePattern:
    swara: str
    repetitions: int
    transition_type: TransitionType
    duration_ratio: float  # Relative duration for each note
    gap_allowance: float  # Maximum allowable gap in seconds
    smoothness_threshold: float  # Minimum smoothness score (0-1)

@dataclass
class JantaExercise:
    level: int
    name: str
    pattern_type: str
    description: str
    double_patterns: List[DoubleNotePattern]
    tempo_range: Tuple[int, int]
    difficulty_score: float
    breath_points: List[int]  # Indices where breathing is recommended
    learning_objectives: List[str]
    common_mistakes: List[str]
    practice_techniques: List[str]
    mastery_criteria: Dict[str, float]

@dataclass
class TransitionAnalysis:
    from_swara: str
    to_swara: str
    movement_quality: MovementQuality
    smoothness_score: float
    gap_duration: float
    pitch_deviation: float
    recommendations: List[str]
    timestamp: datetime

class JantaPatternGenerator:
    """
    Generates and manages Janta Varisai (double-note) exercise patterns
    with advanced transition analysis and movement quality assessment.

    Supports loading patterns from text files (preferred) or
    falling back to hardcoded patterns for backward compatibility.
    """

    def __init__(self, raga: str = "mayamalavagowla"):
        """
        Initialize the Janta pattern generator.

        Args:
            raga: The raga to load patterns for (default: mayamalavagowla)
        """
        self.raga = raga
        self.base_swaras = ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']
        self.swara_frequencies = {
            'Sa': 261.63,   # C4
            'Ri': 293.66,   # D4
            'Ga': 329.63,   # E4
            'Ma': 349.23,   # F4
            'Pa': 392.00,   # G4
            'Da': 440.00,   # A4
            'Ni': 493.88    # B4
        }

        # Store config if loaded from files
        self.config: Optional[ExerciseConfig] = None

        self.janta_exercises = self._generate_all_exercises()

    def _generate_all_exercises(self) -> List[JantaExercise]:
        """
        Generate all Janta Varisai exercises.

        First attempts to load from text files. If files don't exist or
        loading fails, falls back to hardcoded patterns.
        """
        # Try loading from files first
        file_exercises = self._load_from_files()
        if file_exercises:
            logger.info(f"Loaded {len(file_exercises)} Janta exercises from text files")
            return file_exercises

        # Fall back to hardcoded patterns
        logger.info("Loading hardcoded Janta exercises (text files not found)")
        return self._generate_hardcoded_exercises()

    def _load_from_files(self) -> List[JantaExercise]:
        """
        Load Janta exercises from text files.

        Returns:
            List of JantaExercise objects, or empty list if loading fails
        """
        try:
            exercises, config = load_exercises_from_folder(
                "JantaVarasalu",
                f"{self.raga}.txt"
            )

            if not exercises:
                return []

            self.config = config
            janta_exercises = []

            for exercise in exercises:
                janta_ex = self._convert_to_janta_exercise(exercise, config)
                if janta_ex:
                    janta_exercises.append(janta_ex)

            return janta_exercises

        except Exception as e:
            logger.warning(f"Failed to load Janta exercises from files: {e}")
            return []

    def _convert_to_janta_exercise(
        self,
        exercise: ParsedExercise,
        config: Optional[ExerciseConfig]
    ) -> Optional[JantaExercise]:
        """
        Convert a ParsedExercise to a JantaExercise dataclass.

        For Janta, the swara sequence contains repeated notes (Sa Sa Ri Ri).
        We detect doubles and create DoubleNotePattern objects.

        Args:
            exercise: Parsed exercise from text file
            config: Configuration from config.json

        Returns:
            JantaExercise object or None if conversion fails
        """
        try:
            level_config = get_level_config(config, exercise.level) if config else {}

            # Combine arohanam and avarohanam for double pattern detection
            all_swaras = exercise.arohanam

            # Detect double note patterns from sequence
            double_patterns = self._detect_double_patterns(all_swaras)

            # Get tempo range
            tempo_range = level_config.get('tempo_range', [50, 100])
            if isinstance(tempo_range, list):
                tempo_range = tuple(tempo_range)

            return JantaExercise(
                level=exercise.level,
                name=level_config.get('name', f"Janta Varisai {exercise.level}"),
                pattern_type="file_loaded",
                description=f"Janta exercise level {exercise.level}",
                double_patterns=double_patterns,
                tempo_range=tempo_range,
                difficulty_score=level_config.get('difficulty', 0.15 + (exercise.level - 1) * 0.1),
                breath_points=[len(double_patterns) // 2, len(double_patterns)],
                learning_objectives=level_config.get('learning_objectives', [
                    f"Master Janta Varisai level {exercise.level}",
                    "Develop smooth double-note articulation",
                    "Build transition control"
                ]),
                common_mistakes=[
                    "Uneven repetitions",
                    "Poor transition between doubles",
                    "Inconsistent timing"
                ],
                practice_techniques=level_config.get('practice_tips', [
                    "Focus on identical pitch for repeated notes",
                    "Use metronome for consistency",
                    "Practice transitions separately"
                ]),
                mastery_criteria={
                    "pitch_consistency": 0.9,
                    "timing_accuracy": 0.85,
                    "smoothness_score": 0.8
                }
            )

        except Exception as e:
            logger.warning(f"Failed to convert Janta exercise level {exercise.level}: {e}")
            return None

    def _detect_double_patterns(self, swaras: List[str]) -> List[DoubleNotePattern]:
        """
        Detect double note patterns from a sequence of swaras.

        E.g., [Sa, Sa, Ri, Ri, Ga, Ga] -> [DoubleNotePattern(Sa, 2), DoubleNotePattern(Ri, 2), ...]

        Args:
            swaras: List of swara names

        Returns:
            List of DoubleNotePattern objects
        """
        patterns = []
        i = 0

        while i < len(swaras):
            current_swara, octave = extract_octave_shift(swaras[i])

            # Count consecutive repetitions
            count = 1
            while i + count < len(swaras):
                next_swara, next_octave = extract_octave_shift(swaras[i + count])
                if next_swara == current_swara and next_octave == octave:
                    count += 1
                else:
                    break

            # Create pattern if we have repetitions (2 or more)
            if count >= 2:
                patterns.append(DoubleNotePattern(
                    swara=current_swara if octave == 0 else f"{current_swara}2",
                    repetitions=count,
                    transition_type=TransitionType.SMOOTH,
                    duration_ratio=1.0,
                    gap_allowance=0.1,
                    smoothness_threshold=0.8
                ))
            else:
                # Single note, treat as single repetition
                patterns.append(DoubleNotePattern(
                    swara=current_swara if octave == 0 else f"{current_swara}2",
                    repetitions=1,
                    transition_type=TransitionType.SMOOTH,
                    duration_ratio=1.0,
                    gap_allowance=0.1,
                    smoothness_threshold=0.8
                ))

            i += count

        return patterns

    def _generate_hardcoded_exercises(self) -> List[JantaExercise]:
        """Generate hardcoded exercises as fallback."""
        exercises = []

        # Level 1: Basic double notes in ascending order
        exercises.append(self._create_level_1())

        # Level 2: Double notes with simple transitions
        exercises.append(self._create_level_2())

        # Level 3: Extended double note patterns
        exercises.append(self._create_level_3())

        # Level 4: Mixed double note combinations
        exercises.append(self._create_level_4())

        # Level 5: Advanced double note patterns with ornamentation
        exercises.append(self._create_level_5())

        # Level 6: Complex transition patterns
        exercises.append(self._create_level_6())

        return exercises

    def _create_level_1(self) -> JantaExercise:
        """Sa-Sa, Ri-Ri, Ga-Ga, Ma-Ma (Basic double notes)"""
        double_patterns = []

        for swara in ['Sa', 'Ri', 'Ga', 'Ma']:
            double_patterns.append(DoubleNotePattern(
                swara=swara,
                repetitions=2,
                transition_type=TransitionType.SMOOTH,
                duration_ratio=1.0,
                gap_allowance=0.1,  # 100ms max gap
                smoothness_threshold=0.8
            ))

        return JantaExercise(
            level=1,
            name="Basic Janta - Level 1",
            pattern_type="basic_double",
            description="Sa-Sa, Ri-Ri, Ga-Ga, Ma-Ma - Foundation double note patterns",
            double_patterns=double_patterns,
            tempo_range=(50, 90),
            difficulty_score=0.2,
            breath_points=[2, 4],  # After Ri-Ri and Ma-Ma
            learning_objectives=[
                "Master basic double note articulation",
                "Develop consistent note repetition",
                "Build foundation for smooth transitions",
                "Establish proper breath control"
            ],
            common_mistakes=[
                "Too much gap between repeated notes",
                "Inconsistent pitch in repetitions",
                "Poor breath management",
                "Rushing through patterns"
            ],
            practice_techniques=[
                "Start with very slow tempo",
                "Focus on identical pitch for both notes",
                "Use metronome for timing consistency",
                "Practice with sustained breath support"
            ],
            mastery_criteria={
                "pitch_consistency": 0.9,
                "timing_accuracy": 0.85,
                "smoothness_score": 0.8,
                "breath_control": 0.8
            }
        )

    def _create_level_2(self) -> JantaExercise:
        """Sa-Sa Ri-Ri, Ri-Ri Ga-Ga, Ga-Ga Ma-Ma (Connected doubles)"""
        double_patterns = []

        swara_pairs = [('Sa', 'Ri'), ('Ri', 'Ga'), ('Ga', 'Ma')]

        for i, (swara1, swara2) in enumerate(swara_pairs):
            # First swara doubled
            double_patterns.append(DoubleNotePattern(
                swara=swara1,
                repetitions=2,
                transition_type=TransitionType.SMOOTH,
                duration_ratio=1.0,
                gap_allowance=0.08,
                smoothness_threshold=0.85
            ))

            # Second swara doubled
            double_patterns.append(DoubleNotePattern(
                swara=swara2,
                repetitions=2,
                transition_type=TransitionType.LEGATO,
                duration_ratio=1.0,
                gap_allowance=0.08,
                smoothness_threshold=0.85
            ))

        return JantaExercise(
            level=2,
            name="Connected Janta - Level 2",
            pattern_type="connected_double",
            description="Sa-Sa Ri-Ri, Ri-Ri Ga-Ga, Ga-Ga Ma-Ma - Connected double note sequences",
            double_patterns=double_patterns,
            tempo_range=(55, 100),
            difficulty_score=0.3,
            breath_points=[2, 4, 6],
            learning_objectives=[
                "Connect double note patterns smoothly",
                "Maintain pitch accuracy across transitions",
                "Develop longer phrase control",
                "Improve transition smoothness"
            ],
            common_mistakes=[
                "Breaking connection between patterns",
                "Pitch drift during transitions",
                "Uneven note durations",
                "Poor phrase continuity"
            ],
            practice_techniques=[
                "Practice transitions separately",
                "Use drone for pitch reference",
                "Focus on seamless connections",
                "Gradually increase tempo"
            ],
            mastery_criteria={
                "transition_smoothness": 0.85,
                "pitch_stability": 0.9,
                "timing_consistency": 0.85,
                "phrase_continuity": 0.8
            }
        )

    def _create_level_3(self) -> JantaExercise:
        """Extended double patterns with five notes"""
        double_patterns = []

        for swara in ['Sa', 'Ri', 'Ga', 'Ma', 'Pa']:
            double_patterns.append(DoubleNotePattern(
                swara=swara,
                repetitions=2,
                transition_type=TransitionType.SMOOTH,
                duration_ratio=1.0,
                gap_allowance=0.06,
                smoothness_threshold=0.87
            ))

        return JantaExercise(
            level=3,
            name="Extended Janta - Level 3",
            pattern_type="extended_double",
            description="Sa-Sa, Ri-Ri, Ga-Ga, Ma-Ma, Pa-Pa - Extended five-note double patterns",
            double_patterns=double_patterns,
            tempo_range=(60, 110),
            difficulty_score=0.4,
            breath_points=[3, 5],
            learning_objectives=[
                "Extend vocal range with double notes",
                "Maintain consistency over longer phrases",
                "Develop stronger breath support",
                "Master Pa articulation in doubles"
            ],
            common_mistakes=[
                "Pa pitch instability",
                "Breath running out mid-phrase",
                "Tempo inconsistency over longer patterns",
                "Losing focus on later notes"
            ],
            practice_techniques=[
                "Practice Pa separately with reference",
                "Plan breathing points strategically",
                "Use hand gestures for pitch guidance",
                "Build stamina gradually"
            ],
            mastery_criteria={
                "extended_consistency": 0.85,
                "breath_management": 0.8,
                "pa_accuracy": 0.9,
                "overall_stamina": 0.8
            }
        )

    def _create_level_4(self) -> JantaExercise:
        """Mixed patterns with variable repetitions"""
        double_patterns = []

        # Varied repetition patterns
        patterns = [
            ('Sa', 2), ('Ri', 3), ('Ga', 2), ('Ma', 3), ('Pa', 2)
        ]

        for swara, reps in patterns:
            double_patterns.append(DoubleNotePattern(
                swara=swara,
                repetitions=reps,
                transition_type=TransitionType.SMOOTH if reps == 2 else TransitionType.LEGATO,
                duration_ratio=0.8 if reps == 3 else 1.0,
                gap_allowance=0.05,
                smoothness_threshold=0.88
            ))

        return JantaExercise(
            level=4,
            name="Variable Janta - Level 4",
            pattern_type="variable_repetition",
            description="Sa-Sa, Ri-Ri-Ri, Ga-Ga, Ma-Ma-Ma, Pa-Pa - Variable repetition patterns",
            double_patterns=double_patterns,
            tempo_range=(65, 120),
            difficulty_score=0.5,
            breath_points=[2, 4],
            learning_objectives=[
                "Master variable repetition patterns",
                "Adapt to changing note groupings",
                "Maintain rhythmic accuracy",
                "Develop advanced articulation skills"
            ],
            common_mistakes=[
                "Confusion with repetition counts",
                "Inconsistent articulation",
                "Poor rhythmic grouping",
                "Speed variations within groups"
            ],
            practice_techniques=[
                "Count repetitions clearly",
                "Use finger counting initially",
                "Practice each group type separately",
                "Emphasize rhythmic precision"
            ],
            mastery_criteria={
                "repetition_accuracy": 0.95,
                "rhythmic_precision": 0.9,
                "articulation_clarity": 0.85,
                "pattern_memory": 0.85
            }
        )

    def _create_level_5(self) -> JantaExercise:
        """Full octave double patterns"""
        double_patterns = []

        for swara in self.base_swaras:
            double_patterns.append(DoubleNotePattern(
                swara=swara,
                repetitions=2,
                transition_type=TransitionType.SMOOTH,
                duration_ratio=1.0,
                gap_allowance=0.05,
                smoothness_threshold=0.9
            ))

        return JantaExercise(
            level=5,
            name="Complete Janta - Level 5",
            pattern_type="full_octave_double",
            description="Complete octave double patterns: Sa-Sa through Ni-Ni",
            double_patterns=double_patterns,
            tempo_range=(70, 130),
            difficulty_score=0.6,
            breath_points=[3, 6],
            learning_objectives=[
                "Complete full octave in double notes",
                "Master all seven swaras in pairs",
                "Develop full vocal range control",
                "Achieve advanced breath management"
            ],
            common_mistakes=[
                "Upper swara pitch problems",
                "Breath management over full octave",
                "Inconsistent quality across range",
                "Tempo variations in longer phrases"
            ],
            practice_techniques=[
                "Practice upper and lower separately",
                "Use reference drone throughout",
                "Build range gradually",
                "Focus on consistent quality"
            ],
            mastery_criteria={
                "full_range_consistency": 0.85,
                "octave_accuracy": 0.9,
                "breath_endurance": 0.8,
                "overall_quality": 0.85
            }
        )

    def _create_level_6(self) -> JantaExercise:
        """Advanced patterns with ornamentations"""
        double_patterns = []

        # Complex patterns with grace notes and ornamentations
        advanced_patterns = [
            ('Sa', 2, TransitionType.GLIDE),
            ('Ri', 2, TransitionType.SMOOTH),
            ('Ga', 3, TransitionType.LEGATO),
            ('Ma', 2, TransitionType.GLIDE),
            ('Pa', 2, TransitionType.SMOOTH),
            ('Da', 2, TransitionType.LEGATO),
            ('Ni', 2, TransitionType.SMOOTH)
        ]

        for swara, reps, transition_type in advanced_patterns:
            double_patterns.append(DoubleNotePattern(
                swara=swara,
                repetitions=reps,
                transition_type=transition_type,
                duration_ratio=0.9,
                gap_allowance=0.03,
                smoothness_threshold=0.92
            ))

        return JantaExercise(
            level=6,
            name="Advanced Janta - Level 6",
            pattern_type="ornamented_double",
            description="Advanced double patterns with grace notes and ornamentations",
            double_patterns=double_patterns,
            tempo_range=(75, 140),
            difficulty_score=0.8,
            breath_points=[3, 6],
            learning_objectives=[
                "Master advanced ornamentation in doubles",
                "Develop sophisticated transition techniques",
                "Achieve professional-level smoothness",
                "Integrate grace notes and gamakas"
            ],
            common_mistakes=[
                "Overcomplicating ornamentations",
                "Losing basic pitch accuracy",
                "Poor integration of grace notes",
                "Inconsistent ornamentation style"
            ],
            practice_techniques=[
                "Master basic pattern first",
                "Add ornamentations gradually",
                "Study traditional examples",
                "Focus on musical expression"
            ],
            mastery_criteria={
                "ornamentation_quality": 0.9,
                "musical_expression": 0.85,
                "technical_precision": 0.9,
                "artistic_maturity": 0.8
            }
        )

    def analyze_transition_quality(
        self,
        audio_data: np.ndarray,
        expected_transitions: List[Tuple[str, str]],
        sample_rate: int = 44100
    ) -> List[TransitionAnalysis]:
        """
        Analyze the quality of transitions between double notes
        """
        analyses = []

        try:
            # This is a simplified analysis - in production would use advanced audio processing
            for i, (from_swara, to_swara) in enumerate(expected_transitions):

                # Calculate movement quality based on pitch continuity
                smoothness_score = self._calculate_smoothness(audio_data, from_swara, to_swara)
                gap_duration = self._detect_gap_duration(audio_data, i)
                pitch_deviation = self._measure_pitch_deviation(audio_data, from_swara, to_swara)

                # Determine movement quality
                if smoothness_score >= 0.9 and gap_duration < 0.05:
                    quality = MovementQuality.EXCELLENT
                elif smoothness_score >= 0.8 and gap_duration < 0.1:
                    quality = MovementQuality.GOOD
                elif smoothness_score >= 0.7 and gap_duration < 0.15:
                    quality = MovementQuality.FAIR
                else:
                    quality = MovementQuality.POOR

                # Generate recommendations
                recommendations = self._generate_transition_recommendations(
                    quality, smoothness_score, gap_duration, pitch_deviation
                )

                analysis = TransitionAnalysis(
                    from_swara=from_swara,
                    to_swara=to_swara,
                    movement_quality=quality,
                    smoothness_score=smoothness_score,
                    gap_duration=gap_duration,
                    pitch_deviation=pitch_deviation,
                    recommendations=recommendations,
                    timestamp=datetime.now()
                )

                analyses.append(analysis)

        except Exception as e:
            print(f"Error analyzing transition quality: {e}")

        return analyses

    def _calculate_smoothness(self, audio_data: np.ndarray, from_swara: str, to_swara: str) -> float:
        """Calculate smoothness score for transition"""
        # Simplified calculation - would use spectral analysis in production
        from_freq = self.swara_frequencies[from_swara]
        to_freq = self.swara_frequencies[to_swara]

        # Simulate analysis based on frequency difference
        freq_diff = abs(to_freq - from_freq) / from_freq
        smoothness = max(0.5, 1.0 - freq_diff)

        return smoothness

    def _detect_gap_duration(self, audio_data: np.ndarray, transition_index: int) -> float:
        """Detect duration of gaps in audio"""
        # Simplified gap detection
        # In production, would analyze RMS energy to detect silence
        return np.random.uniform(0.02, 0.15)  # Simulated gap duration

    def _measure_pitch_deviation(self, audio_data: np.ndarray, from_swara: str, to_swara: str) -> float:
        """Measure pitch deviation from expected"""
        expected_freq = self.swara_frequencies[to_swara]
        # Simplified deviation measurement
        deviation = np.random.uniform(-10, 10)  # Cents deviation
        return deviation

    def _generate_transition_recommendations(
        self,
        quality: MovementQuality,
        smoothness: float,
        gap_duration: float,
        pitch_deviation: float
    ) -> List[str]:
        """Generate recommendations based on transition analysis"""
        recommendations = []

        if quality == MovementQuality.POOR:
            recommendations.append("Focus on slower practice to improve control")
            recommendations.append("Use drone reference for pitch accuracy")

        if smoothness < 0.7:
            recommendations.append("Work on smoother voice transitions")
            recommendations.append("Practice gliding between notes")

        if gap_duration > 0.1:
            recommendations.append("Reduce gaps between repeated notes")
            recommendations.append("Maintain continuous airflow")

        if abs(pitch_deviation) > 15:
            recommendations.append("Improve pitch accuracy with tuner practice")
            recommendations.append("Strengthen ear training exercises")

        if not recommendations:
            recommendations.append("Excellent technique! Continue to maintain consistency")

        return recommendations

    def get_exercise_by_level(self, level: int) -> Optional[JantaExercise]:
        """Get Janta exercise by level number"""
        for exercise in self.janta_exercises:
            if exercise.level == level:
                return exercise
        return None

    def get_exercises_for_difficulty(self, difficulty_range: Tuple[float, float]) -> List[JantaExercise]:
        """Get exercises within specified difficulty range"""
        min_diff, max_diff = difficulty_range
        return [ex for ex in self.janta_exercises
                if min_diff <= ex.difficulty_score <= max_diff]

    def generate_practice_sequence(
        self,
        level: int,
        session_duration: int,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """Generate practice sequence for Janta Varisai"""
        exercise = self.get_exercise_by_level(level)
        if not exercise:
            return {}

        focus_areas = focus_areas or []

        # Calculate time allocation
        warmup_time = session_duration * 0.15
        main_time = session_duration * 0.7
        cooldown_time = session_duration * 0.15

        sequence = {
            "exercise": exercise,
            "total_duration": session_duration,
            "phases": [
                {
                    "name": "Warmup",
                    "duration": warmup_time,
                    "tempo": exercise.tempo_range[0],
                    "focus": "Preparation and basic articulation",
                    "patterns": exercise.double_patterns[:2]
                },
                {
                    "name": "Main Practice",
                    "duration": main_time,
                    "tempo": exercise.tempo_range[0] + 10,
                    "focus": "Full pattern with transition analysis",
                    "patterns": exercise.double_patterns
                },
                {
                    "name": "Cooldown",
                    "duration": cooldown_time,
                    "tempo": exercise.tempo_range[0] - 5,
                    "focus": "Relaxed practice and integration",
                    "patterns": exercise.double_patterns[-2:]
                }
            ],
            "breath_strategy": exercise.breath_points,
            "key_focus_areas": focus_areas,
            "success_criteria": exercise.mastery_criteria
        }

        return sequence

    def export_exercises_json(self) -> str:
        """Export all exercises to JSON format"""
        exercises_data = []

        for exercise in self.janta_exercises:
            exercise_dict = {
                "level": exercise.level,
                "name": exercise.name,
                "pattern_type": exercise.pattern_type,
                "description": exercise.description,
                "double_patterns": [
                    {
                        "swara": pattern.swara,
                        "repetitions": pattern.repetitions,
                        "transition_type": pattern.transition_type.value,
                        "duration_ratio": pattern.duration_ratio,
                        "gap_allowance": pattern.gap_allowance,
                        "smoothness_threshold": pattern.smoothness_threshold
                    }
                    for pattern in exercise.double_patterns
                ],
                "tempo_range": exercise.tempo_range,
                "difficulty_score": exercise.difficulty_score,
                "breath_points": exercise.breath_points,
                "learning_objectives": exercise.learning_objectives,
                "common_mistakes": exercise.common_mistakes,
                "practice_techniques": exercise.practice_techniques,
                "mastery_criteria": exercise.mastery_criteria
            }
            exercises_data.append(exercise_dict)

        return json.dumps(exercises_data, indent=2, ensure_ascii=False)

# Initialize the generator
janta_generator = JantaPatternGenerator()

# Export functions for API use
def get_janta_exercises() -> List[JantaExercise]:
    """Get all Janta Varisai exercises"""
    return janta_generator.janta_exercises

def get_janta_exercise(level: int) -> Optional[JantaExercise]:
    """Get specific Janta exercise"""
    return janta_generator.get_exercise_by_level(level)

def analyze_janta_performance(
    audio_data: np.ndarray,
    expected_transitions: List[Tuple[str, str]]
) -> List[TransitionAnalysis]:
    """Analyze Janta Varisai performance"""
    return janta_generator.analyze_transition_quality(audio_data, expected_transitions)

def generate_janta_practice_session(
    level: int,
    duration: int,
    focus_areas: List[str] = None
) -> Dict[str, Any]:
    """Generate Janta practice session"""
    return janta_generator.generate_practice_sequence(level, duration, focus_areas)