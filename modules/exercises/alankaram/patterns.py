"""
Alankaram Exercise Patterns

Implementation of traditional Carnatic ornamentation and pattern exercises
with raga integration and advanced melodic complexity frameworks.
"""

from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
import json
from datetime import datetime

class AlanakaramType(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    RAGA_SPECIFIC = "raga_specific"
    ADVANCED = "advanced"
    CREATIVE = "creative"

class OrnanmentationType(Enum):
    KAMPANA = "kampana"  # Oscillation
    ANDOLANA = "andolana"  # Swing
    SPURITA = "spurita"  # Grace note
    PRATYAHATA = "pratyahata"  # Rebound
    TRIPUCCHA = "tripuccha"  # Triple shake

class ComplexityLevel(Enum):
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

@dataclass
class MelodicPhrase:
    swaras: List[str]
    octave_shifts: List[int]  # -1, 0, 1 for lower, middle, upper octaves
    duration_ratios: List[float]
    ornamentations: List[Optional[OrnanmentationType]]
    emphasis_points: List[int]
    phrase_type: str
    difficulty_weight: float

@dataclass
class AlanakaramPattern:
    id: int
    name: str
    type: AlanakaramType
    complexity_level: ComplexityLevel
    description: str
    phrases: List[MelodicPhrase]
    raga_compatibility: List[str]  # Compatible ragas
    tala_compatibility: List[str]  # Compatible talas
    tempo_recommendations: Tuple[int, int]
    learning_objectives: List[str]
    prerequisites: List[int]  # Required pattern IDs
    mastery_indicators: Dict[str, float]
    cultural_context: str
    traditional_usage: List[str]

@dataclass
class RagaIntegration:
    raga_name: str
    arohanam: List[str]
    avarohanam: List[str]
    characteristic_phrases: List[List[str]]
    forbidden_combinations: List[List[str]]
    ornament_preferences: Dict[str, List[OrnanmentationType]]
    emotional_character: str
    practice_recommendations: List[str]

class AlanakaramPatternGenerator:
    """
    Comprehensive Alankaram pattern generator with traditional authenticity
    and advanced pedagogical frameworks for Carnatic music education.
    """

    def __init__(self):
        self.base_swaras = ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']
        self.swara_variants = {
            'Ri': ['Ri1', 'Ri2', 'Ri3'],  # Shuddha, Chathushruti, Shatshruti
            'Ga': ['Ga1', 'Ga2', 'Ga3'],  # Shuddha, Saadhaarana, Antara
            'Ma': ['Ma1', 'Ma2'],          # Shuddha, Prati
            'Da': ['Da1', 'Da2', 'Da3'],  # Shuddha, Chathushruti, Shatshruti
            'Ni': ['Ni1', 'Ni2', 'Ni3']   # Shuddha, Kaisika, Kaakali
        }

        self.raga_database = self._initialize_raga_database()
        self.alankaram_patterns = self._generate_all_patterns()

    def _initialize_raga_database(self) -> Dict[str, RagaIntegration]:
        """Initialize comprehensive raga database with characteristics"""
        ragas = {}

        # Mayamalavagowla (15th Melakarta)
        ragas['Mayamalavagowla'] = RagaIntegration(
            raga_name="Mayamalavagowla",
            arohanam=['Sa', 'Ri1', 'Ga3', 'Ma1', 'Pa', 'Da1', 'Ni3'],
            avarohanam=['Sa', 'Ni3', 'Da1', 'Pa', 'Ma1', 'Ga3', 'Ri1', 'Sa'],
            characteristic_phrases=[
                ['Sa', 'Ri1', 'Ga3', 'Ma1'],
                ['Pa', 'Da1', 'Ni3', 'Sa'],
                ['Ga3', 'Ma1', 'Pa', 'Da1']
            ],
            forbidden_combinations=[
                ['Ri1', 'Ga1'],  # Avoid natural Ga with shuddha Ri
                ['Da1', 'Ni1']   # Avoid natural Ni with shuddha Da
            ],
            ornament_preferences={
                'Sa': [OrnanmentationType.KAMPANA],
                'Ga3': [OrnanmentationType.ANDOLANA],
                'Pa': [OrnanmentationType.SPURITA]
            },
            emotional_character="Devotional, serene, foundational",
            practice_recommendations=[
                "Start slowly to establish proper intonation",
                "Focus on clean transitions between Ri1 and Ga3",
                "Practice characteristic phrases repeatedly"
            ]
        )

        # Shankarabharanam (29th Melakarta)
        ragas['Shankarabharanam'] = RagaIntegration(
            raga_name="Shankarabharanam",
            arohanam=['Sa', 'Ri2', 'Ga3', 'Ma1', 'Pa', 'Da2', 'Ni3'],
            avarohanam=['Sa', 'Ni3', 'Da2', 'Pa', 'Ma1', 'Ga3', 'Ri2', 'Sa'],
            characteristic_phrases=[
                ['Sa', 'Ri2', 'Ga3', 'Pa'],
                ['Ma1', 'Pa', 'Da2', 'Sa'],
                ['Pa', 'Ma1', 'Ga3', 'Ri2']
            ],
            forbidden_combinations=[],
            ornament_preferences={
                'Ri2': [OrnanmentationType.KAMPANA],
                'Da2': [OrnanmentationType.ANDOLANA],
                'Ni3': [OrnanmentationType.SPURITA]
            },
            emotional_character="Joyful, complete, foundational",
            practice_recommendations=[
                "Practice as foundation for all major ragas",
                "Focus on perfect pitch relationships",
                "Use for advanced alankaram practice"
            ]
        )

        # Kalyani (65th Melakarta)
        ragas['Kalyani'] = RagaIntegration(
            raga_name="Kalyani",
            arohanam=['Sa', 'Ri2', 'Ga3', 'Ma2', 'Pa', 'Da2', 'Ni3'],
            avarohanam=['Sa', 'Ni3', 'Da2', 'Pa', 'Ma2', 'Ga3', 'Ri2', 'Sa'],
            characteristic_phrases=[
                ['Sa', 'Ri2', 'Ga3', 'Ma2'],
                ['Ma2', 'Pa', 'Da2', 'Ni3'],
                ['Ni3', 'Da2', 'Pa', 'Ma2']
            ],
            forbidden_combinations=[
                ['Ma1', 'Pa']  # Avoid natural Ma in Kalyani
            ],
            ornament_preferences={
                'Ma2': [OrnanmentationType.KAMPANA, OrnanmentationType.ANDOLANA],
                'Ni3': [OrnanmentationType.SPURITA]
            },
            emotional_character="Uplifting, devotional, expansive",
            practice_recommendations=[
                "Emphasize the characteristic Ma2 (Prati Madhyama)",
                "Practice smooth transitions around Ma2",
                "Focus on devotional expression"
            ]
        )

        return ragas

    def _generate_all_patterns(self) -> List[AlanakaramPattern]:
        """Generate comprehensive set of Alankaram patterns"""
        patterns = []

        # Simple patterns (1-7)
        patterns.extend(self._generate_simple_patterns())

        # Complex patterns (8-21)
        patterns.extend(self._generate_complex_patterns())

        # Raga-specific patterns (22-28)
        patterns.extend(self._generate_raga_specific_patterns())

        # Advanced patterns (29-35)
        patterns.extend(self._generate_advanced_patterns())

        return patterns

    def _generate_simple_patterns(self) -> List[AlanakaramPattern]:
        """Generate simple Alankaram patterns (1-7)"""
        patterns = []

        # Pattern 1: Sa Ri Sa, Sa Ga Sa, Sa Ma Sa...
        phrases = []
        for i, swara in enumerate(['Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']):
            phrases.append(MelodicPhrase(
                swaras=['Sa', swara, 'Sa'],
                octave_shifts=[0, 0, 0],
                duration_ratios=[0.5, 0.5, 1.0],
                ornamentations=[None, None, None],
                emphasis_points=[0, 2],
                phrase_type="returning_pattern",
                difficulty_weight=0.2
            ))

        patterns.append(AlanakaramPattern(
            id=1,
            name="Simple Returning Pattern",
            type=AlanakaramType.SIMPLE,
            complexity_level=ComplexityLevel.BEGINNER,
            description="Sa-X-Sa patterns for each swara",
            phrases=phrases,
            raga_compatibility=["Mayamalavagowla", "Shankarabharanam", "Kalyani"],
            tala_compatibility=["Adi", "Rupaka"],
            tempo_recommendations=(60, 120),
            learning_objectives=[
                "Establish Sa as reference point",
                "Practice accurate interval jumps",
                "Develop returning phrase technique"
            ],
            prerequisites=[],
            mastery_indicators={
                "pitch_accuracy": 0.9,
                "phrase_connection": 0.8,
                "tempo_consistency": 0.85
            },
            cultural_context="Foundation exercise for swara relationships",
            traditional_usage=["Basic training", "Warm-up exercises"]
        ))

        # Pattern 2: Sa Ri Ga Ri Sa, Sa Ga Ma Ga Sa...
        phrases = []
        swara_groups = [
            ['Sa', 'Ri', 'Ga', 'Ri', 'Sa'],
            ['Sa', 'Ga', 'Ma', 'Ga', 'Sa'],
            ['Sa', 'Ma', 'Pa', 'Ma', 'Sa'],
            ['Sa', 'Pa', 'Da', 'Pa', 'Sa'],
            ['Sa', 'Da', 'Ni', 'Da', 'Sa']
        ]

        for i, group in enumerate(swara_groups):
            phrases.append(MelodicPhrase(
                swaras=group,
                octave_shifts=[0] * len(group),
                duration_ratios=[0.5] * (len(group) - 1) + [1.0],
                ornamentations=[None] * len(group),
                emphasis_points=[0, len(group) - 1],
                phrase_type="extended_returning",
                difficulty_weight=0.3
            ))

        patterns.append(AlanakaramPattern(
            id=2,
            name="Extended Returning Patterns",
            type=AlanakaramType.SIMPLE,
            complexity_level=ComplexityLevel.ELEMENTARY,
            description="Three-note groups with return to Sa",
            phrases=phrases,
            raga_compatibility=["Mayamalavagowla", "Shankarabharanam"],
            tala_compatibility=["Adi", "Rupaka", "Khanda Chapu"],
            tempo_recommendations=(55, 110),
            learning_objectives=[
                "Develop three-note phrase control",
                "Practice melodic curves",
                "Strengthen Sa connection"
            ],
            prerequisites=[1],
            mastery_indicators={
                "phrase_smoothness": 0.85,
                "melodic_flow": 0.8,
                "return_accuracy": 0.9
            },
            cultural_context="Traditional phrase development exercise",
            traditional_usage=["Melodic training", "Phrase connection practice"]
        ))

        # Continue with patterns 3-7...
        # Pattern 3: Ascending sequences
        phrases = [MelodicPhrase(
            swaras=['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0, 0, 1],
            duration_ratios=[0.5] * 7 + [1.5],
            ornamentations=[None] * 8,
            emphasis_points=[0, 7],
            phrase_type="ascending_scale",
            difficulty_weight=0.4
        )]

        patterns.append(AlanakaramPattern(
            id=3,
            name="Ascending Scale Pattern",
            type=AlanakaramType.SIMPLE,
            complexity_level=ComplexityLevel.ELEMENTARY,
            description="Complete ascending scale with octave Sa",
            phrases=phrases,
            raga_compatibility=["Shankarabharanam", "Kalyani"],
            tala_compatibility=["Adi"],
            tempo_recommendations=(50, 100),
            learning_objectives=[
                "Master complete octave ascent",
                "Develop breath control for long phrases",
                "Practice octave jump technique"
            ],
            prerequisites=[1, 2],
            mastery_indicators={
                "octave_accuracy": 0.9,
                "breath_control": 0.8,
                "scale_evenness": 0.85
            },
            cultural_context="Fundamental scale training",
            traditional_usage=["Voice training", "Scale practice"]
        ))

        # Add more simple patterns (4-7) following similar structure...

        return patterns

    def _generate_complex_patterns(self) -> List[AlanakaramPattern]:
        """Generate complex Alankaram patterns (8-21)"""
        patterns = []

        # Pattern 8: Alternating jump patterns
        phrases = []
        alternating_groups = [
            ['Sa', 'Ga', 'Ri', 'Ma', 'Ga', 'Pa'],
            ['Ma', 'Da', 'Pa', 'Ni', 'Da', 'Sa']
        ]

        for group in alternating_groups:
            phrases.append(MelodicPhrase(
                swaras=group,
                octave_shifts=[0] * len(group),
                duration_ratios=[0.75] * (len(group) - 1) + [1.0],
                ornamentations=[None, OrnanmentationType.SPURITA, None] * (len(group) // 3 + 1),
                emphasis_points=[0, len(group) - 1],
                phrase_type="alternating_jumps",
                difficulty_weight=0.6
            ))

        patterns.append(AlanakaramPattern(
            id=8,
            name="Alternating Jump Patterns",
            type=AlanakaramType.COMPLEX,
            complexity_level=ComplexityLevel.INTERMEDIATE,
            description="Skip-step patterns with alternating movements",
            phrases=phrases,
            raga_compatibility=["Shankarabharanam", "Kalyani"],
            tala_compatibility=["Adi", "Rupaka"],
            tempo_recommendations=(65, 125),
            learning_objectives=[
                "Master interval jumping technique",
                "Develop alternating movement control",
                "Practice complex melodic sequences"
            ],
            prerequisites=[1, 2, 3],
            mastery_indicators={
                "jump_accuracy": 0.85,
                "movement_control": 0.8,
                "pattern_consistency": 0.85
            },
            cultural_context="Advanced melodic movement training",
            traditional_usage=["Technical development", "Flexibility training"]
        ))

        # Add more complex patterns (9-21)...

        return patterns

    def _generate_raga_specific_patterns(self) -> List[AlanakaramPattern]:
        """Generate raga-specific Alankaram patterns (22-28)"""
        patterns = []

        # Pattern 22: Mayamalavagowla specific
        mayamalavagowla_phrases = [
            MelodicPhrase(
                swaras=['Sa', 'Ri1', 'Ga3', 'Ma1', 'Pa', 'Ma1', 'Ga3', 'Ri1'],
                octave_shifts=[0] * 8,
                duration_ratios=[0.5, 0.5, 1.0, 0.5, 0.75, 0.5, 0.75, 1.0],
                ornamentations=[None, None, OrnanmentationType.ANDOLANA, None,
                              OrnanmentationType.SPURITA, None, OrnanmentationType.KAMPANA, None],
                emphasis_points=[0, 2, 4, 7],
                phrase_type="raga_characteristic",
                difficulty_weight=0.7
            )
        ]

        patterns.append(AlanakaramPattern(
            id=22,
            name="Mayamalavagowla Characteristic Pattern",
            type=AlanakaramType.RAGA_SPECIFIC,
            complexity_level=ComplexityLevel.INTERMEDIATE,
            description="Characteristic phrases of Mayamalavagowla raga",
            phrases=mayamalavagowla_phrases,
            raga_compatibility=["Mayamalavagowla"],
            tala_compatibility=["Adi", "Rupaka"],
            tempo_recommendations=(55, 105),
            learning_objectives=[
                "Master Mayamalavagowla phrase structure",
                "Develop raga-specific ornamentations",
                "Practice devotional expression"
            ],
            prerequisites=[1, 2, 3, 8],
            mastery_indicators={
                "raga_authenticity": 0.9,
                "ornamentation_quality": 0.8,
                "emotional_expression": 0.8
            },
            cultural_context="First melakarta raga training",
            traditional_usage=["Raga introduction", "Devotional practice"]
        ))

        # Add more raga-specific patterns...

        return patterns

    def _generate_advanced_patterns(self) -> List[AlanakaramPattern]:
        """Generate advanced Alankaram patterns (29-35)"""
        patterns = []

        # Pattern 29: Complex ornamented pattern
        advanced_phrases = [
            MelodicPhrase(
                swaras=['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa', 'Ni', 'Da', 'Pa', 'Ma'],
                octave_shifts=[0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                duration_ratios=[0.25, 0.5, 0.75, 0.5, 1.0, 0.5, 0.75, 1.5, 0.5, 0.75, 0.5, 1.0],
                ornamentations=[
                    None, OrnanmentationType.KAMPANA, OrnanmentationType.ANDOLANA,
                    OrnanmentationType.SPURITA, None, OrnanmentationType.KAMPANA,
                    OrnanmentationType.TRIPUCCHA, None, OrnanmentationType.ANDOLANA,
                    None, OrnanmentationType.SPURITA, None
                ],
                emphasis_points=[0, 4, 7, 11],
                phrase_type="advanced_ornamented",
                difficulty_weight=0.9
            )
        ]

        patterns.append(AlanakaramPattern(
            id=29,
            name="Advanced Ornamented Pattern",
            type=AlanakaramType.ADVANCED,
            complexity_level=ComplexityLevel.ADVANCED,
            description="Complex pattern with multiple ornamentations",
            phrases=advanced_phrases,
            raga_compatibility=["Shankarabharanam", "Kalyani"],
            tala_compatibility=["Adi"],
            tempo_recommendations=(70, 140),
            learning_objectives=[
                "Master advanced ornamentation techniques",
                "Develop sophisticated melodic expression",
                "Practice complex rhythmic variations"
            ],
            prerequisites=[8, 22],
            mastery_indicators={
                "ornamentation_mastery": 0.9,
                "rhythmic_precision": 0.85,
                "artistic_expression": 0.85
            },
            cultural_context="Professional-level technique development",
            traditional_usage=["Concert preparation", "Advanced training"]
        ))

        return patterns

    def get_pattern_by_id(self, pattern_id: int) -> Optional[AlanakaramPattern]:
        """Get Alankaram pattern by ID"""
        for pattern in self.alankaram_patterns:
            if pattern.id == pattern_id:
                return pattern
        return None

    def get_patterns_by_complexity(self, complexity: ComplexityLevel) -> List[AlanakaramPattern]:
        """Get patterns by complexity level"""
        return [p for p in self.alankaram_patterns if p.complexity_level == complexity]

    def get_patterns_by_raga(self, raga_name: str) -> List[AlanakaramPattern]:
        """Get patterns compatible with specific raga"""
        return [p for p in self.alankaram_patterns if raga_name in p.raga_compatibility]

    def validate_raga_compatibility(
        self,
        pattern: AlanakaramPattern,
        raga_name: str
    ) -> Tuple[bool, List[str]]:
        """Validate if pattern is compatible with raga and provide recommendations"""
        if raga_name not in self.raga_database:
            return False, ["Raga not found in database"]

        raga = self.raga_database[raga_name]
        issues = []

        for phrase in pattern.phrases:
            # Check for forbidden combinations
            for forbidden in raga.forbidden_combinations:
                for i in range(len(phrase.swaras) - len(forbidden) + 1):
                    if phrase.swaras[i:i+len(forbidden)] == forbidden:
                        issues.append(f"Forbidden combination {' '.join(forbidden)} found")

            # Check for swara compatibility
            for swara in phrase.swaras:
                if swara not in raga.arohanam and swara not in raga.avarohanam:
                    issues.append(f"Swara {swara} not in raga scale")

        is_compatible = len(issues) == 0
        return is_compatible, issues

    def generate_practice_curriculum(
        self,
        target_complexity: ComplexityLevel,
        focus_ragas: List[str] = None,
        session_duration: int = 45
    ) -> Dict[str, Any]:
        """Generate comprehensive practice curriculum"""
        focus_ragas = focus_ragas or ["Mayamalavagowla", "Shankarabharanam"]

        curriculum = {
            "target_complexity": target_complexity.name,
            "focus_ragas": focus_ragas,
            "session_duration": session_duration,
            "learning_path": []
        }

        # Get progressive pattern sequence
        all_patterns = sorted(self.alankaram_patterns, key=lambda x: x.complexity_level.value)
        target_patterns = [p for p in all_patterns
                          if p.complexity_level.value <= target_complexity.value]

        # Filter by raga compatibility
        if focus_ragas:
            compatible_patterns = []
            for pattern in target_patterns:
                if any(raga in pattern.raga_compatibility for raga in focus_ragas):
                    compatible_patterns.append(pattern)
            target_patterns = compatible_patterns

        # Create learning sessions
        patterns_per_session = max(1, len(target_patterns) // 8)  # Spread over 8 sessions

        for i in range(0, len(target_patterns), patterns_per_session):
            session_patterns = target_patterns[i:i + patterns_per_session]

            session = {
                "session_number": (i // patterns_per_session) + 1,
                "patterns": [p.id for p in session_patterns],
                "primary_focus": session_patterns[0].learning_objectives[0] if session_patterns else "",
                "estimated_duration": session_duration,
                "prerequisites_check": list(set().union(*[p.prerequisites for p in session_patterns])),
                "success_criteria": {
                    "pattern_completion": 0.8,
                    "accuracy_threshold": 0.85,
                    "expression_quality": 0.75
                }
            }
            curriculum["learning_path"].append(session)

        return curriculum

    def analyze_pattern_difficulty(self, pattern: AlanakaramPattern) -> Dict[str, float]:
        """Analyze various difficulty factors of a pattern"""
        analysis = {
            "melodic_complexity": 0.0,
            "rhythmic_complexity": 0.0,
            "ornamentation_density": 0.0,
            "phrase_length": 0.0,
            "interval_difficulty": 0.0,
            "overall_difficulty": 0.0
        }

        total_swaras = sum(len(phrase.swaras) for phrase in pattern.phrases)
        total_ornaments = sum(
            len([o for o in phrase.ornamentations if o is not None])
            for phrase in pattern.phrases
        )

        # Melodic complexity based on unique swaras and patterns
        unique_swaras = set()
        for phrase in pattern.phrases:
            unique_swaras.update(phrase.swaras)
        analysis["melodic_complexity"] = min(1.0, len(unique_swaras) / 7.0)

        # Rhythmic complexity from duration variations
        duration_variations = []
        for phrase in pattern.phrases:
            if len(phrase.duration_ratios) > 1:
                duration_variations.extend(phrase.duration_ratios)

        if duration_variations:
            duration_std = np.std(duration_variations)
            analysis["rhythmic_complexity"] = min(1.0, duration_std / 0.5)

        # Ornamentation density
        if total_swaras > 0:
            analysis["ornamentation_density"] = total_ornaments / total_swaras

        # Phrase length factor
        max_phrase_length = max(len(phrase.swaras) for phrase in pattern.phrases)
        analysis["phrase_length"] = min(1.0, max_phrase_length / 12.0)

        # Interval difficulty (larger jumps are harder)
        interval_scores = []
        swara_positions = {swara: i for i, swara in enumerate(self.base_swaras)}

        for phrase in pattern.phrases:
            for i in range(len(phrase.swaras) - 1):
                curr_pos = swara_positions.get(phrase.swaras[i], 0)
                next_pos = swara_positions.get(phrase.swaras[i+1], 0)
                interval = abs(next_pos - curr_pos)
                interval_scores.append(min(1.0, interval / 6.0))

        if interval_scores:
            analysis["interval_difficulty"] = np.mean(interval_scores)

        # Overall difficulty is weighted average
        weights = {
            "melodic_complexity": 0.2,
            "rhythmic_complexity": 0.15,
            "ornamentation_density": 0.25,
            "phrase_length": 0.15,
            "interval_difficulty": 0.25
        }

        analysis["overall_difficulty"] = sum(
            analysis[key] * weight for key, weight in weights.items()
        )

        return analysis

    def export_patterns_json(self) -> str:
        """Export all patterns to JSON format"""
        patterns_data = []

        for pattern in self.alankaram_patterns:
            pattern_dict = {
                "id": pattern.id,
                "name": pattern.name,
                "type": pattern.type.value,
                "complexity_level": pattern.complexity_level.value,
                "description": pattern.description,
                "phrases": [
                    {
                        "swaras": phrase.swaras,
                        "octave_shifts": phrase.octave_shifts,
                        "duration_ratios": phrase.duration_ratios,
                        "ornamentations": [o.value if o else None for o in phrase.ornamentations],
                        "emphasis_points": phrase.emphasis_points,
                        "phrase_type": phrase.phrase_type,
                        "difficulty_weight": phrase.difficulty_weight
                    }
                    for phrase in pattern.phrases
                ],
                "raga_compatibility": pattern.raga_compatibility,
                "tala_compatibility": pattern.tala_compatibility,
                "tempo_recommendations": pattern.tempo_recommendations,
                "learning_objectives": pattern.learning_objectives,
                "prerequisites": pattern.prerequisites,
                "mastery_indicators": pattern.mastery_indicators,
                "cultural_context": pattern.cultural_context,
                "traditional_usage": pattern.traditional_usage
            }
            patterns_data.append(pattern_dict)

        return json.dumps(patterns_data, indent=2, ensure_ascii=False)

# Initialize the generator
alankaram_generator = AlanakaramPatternGenerator()

# Export functions for API use
def get_alankaram_patterns() -> List[AlanakaramPattern]:
    """Get all Alankaram patterns"""
    return alankaram_generator.alankaram_patterns

def get_alankaram_pattern(pattern_id: int) -> Optional[AlanakaramPattern]:
    """Get specific Alankaram pattern"""
    return alankaram_generator.get_pattern_by_id(pattern_id)

def get_patterns_by_raga(raga_name: str) -> List[AlanakaramPattern]:
    """Get patterns for specific raga"""
    return alankaram_generator.get_patterns_by_raga(raga_name)

def validate_pattern_for_raga(pattern_id: int, raga_name: str) -> Tuple[bool, List[str]]:
    """Validate pattern compatibility with raga"""
    pattern = alankaram_generator.get_pattern_by_id(pattern_id)
    if not pattern:
        return False, ["Pattern not found"]
    return alankaram_generator.validate_raga_compatibility(pattern, raga_name)

def generate_alankaram_curriculum(
    complexity_level: int,
    focus_ragas: List[str] = None,
    duration: int = 45
) -> Dict[str, Any]:
    """Generate Alankaram practice curriculum"""
    complexity = ComplexityLevel(complexity_level)
    return alankaram_generator.generate_practice_curriculum(complexity, focus_ragas, duration)