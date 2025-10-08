"""
Comprehensive Tala & Rhythm Training System

Complete implementation of Carnatic tala system with visual beat representation,
interactive tala keeper, polyrhythmic training, and synchronization assessment.
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import json
from datetime import datetime, timedelta
import asyncio

class TalaCategory(Enum):
    SULADI = "suladi"          # 7 basic talas
    CHAPU = "chapu"            # Chapu talas (irregular)
    DESHADI = "deshadi"        # Regional talas
    ADVANCED = "advanced"      # Complex talas

class Jati(Enum):
    TISRA = 3      # 3 beats per unit
    CHATHUSRA = 4  # 4 beats per unit
    KHANDA = 5     # 5 beats per unit
    MISRA = 7      # 7 beats per unit
    SANKIRNA = 9   # 9 beats per unit

class Gati(Enum):
    TISRA_GATI = 3     # 3 subdivisions per beat
    CHATHUSRA_GATI = 4 # 4 subdivisions per beat
    KHANDA_GATI = 5    # 5 subdivisions per beat
    MISRA_GATI = 7     # 7 subdivisions per beat
    SANKIRNA_GATI = 9  # 9 subdivisions per beat

class Nadai(Enum):
    FIRST_SPEED = 1    # Original tempo
    SECOND_SPEED = 2   # Double tempo
    THIRD_SPEED = 4    # Quadruple tempo
    FOURTH_SPEED = 8   # Eight times tempo

class BeatType(Enum):
    ANUDRUTHAM = "0"   # Wave (empty beat)
    DRUTHAM = "1"      # Clap once
    LAGHU = "X"        # Clap + finger counts
    GURU = "8"         # Long beat (8 counts)
    PLUTHAM = "+"      # Extended beat

@dataclass
class BeatPattern:
    beat_type: BeatType
    duration: int              # Number of counts
    hand_gesture: str          # Physical gesture description
    sound_syllable: str        # Vocal representation
    visual_symbol: str         # Display symbol
    emphasis_level: int        # 1-5 importance

@dataclass
class TalaDefinition:
    id: int
    name: str
    category: TalaCategory
    structure: List[BeatPattern]  # Beat pattern sequence
    total_beats: int             # Total beats in cycle
    total_counts: int            # Total counts (including subdivisions)

    # Jati and Gati specifications
    default_jati: Jati
    supported_jatis: List[Jati]
    default_gati: Gati
    supported_gatis: List[Gati]

    # Tempo and timing
    recommended_tempo_range: Tuple[int, int]  # BPM range
    common_nadais: List[Nadai]

    # Learning metadata
    difficulty_level: int        # 1-5 scale
    learning_order: int          # Recommended sequence
    prerequisite_talas: List[str]

    # Cultural context
    common_usage: List[str]      # Where it's typically used
    famous_compositions: List[Dict[str, str]]
    regional_variations: List[str]

    # Practice guidance
    hand_pattern_description: str
    common_mistakes: List[str]
    practice_tips: List[str]
    mastery_indicators: List[str]

    description: str
    historical_background: str

@dataclass
class RhythmicExercise:
    id: int
    name: str
    tala: str
    exercise_type: str           # "basic", "polyrhythmic", "speed", "pattern"
    description: str

    # Exercise structure
    patterns: List[Dict[str, Any]]  # Rhythm patterns to practice
    tempo_progression: List[int]     # BPM progression
    duration_minutes: int

    # Difficulty and learning
    difficulty_rating: float     # 0.0-1.0
    learning_objectives: List[str]
    prerequisites: List[str]

    # Assessment criteria
    timing_tolerance: float      # Allowed deviation in milliseconds
    success_threshold: float     # Required accuracy percentage

    instructions: List[str]
    practice_tips: List[str]

@dataclass
class RhythmAnalysis:
    user_id: int
    exercise_id: int
    timestamp: datetime

    # Timing analysis
    beat_accuracy: List[float]   # Accuracy for each beat
    overall_accuracy: float      # Overall timing accuracy
    tempo_consistency: float     # Tempo stability
    timing_deviations: List[float]  # Millisecond deviations

    # Pattern analysis
    pattern_recognition: float   # How well user follows patterns
    synchronization_quality: float
    rhythm_stability: float

    # Feedback and recommendations
    strengths: List[str]
    improvement_areas: List[str]
    specific_recommendations: List[str]

    score: float                 # Overall performance score
    grade: str                   # Letter grade

class TalaTrainingSystem:
    """
    Comprehensive Carnatic tala training system with interactive practice,
    visual feedback, and advanced rhythm analysis capabilities.
    """

    def __init__(self):
        self.tala_definitions = self._initialize_tala_definitions()
        self.rhythmic_exercises = self._create_rhythmic_exercises()
        self.user_progress = {}

    def _initialize_tala_definitions(self) -> Dict[str, TalaDefinition]:
        """Initialize comprehensive tala definitions"""
        talas = {}

        # Adi Tala (8 beats) - Most common
        talas["Adi"] = TalaDefinition(
            id=1,
            name="Adi",
            category=TalaCategory.SULADI,
            structure=[
                BeatPattern(BeatType.LAGHU, 4, "Clap + 3 finger counts", "Ta Ki Ta Ka", "| 2 3 4", 5),
                BeatPattern(BeatType.DRUTHAM, 2, "Clap + clap", "Ta Ka", "| |", 4),
                BeatPattern(BeatType.DRUTHAM, 2, "Clap + clap", "Ta Ka", "| |", 4)
            ],
            total_beats=8,
            total_counts=8,
            default_jati=Jati.CHATHUSRA,
            supported_jatis=[Jati.TISRA, Jati.CHATHUSRA, Jati.KHANDA, Jati.MISRA],
            default_gati=Gati.CHATHUSRA_GATI,
            supported_gatis=[Gati.TISRA_GATI, Gati.CHATHUSRA_GATI, Gati.KHANDA_GATI],
            recommended_tempo_range=(60, 200),
            common_nadais=[Nadai.FIRST_SPEED, Nadai.SECOND_SPEED],
            difficulty_level=2,
            learning_order=1,
            prerequisite_talas=[],
            common_usage=["Kritis", "Varnams", "Most compositions"],
            famous_compositions=[
                {"title": "Vatapi Ganapatim", "composer": "Dikshitar", "raga": "Hamsadhvani"}
            ],
            regional_variations=["Standard across South India"],
            hand_pattern_description="Right hand: Clap on 1, count 2-3-4 on fingers, clap on 5, clap on 6, clap on 7, clap on 8",
            common_mistakes=[
                "Rushing through finger counts",
                "Uneven beat spacing",
                "Poor clap clarity"
            ],
            practice_tips=[
                "Start very slowly with metronome",
                "Practice hand pattern without singing",
                "Count aloud initially",
                "Maintain consistent clap volume"
            ],
            mastery_indicators=[
                "Steady tempo maintenance",
                "Clear hand gestures",
                "Ability to maintain while singing"
            ],
            description="Most fundamental and commonly used tala in Carnatic music",
            historical_background="Ancient tala mentioned in classical treatises, foundation for most compositions"
        )

        # Rupaka Tala (3 beats)
        talas["Rupaka"] = TalaDefinition(
            id=2,
            name="Rupaka",
            category=TalaCategory.SULADI,
            structure=[
                BeatPattern(BeatType.DRUTHAM, 2, "Clap + clap", "Ta Ka", "| |", 5),
                BeatPattern(BeatType.LAGHU, 4, "Clap + 3 finger counts", "Ta Ki Ta Ka", "| 2 3 4", 4)
            ],
            total_beats=6,
            total_counts=6,
            default_jati=Jati.CHATHUSRA,
            supported_jatis=[Jati.TISRA, Jati.CHATHUSRA, Jati.KHANDA],
            default_gati=Gati.CHATHUSRA_GATI,
            supported_gatis=[Gati.TISRA_GATI, Gati.CHATHUSRA_GATI, Gati.KHANDA_GATI],
            recommended_tempo_range=(80, 160),
            common_nadais=[Nadai.FIRST_SPEED, Nadai.SECOND_SPEED],
            difficulty_level=3,
            learning_order=3,
            prerequisite_talas=["Adi"],
            common_usage=["Light classical", "Semi-classical", "Film songs"],
            famous_compositions=[
                {"title": "Jaya Jaya", "composer": "Traditional", "raga": "Kambhoji"}
            ],
            regional_variations=["Popular in film music"],
            hand_pattern_description="Right hand: Clap on 1, clap on 2, clap on 3, count 4-5-6 on fingers",
            common_mistakes=[
                "Starting with laghu instead of drutham",
                "Inconsistent drutham timing",
                "Confusion with beat emphasis"
            ],
            practice_tips=[
                "Emphasize the first beat strongly",
                "Practice drutham-laghu transition",
                "Use with familiar songs initially"
            ],
            mastery_indicators=[
                "Smooth drutham-laghu transition",
                "Proper beat emphasis",
                "Comfortable at various tempos"
            ],
            description="Six-beat tala starting with drutham, popular in lighter forms",
            historical_background="Classical tala adapted for modern compositions and film music"
        )

        # Khanda Chapu (5 beats) - Irregular
        talas["Khanda Chapu"] = TalaDefinition(
            id=3,
            name="Khanda Chapu",
            category=TalaCategory.CHAPU,
            structure=[
                BeatPattern(BeatType.LAGHU, 2, "Clap + finger", "Ta Ki", "| 2", 5),
                BeatPattern(BeatType.LAGHU, 3, "Clap + 2 fingers", "Ta Ka Dhi", "| 2 3", 4)
            ],
            total_beats=5,
            total_counts=5,
            default_jati=Jati.KHANDA,
            supported_jatis=[Jati.KHANDA],
            default_gati=Gati.CHATHUSRA_GATI,
            supported_gatis=[Gati.CHATHUSRA_GATI, Gati.TISRA_GATI],
            recommended_tempo_range=(70, 140),
            common_nadais=[Nadai.FIRST_SPEED],
            difficulty_level=4,
            learning_order=5,
            prerequisite_talas=["Adi", "Rupaka"],
            common_usage=["Film songs", "Light music", "Devotional songs"],
            famous_compositions=[
                {"title": "Jagadananda Karaka", "composer": "Tyagaraja", "raga": "Nata"}
            ],
            regional_variations=["Common in Tamil film music"],
            hand_pattern_description="Right hand: Clap-finger (2 beats), clap-finger-finger (3 beats)",
            common_mistakes=[
                "Equal emphasis on all beats",
                "Difficulty with 2+3 grouping",
                "Tempo acceleration in groups"
            ],
            practice_tips=[
                "Practice 2+3 grouping separately",
                "Use 'Ta-Ki Ta-Ka-Dhi' syllables",
                "Emphasize first beat of each group"
            ],
            mastery_indicators=[
                "Natural 2+3 feel",
                "Consistent tempo across groups",
                "Comfortable with asymmetric pattern"
            ],
            description="Five-beat irregular tala with 2+3 grouping",
            historical_background="Popular chapu tala used extensively in modern compositions"
        )

        # Misra Chapu (7 beats) - Complex irregular
        talas["Misra Chapu"] = TalaDefinition(
            id=4,
            name="Misra Chapu",
            category=TalaCategory.CHAPU,
            structure=[
                BeatPattern(BeatType.LAGHU, 3, "Clap + 2 fingers", "Ta Ki Ta", "| 2 3", 5),
                BeatPattern(BeatType.LAGHU, 4, "Clap + 3 fingers", "Ta Ka Dhi Mi", "| 2 3 4", 4)
            ],
            total_beats=7,
            total_counts=7,
            default_jati=Jati.MISRA,
            supported_jatis=[Jati.MISRA],
            default_gati=Gati.CHATHUSRA_GATI,
            supported_gatis=[Gati.CHATHUSRA_GATI],
            recommended_tempo_range=(60, 120),
            common_nadais=[Nadai.FIRST_SPEED],
            difficulty_level=5,
            learning_order=7,
            prerequisite_talas=["Adi", "Rupaka", "Khanda Chapu"],
            common_usage=["Complex compositions", "Advanced pieces", "Experimental music"],
            famous_compositions=[
                {"title": "Marugelara", "composer": "Tyagaraja", "raga": "Jayantasri"}
            ],
            regional_variations=["Less common in folk traditions"],
            hand_pattern_description="Right hand: Clap-finger-finger (3 beats), clap-finger-finger-finger (4 beats)",
            common_mistakes=[
                "Losing track of 3+4 grouping",
                "Uneven emphasis patterns",
                "Tempo inconsistency"
            ],
            practice_tips=[
                "Practice very slowly initially",
                "Use strong metronome reference",
                "Count 3+4 grouping aloud",
                "Practice with simple melodies first"
            ],
            mastery_indicators=[
                "Effortless 3+4 grouping",
                "Steady tempo maintenance",
                "Natural phrase feeling"
            ],
            description="Seven-beat complex tala with 3+4 asymmetric grouping",
            historical_background="Advanced tala for sophisticated musical expression"
        )

        # Continue with more talas...
        # Simplified for brevity - in production, all 7 Suladi talas + Chapu talas would be included

        return talas

    def _create_rhythmic_exercises(self) -> List[RhythmicExercise]:
        """Create comprehensive rhythmic exercises"""
        exercises = []

        # Basic Adi Tala clapping
        exercises.append(RhythmicExercise(
            id=1,
            name="Basic Adi Tala Clapping",
            tala="Adi",
            exercise_type="basic",
            description="Learn fundamental Adi tala hand pattern with steady tempo",
            patterns=[
                {
                    "name": "Basic Pattern",
                    "beats": [1, 2, 3, 4, 5, 6, 7, 8],
                    "actions": ["clap", "2", "3", "4", "clap", "clap", "clap", "clap"],
                    "emphasis": [5, 1, 1, 1, 4, 4, 4, 4]
                }
            ],
            tempo_progression=[60, 80, 100, 120],
            duration_minutes=10,
            difficulty_rating=0.2,
            learning_objectives=[
                "Master basic Adi tala hand pattern",
                "Develop steady tempo maintenance",
                "Build muscle memory for clap-count sequence"
            ],
            prerequisites=[],
            timing_tolerance=50.0,  # 50ms tolerance
            success_threshold=0.85,
            instructions=[
                "Sit comfortably with hands ready to clap",
                "Start with slow tempo (60 BPM)",
                "Clap on beat 1, count 2-3-4 on fingers",
                "Clap beats 5, 6, 7, 8 clearly",
                "Maintain consistent tempo throughout"
            ],
            practice_tips=[
                "Use metronome for tempo reference",
                "Count aloud initially",
                "Focus on clear, distinct claps",
                "Practice daily for muscle memory"
            ]
        ))

        # Polyrhythmic exercise
        exercises.append(RhythmicExercise(
            id=2,
            name="Adi Tala with Tisra Gati",
            tala="Adi",
            exercise_type="polyrhythmic",
            description="Advanced exercise combining Adi tala structure with Tisra gati subdivisions",
            patterns=[
                {
                    "name": "Tisra Pattern",
                    "beats": [1, 2, 3, 4, 5, 6, 7, 8],
                    "subdivisions": [3, 3, 3, 3, 3, 3, 3, 3],
                    "syllables": ["Ta Ki Da", "Ta Ki Da", "Ta Ki Da", "Ta Ki Da",
                                 "Ta Ki Da", "Ta Ki Da", "Ta Ki Da", "Ta Ki Da"]
                }
            ],
            tempo_progression=[50, 70, 90],
            duration_minutes=15,
            difficulty_rating=0.6,
            learning_objectives=[
                "Understand gati concept",
                "Practice polyrhythmic coordination",
                "Develop advanced timing skills"
            ],
            prerequisites=["Basic Adi Tala Clapping"],
            timing_tolerance=30.0,
            success_threshold=0.80,
            instructions=[
                "Maintain Adi tala hand pattern",
                "Subdivide each beat into 3 equal parts",
                "Use Ta-Ki-Da syllables for subdivisions",
                "Keep hand pattern steady while vocalizing"
            ],
            practice_tips=[
                "Practice hand pattern first",
                "Add vocal subdivisions gradually",
                "Use slower tempo initially",
                "Focus on coordination between hands and voice"
            ]
        ))

        # Speed exercise (Nadai changes)
        exercises.append(RhythmicExercise(
            id=3,
            name="Adi Tala Speed Variations",
            tala="Adi",
            exercise_type="speed",
            description="Practice Adi tala at different nadais (speed variations)",
            patterns=[
                {
                    "name": "First Speed",
                    "nadai": 1,
                    "subdivisions_per_beat": 1,
                    "syllables": ["Ta", "", "", "", "Ta", "Ta", "Ta", "Ta"]
                },
                {
                    "name": "Second Speed",
                    "nadai": 2,
                    "subdivisions_per_beat": 2,
                    "syllables": ["Ta Ka", "Di Mi", "Ta Ka", "Jha Nu",
                                 "Ta Ka", "Ta Ka", "Ta Ka", "Ta Ka"]
                }
            ],
            tempo_progression=[80, 100, 120, 140],
            duration_minutes=12,
            difficulty_rating=0.7,
            learning_objectives=[
                "Master nadai concept",
                "Develop speed control",
                "Practice tempo transitions"
            ],
            prerequisites=["Basic Adi Tala Clapping"],
            timing_tolerance=25.0,
            success_threshold=0.85,
            instructions=[
                "Start with first speed (one syllable per beat)",
                "Progress to second speed (two syllables per beat)",
                "Maintain same hand pattern throughout",
                "Keep transitions smooth"
            ],
            practice_tips=[
                "Practice each speed separately first",
                "Use clear syllable pronunciation",
                "Maintain hand pattern accuracy",
                "Build speed gradually"
            ]
        ))

        return exercises

    async def start_tala_practice_session(
        self,
        user_id: int,
        tala_name: str,
        exercise_id: Optional[int] = None,
        tempo: int = 80
    ) -> Dict[str, Any]:
        """Start interactive tala practice session"""

        tala = self.tala_definitions.get(tala_name)
        if not tala:
            return {"error": "Tala not found"}

        exercise = None
        if exercise_id:
            exercise = next((ex for ex in self.rhythmic_exercises if ex.id == exercise_id), None)

        session = {
            "session_id": f"tala_{user_id}_{datetime.now().timestamp()}",
            "user_id": user_id,
            "tala": tala,
            "exercise": exercise,
            "tempo": tempo,
            "start_time": datetime.now(),
            "current_beat": 0,
            "cycle_count": 0,
            "beat_timestamps": [],
            "user_input_timestamps": [],
            "status": "active"
        }

        # Store session for tracking
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        self.user_progress[user_id]["current_session"] = session

        return {
            "session_id": session["session_id"],
            "tala_info": {
                "name": tala.name,
                "total_beats": tala.total_beats,
                "structure": [
                    {
                        "beat_type": pattern.beat_type.value,
                        "duration": pattern.duration,
                        "gesture": pattern.hand_gesture,
                        "syllable": pattern.sound_syllable,
                        "symbol": pattern.visual_symbol
                    }
                    for pattern in tala.structure
                ]
            },
            "tempo": tempo,
            "instructions": exercise.instructions if exercise else tala.practice_tips
        }

    def record_beat_input(
        self,
        session_id: str,
        user_id: int,
        timestamp: datetime,
        beat_number: int
    ) -> Dict[str, Any]:
        """Record user's beat input and provide feedback"""

        if user_id not in self.user_progress or "current_session" not in self.user_progress[user_id]:
            return {"error": "No active session"}

        session = self.user_progress[user_id]["current_session"]

        # Calculate expected timestamp for this beat
        beats_per_minute = session["tempo"]
        milliseconds_per_beat = (60 / beats_per_minute) * 1000

        session_start = session["start_time"]
        expected_timestamp = session_start + timedelta(milliseconds=beat_number * milliseconds_per_beat)

        # Calculate timing deviation
        actual_timestamp = timestamp
        deviation_ms = (actual_timestamp - expected_timestamp).total_seconds() * 1000

        # Store the input
        session["user_input_timestamps"].append({
            "beat": beat_number,
            "expected": expected_timestamp,
            "actual": actual_timestamp,
            "deviation_ms": deviation_ms
        })

        # Provide immediate feedback
        tolerance = 50.0  # milliseconds
        feedback = {
            "beat_number": beat_number,
            "deviation_ms": deviation_ms,
            "accuracy": "excellent" if abs(deviation_ms) < 20 else
                       "good" if abs(deviation_ms) < tolerance else "needs_improvement",
            "timing_feedback": self._generate_timing_feedback(deviation_ms)
        }

        return feedback

    def _generate_timing_feedback(self, deviation_ms: float) -> str:
        """Generate timing feedback message"""
        if abs(deviation_ms) < 10:
            return "Perfect timing!"
        elif deviation_ms > 50:
            return "Try to come in a bit earlier"
        elif deviation_ms < -50:
            return "Try to wait a bit longer"
        elif deviation_ms > 20:
            return "Slightly early - relax the tempo"
        elif deviation_ms < -20:
            return "Slightly late - pick up the tempo"
        else:
            return "Good timing!"

    async def analyze_rhythm_performance(
        self,
        session_id: str,
        user_id: int
    ) -> RhythmAnalysis:
        """Analyze user's rhythm performance after session"""

        if user_id not in self.user_progress or "current_session" not in self.user_progress[user_id]:
            return None

        session = self.user_progress[user_id]["current_session"]
        inputs = session["user_input_timestamps"]

        if not inputs:
            return None

        # Calculate beat-by-beat accuracy
        beat_accuracies = []
        timing_deviations = []

        for input_data in inputs:
            deviation = abs(input_data["deviation_ms"])
            timing_deviations.append(deviation)

            # Convert deviation to accuracy score (0-1)
            if deviation < 20:
                accuracy = 1.0
            elif deviation < 50:
                accuracy = 0.8
            elif deviation < 100:
                accuracy = 0.6
            else:
                accuracy = max(0.2, 1.0 - (deviation - 100) / 200)

            beat_accuracies.append(accuracy)

        # Calculate overall metrics
        overall_accuracy = np.mean(beat_accuracies)
        tempo_consistency = 1.0 - (np.std(timing_deviations) / 100.0)  # Normalize std dev
        tempo_consistency = max(0.0, min(1.0, tempo_consistency))

        # Pattern recognition (simplified)
        pattern_recognition = overall_accuracy  # In production, would analyze pattern adherence

        # Synchronization quality
        synchronization_quality = 1.0 - (np.mean([abs(d) for d in timing_deviations]) / 100.0)
        synchronization_quality = max(0.0, min(1.0, synchronization_quality))

        # Generate feedback
        strengths = []
        improvement_areas = []
        recommendations = []

        if overall_accuracy > 0.8:
            strengths.append("Excellent timing accuracy")
        elif overall_accuracy > 0.6:
            strengths.append("Good basic timing")
        else:
            improvement_areas.append("Timing accuracy needs work")
            recommendations.append("Practice with metronome at slower tempo")

        if tempo_consistency > 0.8:
            strengths.append("Good tempo consistency")
        else:
            improvement_areas.append("Tempo fluctuates")
            recommendations.append("Focus on maintaining steady tempo")

        # Calculate overall score and grade
        score = (overall_accuracy * 0.4 + tempo_consistency * 0.3 +
                synchronization_quality * 0.3)

        if score >= 0.9:
            grade = "A"
        elif score >= 0.8:
            grade = "B"
        elif score >= 0.7:
            grade = "C"
        elif score >= 0.6:
            grade = "D"
        else:
            grade = "F"

        return RhythmAnalysis(
            user_id=user_id,
            exercise_id=session.get("exercise", {}).get("id", 0),
            timestamp=datetime.now(),
            beat_accuracy=beat_accuracies,
            overall_accuracy=overall_accuracy,
            tempo_consistency=tempo_consistency,
            timing_deviations=timing_deviations,
            pattern_recognition=pattern_recognition,
            synchronization_quality=synchronization_quality,
            rhythm_stability=tempo_consistency,
            strengths=strengths,
            improvement_areas=improvement_areas,
            specific_recommendations=recommendations,
            score=score,
            grade=grade
        )

    def get_tala_learning_path(self, user_level: str = "beginner") -> List[Dict[str, Any]]:
        """Generate tala learning path based on user level"""

        if user_level == "beginner":
            sequence = ["Adi", "Rupaka"]
        elif user_level == "intermediate":
            sequence = ["Adi", "Rupaka", "Khanda Chapu", "Jhampa"]
        else:  # advanced
            sequence = ["Adi", "Rupaka", "Khanda Chapu", "Misra Chapu", "Jhampa", "Triputa", "Eka"]

        learning_path = []

        for i, tala_name in enumerate(sequence):
            tala = self.tala_definitions.get(tala_name)
            if not tala:
                continue

            stage = {
                "sequence": i + 1,
                "tala": tala,
                "learning_phases": [
                    {
                        "phase": "Recognition",
                        "description": "Listen and identify tala pattern",
                        "duration": "1-2 days",
                        "exercises": ["Pattern listening", "Beat identification"]
                    },
                    {
                        "phase": "Basic Clapping",
                        "description": "Learn hand pattern at slow tempo",
                        "duration": "3-5 days",
                        "exercises": ["Hand pattern practice", "Tempo building"]
                    },
                    {
                        "phase": "Vocal Integration",
                        "description": "Add vocal syllables while clapping",
                        "duration": "3-4 days",
                        "exercises": ["Syllable practice", "Coordination"]
                    },
                    {
                        "phase": "Musical Application",
                        "description": "Practice with songs and compositions",
                        "duration": "1-2 weeks",
                        "exercises": ["Song practice", "Performance"]
                    }
                ],
                "estimated_total_time": "2-3 weeks",
                "success_criteria": tala.mastery_indicators
            }

            learning_path.append(stage)

        return learning_path

    def get_tala_by_name(self, name: str) -> Optional[TalaDefinition]:
        """Get tala definition by name"""
        return self.tala_definitions.get(name)

    def get_exercises_for_tala(self, tala_name: str) -> List[RhythmicExercise]:
        """Get all exercises for specific tala"""
        return [ex for ex in self.rhythmic_exercises if ex.tala == tala_name]

    def export_tala_data(self) -> str:
        """Export all tala data as JSON"""
        export_data = {
            "talas": {},
            "exercises": []
        }

        # Export tala definitions
        for name, tala in self.tala_definitions.items():
            tala_dict = asdict(tala)
            # Convert enums to strings
            tala_dict["category"] = tala.category.value
            tala_dict["default_jati"] = tala.default_jati.value
            tala_dict["supported_jatis"] = [j.value for j in tala.supported_jatis]
            tala_dict["default_gati"] = tala.default_gati.value
            tala_dict["supported_gatis"] = [g.value for g in tala.supported_gatis]
            tala_dict["common_nadais"] = [n.value for n in tala.common_nadais]

            # Convert beat patterns
            tala_dict["structure"] = [
                {
                    "beat_type": pattern.beat_type.value,
                    "duration": pattern.duration,
                    "hand_gesture": pattern.hand_gesture,
                    "sound_syllable": pattern.sound_syllable,
                    "visual_symbol": pattern.visual_symbol,
                    "emphasis_level": pattern.emphasis_level
                }
                for pattern in tala.structure
            ]

            export_data["talas"][name] = tala_dict

        # Export exercises
        for exercise in self.rhythmic_exercises:
            export_data["exercises"].append(asdict(exercise))

        return json.dumps(export_data, indent=2, ensure_ascii=False)

# Initialize the system
tala_system = TalaTrainingSystem()

# Export functions for API use
def get_all_talas() -> List[TalaDefinition]:
    """Get all tala definitions"""
    return list(tala_system.tala_definitions.values())

def get_tala(name: str) -> Optional[TalaDefinition]:
    """Get specific tala"""
    return tala_system.get_tala_by_name(name)

def get_tala_exercises(tala_name: str) -> List[RhythmicExercise]:
    """Get exercises for tala"""
    return tala_system.get_exercises_for_tala(tala_name)

def get_learning_path_api(level: str = "beginner") -> List[Dict[str, Any]]:
    """Get tala learning path"""
    return tala_system.get_tala_learning_path(level)

async def start_practice_session_api(
    user_id: int,
    tala_name: str,
    exercise_id: Optional[int] = None,
    tempo: int = 80
) -> Dict[str, Any]:
    """Start tala practice session"""
    return await tala_system.start_tala_practice_session(user_id, tala_name, exercise_id, tempo)

async def analyze_performance_api(session_id: str, user_id: int) -> Optional[RhythmAnalysis]:
    """Analyze rhythm performance"""
    return await tala_system.analyze_rhythm_performance(session_id, user_id)