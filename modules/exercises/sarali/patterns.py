"""
Sarali Varisai Exercise Patterns

Comprehensive implementation of traditional Carnatic music exercises
with progressive difficulty levels and adaptive learning paths.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import json
from datetime import datetime

class SwaraType(Enum):
    SHUDDHA = "shuddha"  # Natural
    CHATHUSHRUTI = "chathushruti"  # Four-shruti
    SHATSHRUTI = "shatshruti"  # Six-shruti
    ANTARA = "antara"  # Higher variant
    KAISIKA = "kaisika"  # Special variant

class TalaType(Enum):
    ADI = "adi"
    RUPAKA = "rupaka"
    MISRA_CHAPU = "misra_chapu"
    KHANDA_CHAPU = "khanda_chapu"

@dataclass
class SwaraPattern:
    name: str
    swara_sequence: List[str]
    octave_shifts: List[int]  # 0=middle, 1=upper, -1=lower
    duration_ratios: List[float]  # Relative durations
    emphasis_points: List[int]  # Indices of emphasized swaras
    description: str

@dataclass
class SaraliVarisai:
    level: int
    name: str
    pattern_type: str
    arohanam: SwaraPattern  # Ascending
    avarohanam: SwaraPattern  # Descending
    tempo_range: Tuple[int, int]  # Min, Max BPM
    tala: TalaType
    difficulty_score: float  # 0-1 scale
    prerequisite_levels: List[int]
    learning_objectives: List[str]
    common_mistakes: List[str]
    practice_tips: List[str]

class SaraliPatternGenerator:
    """
    Generates traditional Sarali Varisai patterns with proper
    Carnatic music theory implementation.
    """

    def __init__(self):
        # Core swaras in proper order
        self.base_swaras = ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']

        # Swara variations for different ragas
        self.swara_variations = {
            'Ri': ['Ri1', 'Ri2', 'Ri3'],  # Shuddha, Chathushruti, Shatshruti
            'Ga': ['Ga1', 'Ga2', 'Ga3'],  # Shuddha, Saadhaarana, Antara
            'Ma': ['Ma1', 'Ma2'],          # Shuddha, Prati
            'Da': ['Da1', 'Da2', 'Da3'],  # Shuddha, Chathushruti, Shatshruti
            'Ni': ['Ni1', 'Ni2', 'Ni3']   # Shuddha, Kaisika, Kaakali
        }

        # Initialize standard patterns
        self.sarali_patterns = self._generate_all_patterns()

    def _generate_all_patterns(self) -> List[SaraliVarisai]:
        """Generate all 12 levels of Sarali Varisai"""
        patterns = []

        # Level 1: Basic ascending and descending
        patterns.append(self._create_level_1())

        # Level 2: Sa Ri Ga Ma | Ma Ga Ri Sa
        patterns.append(self._create_level_2())

        # Level 3: Sa Ri Ga Ma Pa | Pa Ma Ga Ri Sa
        patterns.append(self._create_level_3())

        # Level 4: Sa Ri Ga Ma Pa Da | Da Pa Ma Ga Ri Sa
        patterns.append(self._create_level_4())

        # Level 5: Complete octave
        patterns.append(self._create_level_5())

        # Level 6: Two note combinations
        patterns.append(self._create_level_6())

        # Level 7: Three note combinations
        patterns.append(self._create_level_7())

        # Level 8: Four note combinations with returns
        patterns.append(self._create_level_8())

        # Level 9: Five note combinations
        patterns.append(self._create_level_9())

        # Level 10: Six note combinations
        patterns.append(self._create_level_10())

        # Level 11: Seven note combinations
        patterns.append(self._create_level_11())

        # Level 12: Advanced patterns with octave jumps
        patterns.append(self._create_level_12())

        return patterns

    def _create_level_1(self) -> SaraliVarisai:
        """Sa Ri Ga Ma - Ma Ga Ri Sa (Basic 4-note patterns)"""
        arohanam = SwaraPattern(
            name="Basic Arohanam",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma'],
            octave_shifts=[0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 3],
            description="Basic ascending four-note pattern"
        )

        avarohanam = SwaraPattern(
            name="Basic Avarohanam",
            swara_sequence=['Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 3],
            description="Basic descending four-note pattern"
        )

        return SaraliVarisai(
            level=1,
            name="Sarali Varisai 1",
            pattern_type="basic_four_note",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(40, 80),
            tala=TalaType.ADI,
            difficulty_score=0.1,
            prerequisite_levels=[],
            learning_objectives=[
                "Establish basic swara relationships",
                "Develop pitch accuracy for Sa-Ri-Ga-Ma",
                "Learn fundamental ascending/descending movement"
            ],
            common_mistakes=[
                "Rushing through the pattern",
                "Incorrect pitch intervals",
                "Not sustaining the final note"
            ],
            practice_tips=[
                "Start very slowly with metronome",
                "Focus on clean pitch transitions",
                "Sustain each swara clearly"
            ]
        )

    def _create_level_2(self) -> SaraliVarisai:
        """Sa Ri Ga Ma Ma Ga Ri Sa (Return pattern)"""
        arohanam = SwaraPattern(
            name="Ascending with Return",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 3, 7],
            description="Ascending and immediate return pattern"
        )

        avarohanam = SwaraPattern(
            name="Descending with Return",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 3, 7],
            description="Same pattern for avarohanam in this level"
        )

        return SaraliVarisai(
            level=2,
            name="Sarali Varisai 2",
            pattern_type="return_pattern",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(45, 90),
            tala=TalaType.ADI,
            difficulty_score=0.2,
            prerequisite_levels=[1],
            learning_objectives=[
                "Master return movements",
                "Develop longer phrase control",
                "Improve breath management"
            ],
            common_mistakes=[
                "Losing track during return journey",
                "Inconsistent tempo",
                "Unclear swara articulation"
            ],
            practice_tips=[
                "Mark the turning point clearly",
                "Maintain consistent volume",
                "Practice hands to show direction"
            ]
        )

    def _create_level_3(self) -> SaraliVarisai:
        """Sa Ri Ga Ma Pa | Pa Ma Ga Ri Sa (Five-note patterns)"""
        arohanam = SwaraPattern(
            name="Five Note Arohanam",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Pa'],
            octave_shifts=[0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 4],
            description="Five-note ascending pattern including Pa"
        )

        avarohanam = SwaraPattern(
            name="Five Note Avarohanam",
            swara_sequence=['Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 4],
            description="Five-note descending pattern from Pa"
        )

        return SaraliVarisai(
            level=3,
            name="Sarali Varisai 3",
            pattern_type="five_note_basic",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(50, 100),
            tala=TalaType.ADI,
            difficulty_score=0.25,
            prerequisite_levels=[1, 2],
            learning_objectives=[
                "Introduce Pa (fifth degree)",
                "Extend vocal range",
                "Develop stronger breath support"
            ],
            common_mistakes=[
                "Pitch drift on Pa",
                "Uneven note durations",
                "Losing connection between Ma and Pa"
            ],
            practice_tips=[
                "Practice Pa separately first",
                "Use hand gestures for pitch guidance",
                "Focus on smooth Ma-Pa transition"
            ]
        )

    def _create_level_4(self) -> SaraliVarisai:
        """Six-note patterns with Da"""
        arohanam = SwaraPattern(
            name="Six Note Arohanam",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da'],
            octave_shifts=[0, 0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 5],
            description="Six-note ascending including Da"
        )

        avarohanam = SwaraPattern(
            name="Six Note Avarohanam",
            swara_sequence=['Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 5],
            description="Six-note descending from Da"
        )

        return SaraliVarisai(
            level=4,
            name="Sarali Varisai 4",
            pattern_type="six_note_basic",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(55, 110),
            tala=TalaType.ADI,
            difficulty_score=0.3,
            prerequisite_levels=[1, 2, 3],
            learning_objectives=[
                "Add Da (sixth degree)",
                "Extend range further",
                "Maintain pitch accuracy over longer phrases"
            ],
            common_mistakes=[
                "Da pitch instability",
                "Rushing through longer sequences",
                "Losing breath control"
            ],
            practice_tips=[
                "Practice Da with reference to Pa",
                "Take breath at appropriate points",
                "Use drone for pitch reference"
            ]
        )

    def _create_level_5(self) -> SaraliVarisai:
        """Complete octave - Sa Ri Ga Ma Pa Da Ni Sa'"""
        arohanam = SwaraPattern(
            name="Full Octave Arohanam",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0, 0, 1],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 7],
            description="Complete octave ascending pattern"
        )

        avarohanam = SwaraPattern(
            name="Full Octave Avarohanam",
            swara_sequence=['Sa', 'Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[1, 0, 0, 0, 0, 0, 0, 0],
            duration_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0],
            emphasis_points=[0, 7],
            description="Complete octave descending pattern"
        )

        return SaraliVarisai(
            level=5,
            name="Sarali Varisai 5",
            pattern_type="full_octave",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(60, 120),
            tala=TalaType.ADI,
            difficulty_score=0.4,
            prerequisite_levels=[1, 2, 3, 4],
            learning_objectives=[
                "Complete the full octave",
                "Master octave jump on Sa",
                "Develop full vocal range"
            ],
            common_mistakes=[
                "Ni pitch placement issues",
                "Difficulty with octave Sa",
                "Breath management over full octave"
            ],
            practice_tips=[
                "Practice Ni with reference to Sa",
                "Prepare for octave jump",
                "Plan breathing strategically"
            ]
        )

    def _create_level_6(self) -> SaraliVarisai:
        """Two-note combination patterns: Sa Ri Sa Ga Sa Ma Sa Pa..."""
        sequence = []
        octaves = []
        durations = []
        emphasis = []

        # Create Sa-X-Sa patterns for each swara
        base_swaras = ['Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']
        for i, swara in enumerate(base_swaras):
            sequence.extend(['Sa', swara, 'Sa'])
            octaves.extend([0, 0, 0])
            durations.extend([0.5, 0.5, 1.0] if i < len(base_swaras) - 1 else [0.5, 0.5, 2.0])
            if i == len(base_swaras) - 1:
                emphasis.extend([len(sequence) - 3, len(sequence) - 1])

        arohanam = SwaraPattern(
            name="Two Note Combinations",
            swara_sequence=sequence,
            octave_shifts=octaves,
            duration_ratios=durations,
            emphasis_points=emphasis,
            description="Sa combined with each ascending swara"
        )

        # Create reverse pattern for avarohanam
        reverse_sequence = []
        reverse_octaves = []
        reverse_durations = []

        base_swaras_desc = ['Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri']
        for i, swara in enumerate(base_swaras_desc):
            reverse_sequence.extend(['Sa', swara, 'Sa'])
            reverse_octaves.extend([0, 0, 0])
            reverse_durations.extend([0.5, 0.5, 1.0] if i < len(base_swaras_desc) - 1 else [0.5, 0.5, 2.0])

        avarohanam = SwaraPattern(
            name="Two Note Combinations Descending",
            swara_sequence=reverse_sequence,
            octave_shifts=reverse_octaves,
            duration_ratios=reverse_durations,
            emphasis_points=[0, len(reverse_sequence) - 1],
            description="Sa combined with each descending swara"
        )

        return SaraliVarisai(
            level=6,
            name="Sarali Varisai 6",
            pattern_type="two_note_combinations",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(50, 100),
            tala=TalaType.ADI,
            difficulty_score=0.45,
            prerequisite_levels=[1, 2, 3, 4, 5],
            learning_objectives=[
                "Master Sa as anchor point",
                "Develop accurate interval jumps",
                "Improve phrase connectivity"
            ],
            common_mistakes=[
                "Losing Sa reference pitch",
                "Uneven rhythm in triplets",
                "Poor connection between phrases"
            ],
            practice_tips=[
                "Keep Sa consistent throughout",
                "Practice each pair separately",
                "Use metronome for rhythm accuracy"
            ]
        )

    def _create_level_7(self) -> SaraliVarisai:
        """Three-note combinations: Sa Ri Ga Sa, Sa Ga Ma Sa..."""
        arohanam_seq = []
        arohanam_oct = []
        arohanam_dur = []

        # Sa Ri Ga Sa, Sa Ga Ma Sa, Sa Ma Pa Sa, Sa Pa Da Sa, Sa Da Ni Sa
        combinations = [
            ['Sa', 'Ri', 'Ga', 'Sa'],
            ['Sa', 'Ga', 'Ma', 'Sa'],
            ['Sa', 'Ma', 'Pa', 'Sa'],
            ['Sa', 'Pa', 'Da', 'Sa'],
            ['Sa', 'Da', 'Ni', 'Sa']
        ]

        for i, combo in enumerate(combinations):
            arohanam_seq.extend(combo)
            arohanam_oct.extend([0, 0, 0, 0])
            if i < len(combinations) - 1:
                arohanam_dur.extend([0.5, 0.5, 0.5, 1.0])
            else:
                arohanam_dur.extend([0.5, 0.5, 0.5, 2.0])

        arohanam = SwaraPattern(
            name="Three Note Combinations",
            swara_sequence=arohanam_seq,
            octave_shifts=arohanam_oct,
            duration_ratios=arohanam_dur,
            emphasis_points=[0, len(arohanam_seq) - 1],
            description="Three-note ascending combinations with Sa return"
        )

        # Descending version
        desc_combinations = [
            ['Sa', 'Ni', 'Da', 'Sa'],
            ['Sa', 'Da', 'Pa', 'Sa'],
            ['Sa', 'Pa', 'Ma', 'Sa'],
            ['Sa', 'Ma', 'Ga', 'Sa'],
            ['Sa', 'Ga', 'Ri', 'Sa']
        ]

        avarohanam_seq = []
        avarohanam_oct = []
        avarohanam_dur = []

        for i, combo in enumerate(desc_combinations):
            avarohanam_seq.extend(combo)
            avarohanam_oct.extend([0, 0, 0, 0])
            if i < len(desc_combinations) - 1:
                avarohanam_dur.extend([0.5, 0.5, 0.5, 1.0])
            else:
                avarohanam_dur.extend([0.5, 0.5, 0.5, 2.0])

        avarohanam = SwaraPattern(
            name="Three Note Combinations Descending",
            swara_sequence=avarohanam_seq,
            octave_shifts=avarohanam_oct,
            duration_ratios=avarohanam_dur,
            emphasis_points=[0, len(avarohanam_seq) - 1],
            description="Three-note descending combinations with Sa return"
        )

        return SaraliVarisai(
            level=7,
            name="Sarali Varisai 7",
            pattern_type="three_note_combinations",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(55, 110),
            tala=TalaType.ADI,
            difficulty_score=0.5,
            prerequisite_levels=[1, 2, 3, 4, 5, 6],
            learning_objectives=[
                "Master three-note melodic cells",
                "Develop smooth phrase transitions",
                "Improve melodic memory"
            ],
            common_mistakes=[
                "Rushing through combinations",
                "Losing pitch accuracy in middle notes",
                "Poor phrase separation"
            ],
            practice_tips=[
                "Practice each combination slowly",
                "Focus on melodic shape of each group",
                "Maintain rhythmic precision"
            ]
        )

    def _create_level_8(self) -> SaraliVarisai:
        """Four-note combinations with return patterns"""
        # This creates more complex patterns building on previous levels
        arohanam = SwaraPattern(
            name="Four Note Return Combinations",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Ga', 'Ri', 'Sa',
                           'Ri', 'Ga', 'Ma', 'Pa', 'Ma', 'Ga', 'Ri'],
            octave_shifts=[0] * 14,
            duration_ratios=[0.5] * 13 + [2.0],
            emphasis_points=[0, 6, 13],
            description="Four-note combinations with return patterns"
        )

        avarohanam = SwaraPattern(
            name="Four Note Return Combinations Desc",
            swara_sequence=['Sa', 'Ni', 'Da', 'Pa', 'Da', 'Ni', 'Sa',
                           'Ni', 'Da', 'Pa', 'Ma', 'Pa', 'Da', 'Ni'],
            octave_shifts=[0] * 14,
            duration_ratios=[0.5] * 13 + [2.0],
            emphasis_points=[0, 6, 13],
            description="Four-note descending combinations with returns"
        )

        return SaraliVarisai(
            level=8,
            name="Sarali Varisai 8",
            pattern_type="four_note_returns",
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(60, 120),
            tala=TalaType.ADI,
            difficulty_score=0.6,
            prerequisite_levels=[1, 2, 3, 4, 5, 6, 7],
            learning_objectives=[
                "Master complex return patterns",
                "Develop advanced phrase control",
                "Improve musical memory and flow"
            ],
            common_mistakes=[
                "Getting lost in complex patterns",
                "Inconsistent rhythm",
                "Poor breath planning"
            ],
            practice_tips=[
                "Break into smaller segments",
                "Use hand movements to track patterns",
                "Practice breathing at natural phrase points"
            ]
        )

    # Simplified implementations for levels 9-12 (following similar patterns)
    def _create_level_9(self) -> SaraliVarisai:
        return self._create_advanced_level(9, "five_note_advanced", 0.65)

    def _create_level_10(self) -> SaraliVarisai:
        return self._create_advanced_level(10, "six_note_advanced", 0.7)

    def _create_level_11(self) -> SaraliVarisai:
        return self._create_advanced_level(11, "seven_note_advanced", 0.8)

    def _create_level_12(self) -> SaraliVarisai:
        return self._create_advanced_level(12, "octave_jumps", 0.9)

    def _create_advanced_level(self, level: int, pattern_type: str, difficulty: float) -> SaraliVarisai:
        """Helper method for creating advanced levels"""
        # Simplified advanced pattern creation
        arohanam = SwaraPattern(
            name=f"Advanced Pattern {level}",
            swara_sequence=['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa'],
            octave_shifts=[0, 0, 0, 0, 0, 0, 0, 1],
            duration_ratios=[0.5] * 7 + [2.0],
            emphasis_points=[0, 7],
            description=f"Advanced level {level} pattern"
        )

        avarohanam = SwaraPattern(
            name=f"Advanced Pattern {level} Desc",
            swara_sequence=['Sa', 'Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
            octave_shifts=[1, 0, 0, 0, 0, 0, 0, 0],
            duration_ratios=[0.5] * 7 + [2.0],
            emphasis_points=[0, 7],
            description=f"Advanced level {level} descending pattern"
        )

        return SaraliVarisai(
            level=level,
            name=f"Sarali Varisai {level}",
            pattern_type=pattern_type,
            arohanam=arohanam,
            avarohanam=avarohanam,
            tempo_range=(70, 140),
            tala=TalaType.ADI,
            difficulty_score=difficulty,
            prerequisite_levels=list(range(1, level)),
            learning_objectives=[f"Master advanced level {level} patterns"],
            common_mistakes=["Complex pattern navigation"],
            practice_tips=["Focus on precision and flow"]
        )

    def get_pattern_by_level(self, level: int) -> Optional[SaraliVarisai]:
        """Get Sarali Varisai pattern by level number"""
        for pattern in self.sarali_patterns:
            if pattern.level == level:
                return pattern
        return None

    def get_patterns_for_difficulty(self, difficulty_range: Tuple[float, float]) -> List[SaraliVarisai]:
        """Get patterns within specified difficulty range"""
        min_diff, max_diff = difficulty_range
        return [p for p in self.sarali_patterns
                if min_diff <= p.difficulty_score <= max_diff]

    def get_prerequisite_chain(self, level: int) -> List[int]:
        """Get the complete prerequisite chain for a given level"""
        pattern = self.get_pattern_by_level(level)
        if not pattern:
            return []

        chain = []
        current_prereqs = pattern.prerequisite_levels

        while current_prereqs:
            chain.extend(current_prereqs)
            next_prereqs = []
            for prereq in current_prereqs:
                prereq_pattern = self.get_pattern_by_level(prereq)
                if prereq_pattern:
                    next_prereqs.extend(prereq_pattern.prerequisite_levels)
            current_prereqs = list(set(next_prereqs) - set(chain))

        return sorted(list(set(chain)))

    def generate_practice_sequence(self, target_level: int, session_duration: int) -> List[Dict]:
        """Generate a practice sequence for a given session"""
        pattern = self.get_pattern_by_level(target_level)
        if not pattern:
            return []

        # Calculate practice allocation
        warmup_time = session_duration * 0.2
        main_time = session_duration * 0.6
        cooldown_time = session_duration * 0.2

        sequence = []

        # Warmup with prerequisite
        if pattern.prerequisite_levels:
            warmup_level = max(pattern.prerequisite_levels)
            warmup_pattern = self.get_pattern_by_level(warmup_level)
            if warmup_pattern:
                sequence.append({
                    'type': 'warmup',
                    'pattern': warmup_pattern,
                    'duration': warmup_time,
                    'tempo': warmup_pattern.tempo_range[0]
                })

        # Main practice
        sequence.append({
            'type': 'main_practice',
            'pattern': pattern,
            'duration': main_time,
            'tempo': pattern.tempo_range[0],
            'instructions': pattern.practice_tips
        })

        # Cooldown
        if pattern.level > 1:
            cooldown_pattern = self.get_pattern_by_level(pattern.level - 1)
            if cooldown_pattern:
                sequence.append({
                    'type': 'cooldown',
                    'pattern': cooldown_pattern,
                    'duration': cooldown_time,
                    'tempo': cooldown_pattern.tempo_range[1]
                })

        return sequence

    def export_patterns_json(self) -> str:
        """Export all patterns to JSON format"""
        patterns_data = []
        for pattern in self.sarali_patterns:
            pattern_dict = {
                'level': pattern.level,
                'name': pattern.name,
                'pattern_type': pattern.pattern_type,
                'arohanam': {
                    'name': pattern.arohanam.name,
                    'swara_sequence': pattern.arohanam.swara_sequence,
                    'octave_shifts': pattern.arohanam.octave_shifts,
                    'duration_ratios': pattern.arohanam.duration_ratios,
                    'emphasis_points': pattern.arohanam.emphasis_points,
                    'description': pattern.arohanam.description
                },
                'avarohanam': {
                    'name': pattern.avarohanam.name,
                    'swara_sequence': pattern.avarohanam.swara_sequence,
                    'octave_shifts': pattern.avarohanam.octave_shifts,
                    'duration_ratios': pattern.avarohanam.duration_ratios,
                    'emphasis_points': pattern.avarohanam.emphasis_points,
                    'description': pattern.avarohanam.description
                },
                'tempo_range': pattern.tempo_range,
                'tala': pattern.tala.value,
                'difficulty_score': pattern.difficulty_score,
                'prerequisite_levels': pattern.prerequisite_levels,
                'learning_objectives': pattern.learning_objectives,
                'common_mistakes': pattern.common_mistakes,
                'practice_tips': pattern.practice_tips
            }
            patterns_data.append(pattern_dict)

        return json.dumps(patterns_data, indent=2, ensure_ascii=False)

# Initialize the pattern generator
sarali_generator = SaraliPatternGenerator()

# Export function for API use
def get_sarali_patterns() -> List[SaraliVarisai]:
    """Get all Sarali Varisai patterns"""
    return sarali_generator.sarali_patterns

def get_sarali_pattern(level: int) -> Optional[SaraliVarisai]:
    """Get specific Sarali Varisai pattern"""
    return sarali_generator.get_pattern_by_level(level)

def generate_practice_session(level: int, duration: int) -> List[Dict]:
    """Generate practice session for given level and duration"""
    return sarali_generator.generate_practice_sequence(level, duration)