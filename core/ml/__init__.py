"""
Machine Learning module for the Carnatic Music Learning Platform.

Provides adaptive learning algorithms and AI-powered personalization.
"""

from .adaptive_engine import (
    AdaptiveLearningEngine,
    AdaptiveRecommendation,
    LearningStyle,
    SkillLevel,
    UserPerformanceMetrics,
)

__all__ = [
    "AdaptiveLearningEngine",
    "AdaptiveRecommendation",
    "UserPerformanceMetrics",
    "LearningStyle",
    "SkillLevel",
]
