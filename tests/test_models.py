"""
Unit Tests for Core Models
Tests for shruti system, user models, and data structures
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from core.models.shruti import (
    Shruti,
    SHRUTI_SYSTEM,
    calculate_shruti_frequency,
    find_closest_shruti,
    analyze_pitch_deviation
)
from core.models.user import (
    UserProfile,
    SubscriptionTier,
    ModuleProgress,
    Achievement,
    PracticeSession,
    LearningGoal,
    SkillLevel,
)


class TestShrutiModel:
    """Test Shruti model and related functions."""

    def test_shruti_creation(self):
        """Test Shruti dataclass creation."""
        shruti = Shruti(
            name="Shadja",
            western_equiv="C",
            cent_value=0,
            frequency_ratio=1.0,
            raga_usage=["All ragas"]
        )

        assert shruti.name == "Shadja"
        assert shruti.western_equiv == "C"
        assert shruti.cent_value == 0
        assert shruti.frequency_ratio == 1.0
        assert "All ragas" in shruti.raga_usage

    def test_frequency_calculation(self):
        """Test frequency calculation from ratio."""
        shruti = Shruti(
            name="Shadja",
            western_equiv="C",
            cent_value=0,
            frequency_ratio=1.0,
            raga_usage=[]
        )

        base_sa = 261.63
        frequency = shruti.calculate_frequency(base_sa)

        assert frequency == base_sa
        assert isinstance(frequency, float)

    def test_shruti_system_completeness(self):
        """Test that SHRUTI_SYSTEM contains all 22 shrutis."""
        assert len(SHRUTI_SYSTEM) == 22

        # Check that all shruti names are unique
        names = [shruti.name for shruti in SHRUTI_SYSTEM]
        assert len(names) == len(set(names))

    def test_shruti_frequency_ratios(self):
        """Test shruti frequency ratios are mathematically correct."""
        for shruti in SHRUTI_SYSTEM:
            # Frequency ratio should be positive
            assert shruti.frequency_ratio > 0

            # Should be within octave (allow some leeway)
            assert 0.9 <= shruti.frequency_ratio <= 2.1

    def test_calculate_shruti_frequency_function(self):
        """Test standalone frequency calculation function."""
        base_sa = 261.63

        # Test Sa (first shruti)
        sa_freq = calculate_shruti_frequency(0, base_sa)
        assert abs(sa_freq - base_sa) < 0.01

    def test_calculate_shruti_frequency_out_of_range(self):
        """Test that out of range shruti index raises error."""
        with pytest.raises(IndexError):
            calculate_shruti_frequency(100, 261.63)

    def test_find_closest_shruti(self):
        """Test finding closest shruti to a given frequency."""
        base_sa = 261.63

        # Test exact Sa frequency
        closest = find_closest_shruti(base_sa, base_sa)
        assert closest['shruti_index'] == 0
        assert abs(closest['deviation_cents']) < 5

        # Test frequency between shrutis
        between_freq = base_sa * 1.1  # Between Sa and Ri
        closest = find_closest_shruti(between_freq, base_sa)
        assert closest['shruti_index'] >= 0  # Should find a valid shruti

    def test_analyze_pitch_deviation(self):
        """Test pitch deviation analysis."""
        base_sa = 261.63
        target_freq = base_sa  # Perfect Sa

        # Test perfect pitch
        analysis = analyze_pitch_deviation(target_freq, base_sa)
        assert abs(analysis['deviation_cents']) < 5
        assert analysis['accuracy_score'] > 0.95
        assert analysis['direction'] in ['sharp', 'flat', 'perfect']

        # Test sharp pitch
        sharp_freq = base_sa * 1.02  # About 34 cents sharp
        analysis = analyze_pitch_deviation(sharp_freq, base_sa)
        assert analysis['deviation_cents'] > 0
        assert analysis['direction'] == 'sharp'

    def test_analyze_pitch_deviation_flat(self):
        """Test pitch deviation analysis for flat pitch."""
        base_sa = 261.63
        flat_freq = base_sa * 0.98  # About 35 cents flat

        analysis = analyze_pitch_deviation(flat_freq, base_sa)
        assert analysis['deviation_cents'] < 0
        assert analysis['direction'] == 'flat'


class TestUserProfile:
    """Test UserProfile model and related functionality."""

    def test_user_profile_creation(self):
        """Test UserProfile creation with defaults."""
        user = UserProfile(
            user_id="test_123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            created_at=datetime.utcnow()
        )

        assert user.user_id == "test_123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.subscription_tier == SubscriptionTier.FREE
        assert isinstance(user.created_at, datetime)
        assert len(user.module_progress) == 0
        assert len(user.achievements) == 0

    def test_subscription_tier_enum(self):
        """Test SubscriptionTier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.STUDENT.value == "student"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        assert SubscriptionTier.GURU.value == "guru"

    def test_learning_goal_enum(self):
        """Test LearningGoal enum values."""
        assert LearningGoal.BEGINNER.value == "beginner"
        assert LearningGoal.CLASSICAL_VOCAL.value == "classical_vocal"
        assert LearningGoal.INSTRUMENTAL.value == "instrumental"

    def test_skill_level_enum(self):
        """Test SkillLevel enum values."""
        assert SkillLevel.NOVICE.value == "novice"
        assert SkillLevel.BEGINNER.value == "beginner"
        assert SkillLevel.INTERMEDIATE.value == "intermediate"
        assert SkillLevel.ADVANCED.value == "advanced"
        assert SkillLevel.EXPERT.value == "expert"

    def test_is_premium_free_user(self):
        """Test is_premium for free user."""
        user = UserProfile(
            user_id="free_user",
            email="free@example.com",
            username="freeuser",
            full_name="Free User",
            created_at=datetime.utcnow(),
            subscription_tier=SubscriptionTier.FREE
        )

        assert user.is_premium is False

    def test_is_premium_premium_user(self):
        """Test is_premium for premium user."""
        user = UserProfile(
            user_id="premium_user",
            email="premium@example.com",
            username="premiumuser",
            full_name="Premium User",
            created_at=datetime.utcnow(),
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            subscription_expires=datetime.utcnow() + timedelta(days=30)
        )

        assert user.is_premium is True

    def test_is_premium_expired_subscription(self):
        """Test is_premium for expired subscription."""
        user = UserProfile(
            user_id="expired_user",
            email="expired@example.com",
            username="expireduser",
            full_name="Expired User",
            created_at=datetime.utcnow(),
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            subscription_expires=datetime.utcnow() - timedelta(days=1)
        )

        assert user.is_premium is False

    def test_add_practice_session(self):
        """Test adding practice session to user."""
        user = UserProfile(
            user_id="session_test",
            email="session@example.com",
            username="sessionuser",
            full_name="Session User",
            created_at=datetime.utcnow()
        )

        session = PracticeSession(
            session_id="session_1",
            user_id=user.user_id,
            module="swara_recognition",
            exercise_type="pitch_matching",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            end_time=datetime.utcnow(),
            duration_minutes=30.0,
            accuracy_score=85.0
        )

        user.add_practice_session(session)

        assert user.total_sessions == 1
        assert user.total_practice_time == 30.0
        assert "swara_recognition" in user.module_progress

    def test_get_weekly_practice_time(self):
        """Test getting weekly practice time."""
        user = UserProfile(
            user_id="weekly_test",
            email="weekly@example.com",
            username="weeklyuser",
            full_name="Weekly User",
            created_at=datetime.utcnow()
        )

        # Add sessions from this week
        for i in range(3):
            session = PracticeSession(
                session_id=f"session_{i}",
                user_id=user.user_id,
                module="swara_recognition",
                exercise_type="pitch_matching",
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i) + timedelta(minutes=20),
                duration_minutes=20.0,
                accuracy_score=80.0
            )
            user.add_practice_session(session)

        weekly_time = user.get_weekly_practice_time()
        assert weekly_time == 60.0  # 3 sessions * 20 minutes

    def test_to_dict(self):
        """Test converting user profile to dictionary."""
        user = UserProfile(
            user_id="dict_test",
            email="dict@example.com",
            username="dictuser",
            full_name="Dict User",
            created_at=datetime.utcnow()
        )

        user_dict = user.to_dict()

        assert user_dict['user_id'] == "dict_test"
        assert user_dict['email'] == "dict@example.com"
        assert user_dict['username'] == "dictuser"
        assert 'created_at' in user_dict
        assert 'subscription_tier' in user_dict


class TestModuleProgress:
    """Test ModuleProgress model."""

    def test_module_progress_creation(self):
        """Test ModuleProgress creation."""
        progress = ModuleProgress(
            module_name="raga_recognition",
            skill_level=SkillLevel.BEGINNER,
            completion_percentage=45.5
        )

        assert progress.module_name == "raga_recognition"
        assert progress.completion_percentage == 45.5
        assert progress.skill_level == SkillLevel.BEGINNER

    def test_update_progress(self):
        """Test updating progress with a session."""
        progress = ModuleProgress(
            module_name="swara_recognition",
            skill_level=SkillLevel.BEGINNER
        )

        session = PracticeSession(
            session_id="update_test",
            user_id="user_1",
            module="swara_recognition",
            exercise_type="pitch_matching",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            end_time=datetime.utcnow(),
            duration_minutes=30.0,
            accuracy_score=85.0
        )

        progress.update_progress(session)

        assert progress.total_practice_time == 30.0
        assert progress.average_accuracy == 85.0


class TestAchievement:
    """Test Achievement model."""

    def test_achievement_creation(self):
        """Test Achievement creation."""
        achievement = Achievement(
            achievement_id="pitch_perfect",
            name="Pitch Perfect",
            description="Achieved 95% accuracy in pitch detection",
            category="pitch_accuracy",
            icon="🎯",
            points=250,
            earned_date=datetime.utcnow()
        )

        assert achievement.achievement_id == "pitch_perfect"
        assert achievement.name == "Pitch Perfect"
        assert achievement.points == 250
        assert achievement.icon == "🎯"
        assert achievement.rarity == "common"  # Default value

    def test_achievement_rarity(self):
        """Test achievement rarity levels."""
        rarities = ["common", "rare", "epic", "legendary"]

        for rarity in rarities:
            achievement = Achievement(
                achievement_id=f"{rarity}_achievement",
                name=f"{rarity.title()} Achievement",
                description=f"A {rarity} achievement",
                category="test",
                icon="🏆",
                points=100,
                earned_date=datetime.utcnow(),
                rarity=rarity
            )
            assert achievement.rarity == rarity


class TestPracticeSession:
    """Test PracticeSession model."""

    def test_practice_session_creation(self):
        """Test PracticeSession creation."""
        start_time = datetime.utcnow() - timedelta(minutes=30)
        session = PracticeSession(
            session_id="session_123",
            user_id="user_456",
            module="swara_recognition",
            exercise_type="pitch_matching",
            start_time=start_time,
            duration_minutes=30.0,
            accuracy_score=87.5
        )

        assert session.session_id == "session_123"
        assert session.user_id == "user_456"
        assert session.module == "swara_recognition"
        assert session.duration_minutes == 30.0
        assert session.accuracy_score == 87.5
        assert session.is_active is True  # end_time is None

    def test_end_session(self):
        """Test ending a practice session."""
        start_time = datetime.utcnow() - timedelta(minutes=30)
        session = PracticeSession(
            session_id="end_test",
            user_id="user_test",
            module="swara_recognition",
            exercise_type="pitch_matching",
            start_time=start_time
        )

        assert session.is_active is True

        session.end_session()

        assert session.is_active is False
        assert session.end_time is not None
        assert session.duration_minutes > 0


class TestModelIntegration:
    """Test integration between different models."""

    def test_user_progress_with_achievements(self):
        """Test user progress tracking with achievements."""
        user = UserProfile(
            user_id="integration_test",
            email="integration@example.com",
            username="integrationuser",
            full_name="Integration User",
            created_at=datetime.utcnow()
        )

        # Add practice session
        session = PracticeSession(
            session_id="int_session_1",
            user_id=user.user_id,
            module="swara_recognition",
            exercise_type="pitch_matching",
            start_time=datetime.utcnow() - timedelta(minutes=20),
            end_time=datetime.utcnow(),
            duration_minutes=20.0,
            accuracy_score=92.0
        )

        user.add_practice_session(session)

        # Check if achievement should be unlocked (90%+ accuracy)
        if session.accuracy_score >= 90.0:
            achievement = Achievement(
                achievement_id="high_accuracy",
                name="High Accuracy Achiever",
                description="Achieved 90%+ accuracy in a practice session",
                category="accuracy",
                icon="🎯",
                points=150,
                earned_date=datetime.utcnow()
            )
            user.achievements.append(achievement)

        assert user.total_practice_time == 20.0
        assert len(user.achievements) == 1
        assert user.achievements[0].name == "High Accuracy Achiever"
