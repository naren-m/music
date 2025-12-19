"""
Core data models for the Carnatic Music Learning Platform.

This module provides:
- Shruti: The 22-shruti microtonal system
- User: User profiles and authentication models
"""

from .shruti import (
    Shruti,
    ShrutiSystem,
    RagaAnalyzer,
    SHRUTI_SYSTEM,
    MELAKARTA_RAGAS,
    JANYA_RAGAS,
    calculate_shruti_frequency,
    find_closest_shruti,
    analyze_pitch_deviation,
)
from .user import (
    UserProfile,
    SubscriptionTier,
    ModuleProgress,
    Achievement,
    PracticeSession,
    LearningGoal,
    SkillLevel,
    UserPreferences,
    UserModel,
)

__all__ = [
    # Shruti module exports
    'Shruti',
    'ShrutiSystem',
    'RagaAnalyzer',
    'SHRUTI_SYSTEM',
    'MELAKARTA_RAGAS',
    'JANYA_RAGAS',
    'calculate_shruti_frequency',
    'find_closest_shruti',
    'analyze_pitch_deviation',
    # User module exports
    'UserProfile',
    'SubscriptionTier',
    'ModuleProgress',
    'Achievement',
    'PracticeSession',
    'LearningGoal',
    'SkillLevel',
    'UserPreferences',
    'UserModel',
]
