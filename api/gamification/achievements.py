"""
Gamification and Achievement System

Comprehensive system for user engagement through achievements, badges,
streaks, leaderboards, and progressive challenges in Carnatic music learning.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import math
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db_session
from ..models import User, Progress, Achievement, UserAchievement

class AchievementType(Enum):
    PRACTICE = "practice"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    MILESTONE = "milestone"
    STREAK = "streak"
    EXPLORATION = "exploration"
    MASTERY = "mastery"
    SOCIAL = "social"

class BadgeRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class ChallengeType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    SPECIAL = "special"

@dataclass
class Badge:
    id: str
    name: str
    description: str
    icon: str
    rarity: BadgeRarity
    points: int
    requirements: Dict[str, Any]
    category: AchievementType
    hidden: bool = False
    seasonal: bool = False

@dataclass
class UserStats:
    user_id: int
    total_practice_time: int  # minutes
    sessions_completed: int
    current_streak: int
    longest_streak: int
    average_accuracy: float
    swaras_mastered: int
    ragas_explored: int
    total_points: int
    level: int
    next_level_progress: float
    badges_earned: int
    achievements_unlocked: int

@dataclass
class Challenge:
    id: str
    name: str
    description: str
    type: ChallengeType
    start_date: datetime
    end_date: datetime
    requirements: Dict[str, Any]
    rewards: Dict[str, int]  # points, badges, etc.
    progress_tracking: Dict[str, str]
    difficulty: float
    participants: int = 0

@dataclass
class LeaderboardEntry:
    user_id: int
    username: str
    avatar: Optional[str]
    score: float
    rank: int
    level: int
    change_from_previous: int  # +/- rank change

class GamificationEngine:
    """
    Core gamification engine that manages achievements, badges,
    challenges, and user progression.
    """

    def __init__(self):
        self.achievement_definitions = self._load_achievement_definitions()
        self.badge_definitions = self._load_badge_definitions()
        self.level_thresholds = self._calculate_level_thresholds()
        self.active_challenges = []

    def _load_achievement_definitions(self) -> List[Badge]:
        """Load all achievement and badge definitions"""
        return [
            # Practice-based achievements
            Badge(
                id="first_practice",
                name="First Steps",
                description="Complete your first practice session",
                icon="🎵",
                rarity=BadgeRarity.COMMON,
                points=50,
                requirements={"sessions_completed": 1},
                category=AchievementType.PRACTICE
            ),
            Badge(
                id="daily_warrior",
                name="Daily Warrior",
                description="Practice for 7 consecutive days",
                icon="🔥",
                rarity=BadgeRarity.UNCOMMON,
                points=250,
                requirements={"streak_days": 7},
                category=AchievementType.STREAK
            ),
            Badge(
                id="week_champion",
                name="Weekly Champion",
                description="Practice for 30 consecutive days",
                icon="👑",
                rarity=BadgeRarity.RARE,
                points=750,
                requirements={"streak_days": 30},
                category=AchievementType.STREAK
            ),
            Badge(
                id="marathon_monk",
                name="Marathon Monk",
                description="Practice for 100 consecutive days",
                icon="🏆",
                rarity=BadgeRarity.EPIC,
                points=2000,
                requirements={"streak_days": 100},
                category=AchievementType.STREAK
            ),

            # Accuracy achievements
            Badge(
                id="perfect_pitch",
                name="Perfect Pitch",
                description="Achieve 95%+ accuracy in a session",
                icon="🎯",
                rarity=BadgeRarity.UNCOMMON,
                points=300,
                requirements={"session_accuracy": 0.95},
                category=AchievementType.ACCURACY
            ),
            Badge(
                id="precision_master",
                name="Precision Master",
                description="Maintain 90%+ accuracy for 10 sessions",
                icon="🎪",
                rarity=BadgeRarity.RARE,
                points=500,
                requirements={"consecutive_high_accuracy": 10, "min_accuracy": 0.90},
                category=AchievementType.CONSISTENCY
            ),

            # Swara mastery achievements
            Badge(
                id="sa_foundation",
                name="Sa Foundation",
                description="Master the fundamental Sa with consistent accuracy",
                icon="🏗️",
                rarity=BadgeRarity.COMMON,
                points=100,
                requirements={"swara_mastery": ["Sa"], "min_accuracy": 0.85},
                category=AchievementType.MASTERY
            ),
            Badge(
                id="saptak_explorer",
                name="Saptak Explorer",
                description="Practice all seven swaras with good accuracy",
                icon="🌈",
                rarity=BadgeRarity.UNCOMMON,
                points=400,
                requirements={"swaras_practiced": 7, "min_accuracy": 0.80},
                category=AchievementType.EXPLORATION
            ),
            Badge(
                id="swara_sage",
                name="Swara Sage",
                description="Master all seven swaras with high precision",
                icon="🧙‍♂️",
                rarity=BadgeRarity.EPIC,
                points=1500,
                requirements={"swaras_mastered": 7, "min_accuracy": 0.90},
                category=AchievementType.MASTERY
            ),

            # Time-based achievements
            Badge(
                id="dedicated_learner",
                name="Dedicated Learner",
                description="Practice for 10 total hours",
                icon="📚",
                rarity=BadgeRarity.UNCOMMON,
                points=350,
                requirements={"total_practice_minutes": 600},
                category=AchievementType.PRACTICE
            ),
            Badge(
                id="time_traveler",
                name="Time Traveler",
                description="Practice for 100 total hours",
                icon="⏰",
                rarity=BadgeRarity.RARE,
                points=1000,
                requirements={"total_practice_minutes": 6000},
                category=AchievementType.PRACTICE
            ),
            Badge(
                id="lifetime_devotee",
                name="Lifetime Devotee",
                description="Practice for 1000 total hours",
                icon="🕉️",
                rarity=BadgeRarity.LEGENDARY,
                points=10000,
                requirements={"total_practice_minutes": 60000},
                category=AchievementType.PRACTICE
            ),

            # Raga exploration achievements
            Badge(
                id="raga_explorer",
                name="Raga Explorer",
                description="Practice 5 different ragas",
                icon="🗺️",
                rarity=BadgeRarity.UNCOMMON,
                points=400,
                requirements={"ragas_practiced": 5},
                category=AchievementType.EXPLORATION
            ),
            Badge(
                id="raga_connoisseur",
                name="Raga Connoisseur",
                description="Practice 25 different ragas",
                icon="🎨",
                rarity=BadgeRarity.RARE,
                points=1200,
                requirements={"ragas_practiced": 25},
                category=AchievementType.EXPLORATION
            ),

            # Sarali Varisai achievements
            Badge(
                id="sarali_beginner",
                name="Sarali Beginner",
                description="Complete first 3 levels of Sarali Varisai",
                icon="📋",
                rarity=BadgeRarity.COMMON,
                points=200,
                requirements={"sarali_levels_completed": 3},
                category=AchievementType.MILESTONE
            ),
            Badge(
                id="sarali_intermediate",
                name="Sarali Intermediate",
                description="Complete first 6 levels of Sarali Varisai",
                icon="📈",
                rarity=BadgeRarity.UNCOMMON,
                points=500,
                requirements={"sarali_levels_completed": 6},
                category=AchievementType.MILESTONE
            ),
            Badge(
                id="sarali_advanced",
                name="Sarali Advanced",
                description="Complete first 9 levels of Sarali Varisai",
                icon="🎓",
                rarity=BadgeRarity.RARE,
                points=1000,
                requirements={"sarali_levels_completed": 9},
                category=AchievementType.MILESTONE
            ),
            Badge(
                id="sarali_master",
                name="Sarali Master",
                description="Complete all 12 levels of Sarali Varisai",
                icon="👨‍🎓",
                rarity=BadgeRarity.EPIC,
                points=2500,
                requirements={"sarali_levels_completed": 12},
                category=AchievementType.MASTERY
            ),

            # Social achievements
            Badge(
                id="helpful_friend",
                name="Helpful Friend",
                description="Help 10 other students with feedback",
                icon="🤝",
                rarity=BadgeRarity.UNCOMMON,
                points=300,
                requirements={"help_given": 10},
                category=AchievementType.SOCIAL,
                hidden=True
            ),
            Badge(
                id="community_leader",
                name="Community Leader",
                description="Be featured in top 10 of monthly leaderboard",
                icon="🌟",
                rarity=BadgeRarity.RARE,
                points=800,
                requirements={"monthly_leaderboard_rank": 10},
                category=AchievementType.SOCIAL
            ),

            # Special seasonal achievements
            Badge(
                id="diwali_celebration",
                name="Diwali Celebration",
                description="Practice traditional ragas during Diwali week",
                icon="🪔",
                rarity=BadgeRarity.RARE,
                points=600,
                requirements={"seasonal_practice": "diwali", "sessions": 5},
                category=AchievementType.PRACTICE,
                seasonal=True
            ),
            Badge(
                id="new_year_resolution",
                name="New Year Resolution",
                description="Start the year with 10 days of consistent practice",
                icon="🎊",
                rarity=BadgeRarity.UNCOMMON,
                points=400,
                requirements={"january_streak": 10},
                category=AchievementType.STREAK,
                seasonal=True
            )
        ]

    def _load_badge_definitions(self) -> Dict[str, Badge]:
        """Convert achievement list to dictionary for quick lookup"""
        return {badge.id: badge for badge in self.achievement_definitions}

    def _calculate_level_thresholds(self) -> List[int]:
        """Calculate point thresholds for each level"""
        thresholds = [0]  # Level 0
        base_points = 100

        for level in range(1, 101):  # Support up to level 100
            # Exponential growth with some adjustment
            points_needed = int(base_points * (1.2 ** (level - 1)))
            thresholds.append(thresholds[-1] + points_needed)

        return thresholds

    async def check_achievements(self, user_id: int, session_data: Dict[str, Any]) -> List[Badge]:
        """Check and award new achievements based on session data"""
        newly_earned = []

        try:
            # Get current user stats
            user_stats = await self.get_user_stats(user_id)

            # Get user's existing achievements
            existing_achievements = await self.get_user_achievements(user_id)
            existing_ids = {ach['badge_id'] for ach in existing_achievements}

            # Check each achievement definition
            for badge in self.achievement_definitions:
                if badge.id in existing_ids:
                    continue  # Already earned

                if self._check_badge_requirements(badge, user_stats, session_data):
                    await self._award_badge(user_id, badge)
                    newly_earned.append(badge)

            return newly_earned

        except Exception as e:
            print(f"Error checking achievements for user {user_id}: {e}")
            return []

    def _check_badge_requirements(self, badge: Badge, user_stats: UserStats, session_data: Dict) -> bool:
        """Check if badge requirements are met"""
        requirements = badge.requirements

        # Check session-specific requirements
        if "session_accuracy" in requirements:
            session_accuracy = session_data.get('accuracy', 0)
            if session_accuracy < requirements["session_accuracy"]:
                return False

        # Check cumulative stats requirements
        if "sessions_completed" in requirements:
            if user_stats.sessions_completed < requirements["sessions_completed"]:
                return False

        if "streak_days" in requirements:
            if user_stats.current_streak < requirements["streak_days"]:
                return False

        if "total_practice_minutes" in requirements:
            if user_stats.total_practice_time < requirements["total_practice_minutes"]:
                return False

        if "swaras_mastered" in requirements:
            if user_stats.swaras_mastered < requirements["swaras_mastered"]:
                return False

        if "ragas_practiced" in requirements:
            if user_stats.ragas_explored < requirements["ragas_practiced"]:
                return False

        # Check Sarali Varisai progress
        if "sarali_levels_completed" in requirements:
            sarali_completed = session_data.get('sarali_completed', 0)
            if sarali_completed < requirements["sarali_levels_completed"]:
                return False

        # Check specific swara mastery
        if "swara_mastery" in requirements:
            required_swaras = set(requirements["swara_mastery"])
            mastered_swaras = set(session_data.get('mastered_swaras', []))
            if not required_swaras.issubset(mastered_swaras):
                return False

        return True

    async def _award_badge(self, user_id: int, badge: Badge):
        """Award a badge to the user"""
        try:
            with get_db_session() as db:
                # Create user achievement record
                user_achievement = UserAchievement(
                    user_id=user_id,
                    badge_id=badge.id,
                    badge_name=badge.name,
                    points_awarded=badge.points,
                    earned_at=datetime.now(),
                    badge_data=asdict(badge)
                )
                db.add(user_achievement)

                # Update user's total points
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.total_points = (user.total_points or 0) + badge.points
                    user.level = self._calculate_level(user.total_points)

                db.commit()
                print(f"Awarded badge '{badge.name}' to user {user_id}")

        except Exception as e:
            print(f"Error awarding badge {badge.id} to user {user_id}: {e}")

    def _calculate_level(self, total_points: int) -> int:
        """Calculate user level based on total points"""
        for level, threshold in enumerate(self.level_thresholds):
            if total_points < threshold:
                return level - 1
        return len(self.level_thresholds) - 1  # Max level

    async def get_user_stats(self, user_id: int) -> UserStats:
        """Get comprehensive user statistics"""
        try:
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return self._create_empty_user_stats(user_id)

                # Get practice statistics
                progress_records = db.query(Progress).filter(
                    Progress.user_id == user_id
                ).all()

                total_practice_time = sum(
                    (p.session_duration or 0) for p in progress_records
                )
                sessions_completed = len(progress_records)

                # Calculate streak
                current_streak, longest_streak = self._calculate_streaks(progress_records)

                # Calculate average accuracy
                accuracies = [p.accuracy_score for p in progress_records if p.accuracy_score]
                average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

                # Count mastered swaras and ragas
                swaras_mastered = self._count_mastered_swaras(progress_records)
                ragas_explored = self._count_explored_ragas(progress_records)

                # Get achievements count
                achievements = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id
                ).count()

                total_points = user.total_points or 0
                level = self._calculate_level(total_points)
                next_level_points = self.level_thresholds[level + 1] if level + 1 < len(self.level_thresholds) else total_points
                current_level_points = self.level_thresholds[level]
                next_level_progress = (total_points - current_level_points) / (next_level_points - current_level_points)

                return UserStats(
                    user_id=user_id,
                    total_practice_time=total_practice_time,
                    sessions_completed=sessions_completed,
                    current_streak=current_streak,
                    longest_streak=longest_streak,
                    average_accuracy=average_accuracy,
                    swaras_mastered=swaras_mastered,
                    ragas_explored=ragas_explored,
                    total_points=total_points,
                    level=level,
                    next_level_progress=next_level_progress,
                    badges_earned=achievements,
                    achievements_unlocked=achievements
                )

        except Exception as e:
            print(f"Error getting user stats for {user_id}: {e}")
            return self._create_empty_user_stats(user_id)

    def _create_empty_user_stats(self, user_id: int) -> UserStats:
        """Create empty user stats for new users"""
        return UserStats(
            user_id=user_id,
            total_practice_time=0,
            sessions_completed=0,
            current_streak=0,
            longest_streak=0,
            average_accuracy=0.0,
            swaras_mastered=0,
            ragas_explored=0,
            total_points=0,
            level=0,
            next_level_progress=0.0,
            badges_earned=0,
            achievements_unlocked=0
        )

    def _calculate_streaks(self, progress_records: List[Progress]) -> Tuple[int, int]:
        """Calculate current and longest practice streaks"""
        if not progress_records:
            return 0, 0

        # Group sessions by date
        session_dates = set()
        for record in progress_records:
            session_dates.add(record.created_at.date())

        sorted_dates = sorted(session_dates)

        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        check_date = today

        while check_date in sorted_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate longest streak
        longest_streak = 0
        temp_streak = 1

        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i-1] == timedelta(days=1):
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)

        return current_streak, longest_streak

    def _count_mastered_swaras(self, progress_records: List[Progress]) -> int:
        """Count number of swaras mastered (>85% accuracy over multiple sessions)"""
        swara_accuracy = {}

        for record in progress_records:
            if record.exercise_data and 'target_swara' in record.exercise_data:
                swara = record.exercise_data['target_swara']
                if swara not in swara_accuracy:
                    swara_accuracy[swara] = []
                swara_accuracy[swara].append(record.accuracy_score)

        mastered_count = 0
        for swara, accuracies in swara_accuracy.items():
            if len(accuracies) >= 3 and sum(accuracies) / len(accuracies) >= 0.85:
                mastered_count += 1

        return mastered_count

    def _count_explored_ragas(self, progress_records: List[Progress]) -> int:
        """Count number of different ragas practiced"""
        ragas = set()
        for record in progress_records:
            if record.exercise_data and 'raga' in record.exercise_data:
                ragas.add(record.exercise_data['raga'])
        return len(ragas)

    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get all achievements earned by user"""
        try:
            with get_db_session() as db:
                achievements = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id
                ).all()

                return [
                    {
                        'badge_id': ach.badge_id,
                        'badge_name': ach.badge_name,
                        'points_awarded': ach.points_awarded,
                        'earned_at': ach.earned_at.isoformat(),
                        'badge_data': ach.badge_data
                    }
                    for ach in achievements
                ]

        except Exception as e:
            print(f"Error getting user achievements for {user_id}: {e}")
            return []

    async def get_leaderboard(self, period: str = "monthly", limit: int = 100) -> List[LeaderboardEntry]:
        """Get leaderboard for specified period"""
        try:
            with get_db_session() as db:
                # Calculate date range based on period
                now = datetime.now()
                if period == "daily":
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif period == "weekly":
                    days_since_monday = now.weekday()
                    start_date = now - timedelta(days=days_since_monday)
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                elif period == "monthly":
                    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:  # all time
                    start_date = datetime.min

                # Get users with their points in the period
                if period == "all_time":
                    leaderboard_data = db.query(
                        User.id,
                        User.username,
                        User.avatar,
                        func.coalesce(User.total_points, 0).label('score')
                    ).filter(
                        User.total_points.isnot(None)
                    ).order_by(
                        User.total_points.desc()
                    ).limit(limit).all()
                else:
                    # For period-based leaderboards, sum points from achievements in that period
                    leaderboard_data = db.query(
                        User.id,
                        User.username,
                        User.avatar,
                        func.coalesce(func.sum(UserAchievement.points_awarded), 0).label('score')
                    ).join(
                        UserAchievement, User.id == UserAchievement.user_id
                    ).filter(
                        UserAchievement.earned_at >= start_date
                    ).group_by(
                        User.id, User.username, User.avatar
                    ).order_by(
                        func.sum(UserAchievement.points_awarded).desc()
                    ).limit(limit).all()

                # Format leaderboard entries
                entries = []
                for rank, (user_id, username, avatar, score) in enumerate(leaderboard_data, 1):
                    # Calculate user level
                    total_points = score if period == "all_time" else 0  # For period boards, show period points
                    level = self._calculate_level(total_points) if period == "all_time" else 1

                    entries.append(LeaderboardEntry(
                        user_id=user_id,
                        username=username or f"User{user_id}",
                        avatar=avatar,
                        score=float(score),
                        rank=rank,
                        level=level,
                        change_from_previous=0  # TODO: Track rank changes
                    ))

                return entries

        except Exception as e:
            print(f"Error getting leaderboard for {period}: {e}")
            return []

    async def create_challenge(self, challenge_data: Dict) -> Challenge:
        """Create a new challenge"""
        challenge = Challenge(
            id=challenge_data['id'],
            name=challenge_data['name'],
            description=challenge_data['description'],
            type=ChallengeType(challenge_data['type']),
            start_date=datetime.fromisoformat(challenge_data['start_date']),
            end_date=datetime.fromisoformat(challenge_data['end_date']),
            requirements=challenge_data['requirements'],
            rewards=challenge_data['rewards'],
            progress_tracking=challenge_data.get('progress_tracking', {}),
            difficulty=challenge_data.get('difficulty', 0.5)
        )

        self.active_challenges.append(challenge)
        return challenge

    async def get_active_challenges(self) -> List[Challenge]:
        """Get all currently active challenges"""
        now = datetime.now()
        return [c for c in self.active_challenges
                if c.start_date <= now <= c.end_date]

    def get_badge_by_id(self, badge_id: str) -> Optional[Badge]:
        """Get badge definition by ID"""
        return self.badge_definitions.get(badge_id)

    async def simulate_progress_session(self, user_id: int) -> Dict:
        """Simulate a practice session and return achievements/progress"""
        # This is for testing/demo purposes
        import random

        session_data = {
            'accuracy': random.uniform(0.7, 0.98),
            'duration_minutes': random.randint(10, 45),
            'target_swara': random.choice(['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni']),
            'mastered_swaras': ['Sa', 'Ri'],
            'sarali_completed': random.randint(0, 5)
        }

        # Check for new achievements
        new_badges = await self.check_achievements(user_id, session_data)

        # Get updated stats
        updated_stats = await self.get_user_stats(user_id)

        return {
            'session_data': session_data,
            'new_badges': [asdict(badge) for badge in new_badges],
            'updated_stats': asdict(updated_stats),
            'level_up': len(new_badges) > 0  # Simplified level up check
        }

# Initialize the gamification engine
gamification_engine = GamificationEngine()

# Export functions for API use
async def check_user_achievements(user_id: int, session_data: Dict) -> List[Badge]:
    """Check and award new achievements for user"""
    return await gamification_engine.check_achievements(user_id, session_data)

async def get_user_gamification_data(user_id: int) -> Dict:
    """Get comprehensive gamification data for user"""
    stats = await gamification_engine.get_user_stats(user_id)
    achievements = await gamification_engine.get_user_achievements(user_id)
    active_challenges = await gamification_engine.get_active_challenges()

    return {
        'stats': asdict(stats),
        'achievements': achievements,
        'active_challenges': [asdict(c) for c in active_challenges],
        'available_badges': [asdict(b) for b in gamification_engine.achievement_definitions if not b.hidden]
    }

async def get_global_leaderboard(period: str = "monthly") -> List[LeaderboardEntry]:
    """Get global leaderboard"""
    return await gamification_engine.get_leaderboard(period)

def get_level_info(total_points: int) -> Dict:
    """Get level information for given points"""
    engine = gamification_engine
    level = engine._calculate_level(total_points)

    current_threshold = engine.level_thresholds[level]
    next_threshold = engine.level_thresholds[level + 1] if level + 1 < len(engine.level_thresholds) else total_points

    return {
        'current_level': level,
        'current_points': total_points,
        'points_in_level': total_points - current_threshold,
        'points_to_next_level': next_threshold - total_points,
        'progress_to_next_level': (total_points - current_threshold) / (next_threshold - current_threshold)
    }