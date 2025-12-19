"""
Social API module for the Carnatic Music Learning Platform.

Provides social features, groups, collaborative learning,
user discovery, activity feeds, leaderboards, and practice challenges.
"""

from .routes import (
    social_bp,
    ActivityType,
    ChallengeStatus,
    PracticeChallenge,
)

__all__ = [
    'social_bp',
    'ActivityType',
    'ChallengeStatus',
    'PracticeChallenge',
]
