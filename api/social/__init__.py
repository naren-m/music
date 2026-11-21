"""
Social API module for the Carnatic Music Learning Platform.

Provides social features, groups, collaborative learning,
user discovery, activity feeds, leaderboards, and practice challenges.
"""

from .routes import (
    ActivityType,
    ChallengeStatus,
    PracticeChallenge,
    social_bp,
)

__all__ = [
    "social_bp",
    "ActivityType",
    "ChallengeStatus",
    "PracticeChallenge",
]
