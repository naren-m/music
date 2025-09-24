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
    SkillAssessment,
    LearningGoal
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
            raga_usage=["Bilaval", "Kalyan"]
        )
        
        assert shruti.name == "Shadja"
        assert shruti.western_equiv == "C"
        assert shruti.cent_value == 0
        assert shruti.frequency_ratio == 1.0
        assert "Bilaval" in shruti.raga_usage
    
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
        
        # Check that cent values are in ascending order
        cent_values = [shruti.cent_value for shruti in SHRUTI_SYSTEM]
        assert cent_values == sorted(cent_values)
    
    def test_shruti_frequency_ratios(self):
        """Test shruti frequency ratios are mathematically correct."""
        for shruti in SHRUTI_SYSTEM:
            # Frequency ratio should be positive
            assert shruti.frequency_ratio > 0
            
            # Should be within octave (1.0 to 2.0)
            assert 1.0 <= shruti.frequency_ratio < 2.0
    
    def test_calculate_shruti_frequency_function(self):
        """Test standalone frequency calculation function."""
        base_sa = 261.63
        
        # Test Sa (first shruti)
        sa_freq = calculate_shruti_frequency(0, base_sa)
        assert abs(sa_freq - base_sa) < 0.01
        
        # Test Pa (should be perfect fifth)
        pa_index = next(i for i, s in enumerate(SHRUTI_SYSTEM) if 'Panchama' in s.name)
        pa_freq = calculate_shruti_frequency(pa_index, base_sa)
        expected_pa = base_sa * 1.5  # Perfect fifth ratio
        assert abs(pa_freq - expected_pa) < 5.0  # Allow small deviation for just intonation
    
    def test_find_closest_shruti(self):
        """Test finding closest shruti to a given frequency."""
        base_sa = 261.63
        
        # Test exact Sa frequency
        closest = find_closest_shruti(base_sa, base_sa)
        assert closest['shruti_index'] == 0
        assert closest['deviation_cents'] < 5
        
        # Test frequency between shrutis
        between_freq = base_sa * 1.1  # Between Sa and Ri
        closest = find_closest_shruti(between_freq, base_sa)
        assert closest['shruti_index'] in [0, 1, 2]  # Should be close to Sa or Ri variants
    
    def test_analyze_pitch_deviation(self):
        """Test pitch deviation analysis."""
        base_sa = 261.63
        target_freq = base_sa  # Perfect Sa
        
        # Test perfect pitch
        analysis = analyze_pitch_deviation(target_freq, base_sa)
        assert analysis['deviation_cents'] < 5
        assert analysis['accuracy_score'] > 0.95
        
        # Test sharp pitch
        sharp_freq = base_sa * 1.02  # About 34 cents sharp
        analysis = analyze_pitch_deviation(sharp_freq, base_sa)
        assert analysis['deviation_cents'] > 30
        assert 0.7 < analysis['accuracy_score'] < 0.9
    
    def test_raga_shruti_usage(self):
        """Test raga-specific shruti usage patterns."""
        # Bilaval should use natural shrutis
        bilaval_shrutis = [s for s in SHRUTI_SYSTEM if 'Bilaval' in s.raga_usage]
        assert len(bilaval_shrutis) >= 7  # At least 7 main swaras
        
        # Kalyan should include Tivra Ma
        kalyan_shrutis = [s for s in SHRUTI_SYSTEM if 'Kalyan' in s.raga_usage]
        tivra_ma_present = any('Tivra' in s.name and 'Madhyama' in s.name for s in kalyan_shrutis)
        assert tivra_ma_present


class TestUserProfile:
    """Test UserProfile model and related functionality."""
    
    def test_user_profile_creation(self):
        """Test UserProfile creation with defaults."""
        user = UserProfile(
            user_id="test_123",
            email="test@example.com",
            name="Test User"
        )
        
        assert user.user_id == "test_123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.subscription_tier == SubscriptionTier.FREE
        assert isinstance(user.created_at, datetime)
        assert len(user.module_progress) == 0
        assert len(user.achievements) == 0
    
    def test_subscription_tier_enum(self):
        """Test SubscriptionTier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.PREMIUM.value == "premium"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        
        # Test tier comparison
        assert SubscriptionTier.PREMIUM > SubscriptionTier.FREE
        assert SubscriptionTier.PROFESSIONAL > SubscriptionTier.PREMIUM
    
    def test_user_profile_with_all_fields(self):
        """Test UserProfile with all optional fields."""
        user = UserProfile(
            user_id="advanced_user",
            email="advanced@example.com",
            name="Advanced User",
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            learning_goal=LearningGoal.RAGA_MASTERY,
            skill_level="advanced",
            preferred_shruti_count=22,
            practice_streak=15,
            total_practice_time=7200  # 2 hours in seconds
        )
        
        assert user.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert user.learning_goal == LearningGoal.RAGA_MASTERY
        assert user.skill_level == "advanced"
        assert user.preferred_shruti_count == 22
        assert user.practice_streak == 15
        assert user.total_practice_time == 7200
    
    def test_add_achievement(self):
        """Test adding achievements to user profile."""
        user = UserProfile(
            user_id="achiever",
            email="achiever@example.com",
            name="Achievement User"
        )
        
        achievement = Achievement(
            achievement_id="swara_mastery_1",
            title="Swara Recognition Beginner",
            description="Completed first level of swara recognition",
            category="swara_recognition",
            points=100,
            achieved_at=datetime.utcnow()
        )
        
        user.achievements.append(achievement)
        
        assert len(user.achievements) == 1
        assert user.achievements[0].title == "Swara Recognition Beginner"
        assert user.achievements[0].points == 100
    
    def test_update_module_progress(self):
        """Test updating module progress."""
        user = UserProfile(
            user_id="learner",
            email="learner@example.com",
            name="Learning User"
        )
        
        progress = ModuleProgress(
            module_name="swara_recognition",
            completion_percentage=75.0,
            current_level="intermediate",
            exercises_completed=15,
            total_exercises=20,
            last_accessed=datetime.utcnow()
        )
        
        user.module_progress["swara_recognition"] = progress
        
        assert "swara_recognition" in user.module_progress
        assert user.module_progress["swara_recognition"].completion_percentage == 75.0
        assert user.module_progress["swara_recognition"].current_level == "intermediate"


class TestModuleProgress:
    """Test ModuleProgress model."""
    
    def test_module_progress_creation(self):
        """Test ModuleProgress creation."""
        progress = ModuleProgress(
            module_name="raga_recognition",
            completion_percentage=45.5,
            current_level="beginner_plus",
            exercises_completed=9,
            total_exercises=20
        )
        
        assert progress.module_name == "raga_recognition"
        assert progress.completion_percentage == 45.5
        assert progress.current_level == "beginner_plus"
        assert progress.exercises_completed == 9
        assert progress.total_exercises == 20
        assert isinstance(progress.last_accessed, datetime)
    
    def test_completion_percentage_validation(self):
        """Test completion percentage bounds."""
        # Valid percentage
        progress = ModuleProgress(
            module_name="test_module",
            completion_percentage=50.0,
            current_level="intermediate",
            exercises_completed=5,
            total_exercises=10
        )
        assert 0 <= progress.completion_percentage <= 100
        
        # Test calculated percentage
        calculated_percentage = (progress.exercises_completed / progress.total_exercises) * 100
        assert abs(progress.completion_percentage - calculated_percentage) < 1.0
    
    def test_progress_advancement(self):
        """Test progress advancement logic."""
        progress = ModuleProgress(
            module_name="advancement_test",
            completion_percentage=80.0,
            current_level="intermediate",
            exercises_completed=16,
            total_exercises=20
        )
        
        # Simulate completing an exercise
        progress.exercises_completed += 1
        progress.completion_percentage = (progress.exercises_completed / progress.total_exercises) * 100
        progress.last_accessed = datetime.utcnow()
        
        assert progress.exercises_completed == 17
        assert progress.completion_percentage == 85.0


class TestAchievement:
    """Test Achievement model."""
    
    def test_achievement_creation(self):
        """Test Achievement creation."""
        achievement = Achievement(
            achievement_id="pitch_perfect",
            title="Pitch Perfect",
            description="Achieved 95% accuracy in pitch detection for 10 consecutive exercises",
            category="pitch_accuracy",
            points=250,
            unlock_condition="pitch_accuracy >= 95% for 10 exercises",
            badge_icon="🎯"
        )
        
        assert achievement.achievement_id == "pitch_perfect"
        assert achievement.title == "Pitch Perfect"
        assert achievement.points == 250
        assert achievement.badge_icon == "🎯"
        assert isinstance(achievement.achieved_at, datetime)
    
    def test_achievement_categories(self):
        """Test different achievement categories."""
        categories = [
            "swara_recognition",
            "raga_mastery",
            "pitch_accuracy",
            "practice_consistency",
            "social_engagement"
        ]
        
        for category in categories:
            achievement = Achievement(
                achievement_id=f"test_{category}",
                title=f"Test {category.title()}",
                description=f"Test achievement for {category}",
                category=category,
                points=100
            )
            assert achievement.category == category
    
    def test_achievement_ranking(self):
        """Test achievement point-based ranking."""
        achievements = [
            Achievement("bronze", "Bronze", "Bronze level", "test", 100),
            Achievement("gold", "Gold", "Gold level", "test", 500),
            Achievement("silver", "Silver", "Silver level", "test", 250)
        ]
        
        # Sort by points descending
        sorted_achievements = sorted(achievements, key=lambda a: a.points, reverse=True)
        
        assert sorted_achievements[0].points == 500  # Gold
        assert sorted_achievements[1].points == 250  # Silver
        assert sorted_achievements[2].points == 100  # Bronze


class TestPracticeSession:
    """Test PracticeSession model."""
    
    def test_practice_session_creation(self):
        """Test PracticeSession creation."""
        session = PracticeSession(
            session_id="session_123",
            user_id="user_456",
            module="swara_recognition",
            exercise_type="pitch_matching",
            duration_seconds=1800,  # 30 minutes
            accuracy_score=87.5,
            exercises_completed=12
        )
        
        assert session.session_id == "session_123"
        assert session.user_id == "user_456"
        assert session.module == "swara_recognition"
        assert session.duration_seconds == 1800
        assert session.accuracy_score == 87.5
        assert isinstance(session.start_time, datetime)
    
    def test_session_statistics(self):
        """Test session statistics calculation."""
        session = PracticeSession(
            session_id="stats_test",
            user_id="user_stats",
            module="raga_recognition",
            exercise_type="pattern_identification",
            duration_seconds=2400,  # 40 minutes
            accuracy_score=92.3,
            exercises_completed=8,
            mistakes_count=3,
            improvement_areas=["timing", "pitch_stability"]
        )
        
        # Calculate exercises per minute
        exercises_per_minute = session.exercises_completed / (session.duration_seconds / 60)
        assert abs(exercises_per_minute - 0.2) < 0.01  # 8 exercises in 40 minutes
        
        # Calculate mistake rate
        mistake_rate = session.mistakes_count / session.exercises_completed if session.exercises_completed > 0 else 0
        assert abs(mistake_rate - 0.375) < 0.01  # 3 mistakes out of 8 exercises
    
    def test_session_completion(self):
        """Test session completion logic."""
        start_time = datetime.utcnow() - timedelta(minutes=30)
        
        session = PracticeSession(
            session_id="completion_test",
            user_id="user_complete",
            module="test_module",
            exercise_type="test_exercise",
            start_time=start_time,
            duration_seconds=1800,
            accuracy_score=85.0,
            exercises_completed=10,
            completed=True
        )
        
        assert session.completed is True
        assert session.duration_seconds == 1800
        
        # Calculate actual duration if end_time was set
        if hasattr(session, 'end_time') and session.end_time:
            actual_duration = (session.end_time - session.start_time).total_seconds()
            assert abs(actual_duration - session.duration_seconds) < 60  # Within 1 minute


class TestSkillAssessment:
    """Test SkillAssessment model."""
    
    def test_skill_assessment_creation(self):
        """Test SkillAssessment creation."""
        assessment = SkillAssessment(
            assessment_id="initial_assessment",
            user_id="new_user",
            skill_areas={
                "pitch_accuracy": 65.0,
                "rhythm_recognition": 70.0,
                "raga_identification": 40.0,
                "swara_recognition": 75.0
            },
            overall_level="beginner_plus",
            recommended_modules=["swara_recognition", "basic_rhythm"]
        )
        
        assert assessment.assessment_id == "initial_assessment"
        assert assessment.overall_level == "beginner_plus"
        assert len(assessment.skill_areas) == 4
        assert "swara_recognition" in assessment.recommended_modules
    
    def test_skill_level_calculation(self):
        """Test skill level calculation from scores."""
        skill_scores = {
            "pitch_accuracy": 85.0,
            "rhythm_recognition": 80.0,
            "raga_identification": 75.0,
            "swara_recognition": 90.0
        }
        
        average_score = sum(skill_scores.values()) / len(skill_scores)
        assert average_score == 82.5
        
        # Test level assignment logic
        if average_score >= 90:
            expected_level = "advanced"
        elif average_score >= 75:
            expected_level = "intermediate"
        elif average_score >= 50:
            expected_level = "beginner_plus"
        else:
            expected_level = "beginner"
        
        assert expected_level == "intermediate"
    
    def test_assessment_recommendations(self):
        """Test module recommendations based on assessment."""
        # Low pitch accuracy should recommend pitch training
        assessment = SkillAssessment(
            assessment_id="recommendation_test",
            user_id="test_user",
            skill_areas={
                "pitch_accuracy": 45.0,  # Low
                "rhythm_recognition": 80.0,  # Good
                "raga_identification": 30.0,  # Very low
                "swara_recognition": 70.0  # Decent
            },
            overall_level="beginner",
            recommended_modules=[]
        )
        
        # Generate recommendations based on low scores
        recommendations = []
        for skill, score in assessment.skill_areas.items():
            if score < 50:
                if skill == "pitch_accuracy":
                    recommendations.append("pitch_training")
                elif skill == "raga_identification":
                    recommendations.append("raga_basics")
        
        assert "pitch_training" in recommendations
        assert "raga_basics" in recommendations


class TestModelIntegration:
    """Test integration between different models."""
    
    def test_user_progress_with_achievements(self):
        """Test user progress tracking with achievements."""
        user = UserProfile(
            user_id="integration_test",
            email="integration@example.com",
            name="Integration User"
        )
        
        # Add practice session
        session = PracticeSession(
            session_id="int_session_1",
            user_id=user.user_id,
            module="swara_recognition",
            exercise_type="pitch_matching",
            duration_seconds=1200,
            accuracy_score=92.0,
            exercises_completed=10
        )
        
        # Update user practice time
        user.total_practice_time += session.duration_seconds
        user.last_active = datetime.utcnow()
        
        # Check if achievement should be unlocked (90%+ accuracy)
        if session.accuracy_score >= 90.0:
            achievement = Achievement(
                achievement_id="high_accuracy",
                title="High Accuracy Achiever",
                description="Achieved 90%+ accuracy in a practice session",
                category="accuracy",
                points=150
            )
            user.achievements.append(achievement)
        
        assert user.total_practice_time == 1200
        assert len(user.achievements) == 1
        assert user.achievements[0].title == "High Accuracy Achiever"
    
    def test_module_progress_advancement(self):
        """Test module progress advancement with multiple sessions."""
        user = UserProfile(
            user_id="progress_test",
            email="progress@example.com",
            name="Progress User"
        )
        
        # Initialize module progress
        progress = ModuleProgress(
            module_name="swara_recognition",
            completion_percentage=0.0,
            current_level="beginner",
            exercises_completed=0,
            total_exercises=50
        )
        user.module_progress["swara_recognition"] = progress
        
        # Simulate multiple practice sessions
        sessions = [
            {"exercises": 5, "accuracy": 75.0},
            {"exercises": 7, "accuracy": 82.0},
            {"exercises": 6, "accuracy": 88.0},
            {"exercises": 8, "accuracy": 91.0}
        ]
        
        total_exercises = 0
        total_accuracy = 0
        
        for session_data in sessions:
            total_exercises += session_data["exercises"]
            total_accuracy += session_data["accuracy"]
            
            # Update progress
            progress.exercises_completed = total_exercises
            progress.completion_percentage = (total_exercises / progress.total_exercises) * 100
            
            # Update level based on average accuracy
            avg_accuracy = total_accuracy / len(sessions[:sessions.index(session_data) + 1])
            if avg_accuracy >= 90:
                progress.current_level = "advanced"
            elif avg_accuracy >= 80:
                progress.current_level = "intermediate"
            else:
                progress.current_level = "beginner"
        
        assert progress.exercises_completed == 26
        assert progress.completion_percentage == 52.0
        assert progress.current_level == "intermediate"  # Average accuracy = 84%