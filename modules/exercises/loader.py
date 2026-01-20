"""
Exercise File Loader

Loads exercise patterns from text files and configuration from JSON files.
Converts text-based patterns to the existing dataclass structures used by the application.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

# Base path for exercise data files
DATA_DIR = Path(__file__).parent / "data"


@dataclass
class ParsedExercise:
    """Represents a parsed exercise from a text file."""
    level: int
    arohanam: List[str]  # List of swaras for ascending
    avarohanam: List[str]  # List of swaras for descending


@dataclass
class ExerciseConfig:
    """Configuration loaded from config.json."""
    exercise_type: str
    name: str
    description: str
    raga: str
    talam: str
    angah: str
    default_tempo_range: Tuple[int, int]
    swara_mapping: Dict[str, str]
    levels: List[Dict[str, Any]]
    gamaka_notation: Optional[Dict[str, str]] = None


def parse_swara_sequence(line: str) -> List[str]:
    """
    Parse a space-separated swara sequence into a list.

    Handles:
    - Simple swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni
    - Octave notation: Sa2 (upper octave)
    - Swara variants: Ri1, Ri2, Ga3, etc.
    - Future gamaka notation: Sa~, Ri^, etc. (strips for now, preserves swara)

    Args:
        line: Space-separated swara sequence string

    Returns:
        List of swara names
    """
    if not line or not line.strip():
        return []

    # Split by whitespace
    tokens = line.strip().split()

    swaras = []
    for token in tokens:
        # Strip any gamaka notation (for future extensibility)
        # Currently just removes ~ ^ _ suffixes but preserves the swara
        swara = re.sub(r'[~^_]+$', '', token)
        if swara:
            swaras.append(swara)

    return swaras


def parse_exercise_file(file_path: Path) -> List[ParsedExercise]:
    """
    Parse a text file containing exercises.

    Format:
    - Each exercise has arohanam (line 1) and avarohanam (line 2)
    - Exercises separated by '---' or blank lines
    - Lines starting with '#' are comments

    Args:
        file_path: Path to the exercise text file

    Returns:
        List of ParsedExercise objects
    """
    exercises = []

    if not file_path.exists():
        return exercises

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by exercise separator
    exercise_blocks = re.split(r'\n---\n|\n\n+', content)

    level = 1
    for block in exercise_blocks:
        block = block.strip()
        if not block:
            continue

        # Filter out comment lines
        lines = [
            line.strip()
            for line in block.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        if len(lines) >= 2:
            # First line is arohanam, second is avarohanam
            arohanam = parse_swara_sequence(lines[0])
            avarohanam = parse_swara_sequence(lines[1])

            if arohanam and avarohanam:
                exercises.append(ParsedExercise(
                    level=level,
                    arohanam=arohanam,
                    avarohanam=avarohanam
                ))
                level += 1
        elif len(lines) == 1:
            # Single line - use same for both arohanam and avarohanam
            sequence = parse_swara_sequence(lines[0])
            if sequence:
                exercises.append(ParsedExercise(
                    level=level,
                    arohanam=sequence,
                    avarohanam=sequence
                ))
                level += 1

    return exercises


def load_config(config_path: Path) -> Optional[ExerciseConfig]:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to config.json

    Returns:
        ExerciseConfig object or None if file doesn't exist
    """
    if not config_path.exists():
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return ExerciseConfig(
        exercise_type=data.get('exercise_type', 'unknown'),
        name=data.get('name', 'Unknown Exercise'),
        description=data.get('description', ''),
        raga=data.get('raga', 'mayamalavagowla'),
        talam=data.get('talam', 'adi'),
        angah=data.get('angah', ''),
        default_tempo_range=tuple(data.get('default_tempo_range', [60, 120])),
        swara_mapping=data.get('swara_mapping', {}),
        levels=data.get('levels', []),
        gamaka_notation=data.get('gamaka_notation')
    )


def get_level_config(config: ExerciseConfig, level: int) -> Dict[str, Any]:
    """
    Get configuration for a specific level.

    Args:
        config: ExerciseConfig object
        level: Level number (1-based)

    Returns:
        Level configuration dict with defaults applied
    """
    # Find level config by index (level is 1-based)
    level_idx = level - 1

    if level_idx < len(config.levels):
        level_config = config.levels[level_idx].copy()
    else:
        # Generate default level config
        level_config = {
            'name': f'{config.name} {level}',
            'difficulty': min(0.1 + (level - 1) * 0.1, 1.0),
        }

    # Apply defaults from config
    if 'tempo_range' not in level_config:
        level_config['tempo_range'] = list(config.default_tempo_range)

    if 'learning_objectives' not in level_config:
        level_config['learning_objectives'] = [
            f'Master {config.name} level {level} patterns',
            'Develop pitch accuracy',
            'Build musical memory'
        ]

    if 'practice_tips' not in level_config:
        level_config['practice_tips'] = [
            'Start slowly with drone reference',
            'Focus on clean transitions',
            'Gradually increase tempo'
        ]

    return level_config


def normalize_swara(swara: str, swara_mapping: Dict[str, str]) -> str:
    """
    Normalize a swara name using the mapping from config.

    This handles conversion of simple names (Ri, Ga) to explicit variants (Ri1, Ga3)
    based on the raga configuration.

    Args:
        swara: Input swara name
        swara_mapping: Mapping from simple to explicit swara names

    Returns:
        Normalized swara name
    """
    # Check if swara is in mapping
    if swara in swara_mapping:
        return swara_mapping[swara]

    # Return as-is (already explicit or unknown)
    return swara


def extract_octave_shift(swara: str) -> Tuple[str, int]:
    """
    Extract octave shift from swara notation.

    Args:
        swara: Swara with possible octave notation (e.g., 'Sa2', 'Sa')

    Returns:
        Tuple of (base_swara, octave_shift) where shift is 0 for middle, 1 for upper
    """
    # Check for upper octave notation (Sa2, Ri2, etc. where 2 indicates upper octave)
    match = re.match(r'^([A-Za-z]+)2$', swara)
    if match:
        return (match.group(1), 1)

    # Check for explicit variant with octave (e.g., Ri12 = Ri1 upper octave)
    match = re.match(r'^([A-Za-z]+\d)2$', swara)
    if match:
        return (match.group(1), 1)

    # Default: middle octave
    return (swara, 0)


def load_exercises_from_folder(folder_name: str, file_name: str = None) -> Tuple[List[ParsedExercise], Optional[ExerciseConfig]]:
    """
    Load all exercises from a folder.

    Args:
        folder_name: Name of the exercise folder (e.g., 'SaraliSwaras')
        file_name: Optional specific file to load (e.g., 'mayamalavagowla.txt')
                   If None, loads all .txt files in the folder

    Returns:
        Tuple of (list of exercises, config)
    """
    folder_path = DATA_DIR / folder_name

    if not folder_path.exists():
        return ([], None)

    # Load config
    config = load_config(folder_path / 'config.json')

    # Load exercises
    all_exercises = []

    if file_name:
        # Load specific file
        file_path = folder_path / file_name
        if file_path.exists():
            all_exercises = parse_exercise_file(file_path)
    else:
        # Load all .txt files
        txt_files = sorted(folder_path.glob('*.txt'))
        level_offset = 0
        for txt_file in txt_files:
            exercises = parse_exercise_file(txt_file)
            # Adjust level numbers for combined loading
            for ex in exercises:
                ex.level += level_offset
            all_exercises.extend(exercises)
            level_offset = len(all_exercises)

    return (all_exercises, config)


def get_available_exercise_folders() -> List[str]:
    """
    Get list of available exercise folders.

    Returns:
        List of folder names that contain exercise data
    """
    if not DATA_DIR.exists():
        return []

    folders = []
    for item in DATA_DIR.iterdir():
        if item.is_dir() and (item / 'config.json').exists():
            folders.append(item.name)

    return sorted(folders)


def get_available_ragas(folder_name: str) -> List[str]:
    """
    Get list of available raga files in a folder.

    Args:
        folder_name: Name of the exercise folder

    Returns:
        List of raga names (without .txt extension)
    """
    folder_path = DATA_DIR / folder_name

    if not folder_path.exists():
        return []

    ragas = []
    for txt_file in folder_path.glob('*.txt'):
        ragas.append(txt_file.stem)

    return sorted(ragas)
