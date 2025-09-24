"""
User models for Carnatic learning application
Includes user profiles, progress tracking, and subscription management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json


class SubscriptionTier(Enum):
    """Subscription tier levels"""
    FREE = "free"
    STUDENT = "student"
    PROFESSIONAL = "professional"
    GURU = "guru"


class LearningGoal(Enum):
    """User learning goals"""
    BEGINNER = "beginner"
    CLASSICAL_VOCAL = "classical_vocal"
    INSTRUMENTAL = "instrumental"
    MUSIC_THEORY = "music_theory"
    PERFORMANCE = "performance"
    TEACHING = "teaching"


class SkillLevel(Enum):
    """Skill progression levels"""
    NOVICE = "novice"
    BEGINNER = "beginner"
    STUDENT = "student"
    PRACTITIONER = "practitioner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    ARTIST = "artist"


@dataclass
class UserPreferences:
    """User preferences and settings"""
    language: str = "en"  # en, ta, te, kn, ml, hi
    base_sa_frequency: float = 261.63  # C4 by default
    preferred_tempo: int = 120  # BPM
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {
        "practice_reminders": True,
        "achievement_notifications": True,
        "social_updates": True,
        "expert_feedback": True
    })
    audio_settings: Dict[str, Any] = field(default_factory=lambda: {
        "tanpura_volume": 0.7,
        "metronome_volume": 0.5,
        "feedback_sounds": True,
        "haptic_feedback": True
    })
    visual_settings: Dict[str, Any] = field(default_factory=lambda: {
        "notation_style": "carnatic",  # carnatic, western, both
        "color_scheme": "traditional",  # traditional, modern, dark
        "animations": True,
        "high_contrast": False
    })


@dataclass
class PracticeSession:
    """Individual practice session record"""
    session_id: str
    user_id: str
    module: str  # swara, sarali, raga, etc.
    exercise_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: float = 0.0
    accuracy_score: float = 0.0
    consistency_score: float = 0.0
    notes_practiced: List[str] = field(default_factory=list)
    achievements_earned: List[str] = field(default_factory=list)
    recordings: List[str] = field(default_factory=list)  # File paths/URLs
    notes: str = ""
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.end_time is None
    
    def end_session(self) -> None:
        """End the practice session"""
        if self.end_time is None:
            self.end_time = datetime.utcnow()
            self.duration_minutes = (self.end_time - self.start_time).total_seconds() / 60


@dataclass
class ModuleProgress:
    """Progress tracking for learning modules"""
    module_name: str
    skill_level: SkillLevel
    completion_percentage: float = 0.0
    lessons_completed: List[str] = field(default_factory=list)
    lessons_unlocked: List[str] = field(default_factory=list)
    total_practice_time: float = 0.0  # in minutes
    last_practiced: Optional[datetime] = None
    average_accuracy: float = 0.0
    streak_days: int = 0
    personal_best: Dict[str, float] = field(default_factory=dict)
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    
    def update_progress(self, session: PracticeSession) -> None:
        """Update progress based on practice session"""
        self.total_practice_time += session.duration_minutes
        self.last_practiced = session.end_time or datetime.utcnow()
        
        # Update average accuracy (weighted)
        if self.average_accuracy == 0.0:
            self.average_accuracy = session.accuracy_score
        else:
            # Weighted average with more weight to recent sessions
            self.average_accuracy = (self.average_accuracy * 0.8) + (session.accuracy_score * 0.2)


@dataclass
class Achievement:
    """User achievement record"""
    achievement_id: str
    name: str
    description: str
    category: str  # skill, streak, social, milestone
    icon: str
    points: int
    earned_date: datetime
    rarity: str = "common"  # common, rare, epic, legendary
    
    
@dataclass
class UserProfile:
    """Complete user profile with learning data"""
    user_id: str
    email: str
    username: str
    full_name: str
    created_at: datetime
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires: Optional[datetime] = None
    preferences: UserPreferences = field(default_factory=UserPreferences)
    learning_goals: List[LearningGoal] = field(default_factory=list)
    
    # Progress tracking
    overall_skill_level: SkillLevel = SkillLevel.NOVICE
    total_practice_time: float = 0.0  # in minutes
    practice_streak: int = 0
    longest_streak: int = 0
    total_sessions: int = 0
    
    # Module progress
    module_progress: Dict[str, ModuleProgress] = field(default_factory=dict)
    achievements: List[Achievement] = field(default_factory=list)
    practice_history: List[PracticeSession] = field(default_factory=list)
    
    # Social features
    friends: List[str] = field(default_factory=list)  # User IDs
    groups: List[str] = field(default_factory=list)   # Group IDs
    teacher_id: Optional[str] = None
    students: List[str] = field(default_factory=list)  # For teachers
    
    # Analytics
    weekly_stats: Dict[str, Any] = field(default_factory=dict)
    monthly_stats: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return (self.subscription_tier != SubscriptionTier.FREE and 
                (self.subscription_expires is None or 
                 self.subscription_expires > datetime.utcnow()))
    
    def add_practice_session(self, session: PracticeSession) -> None:
        """Add a practice session and update statistics"""
        self.practice_history.append(session)
        self.total_sessions += 1
        self.total_practice_time += session.duration_minutes
        
        # Update module progress
        if session.module not in self.module_progress:
            self.module_progress[session.module] = ModuleProgress(session.module, SkillLevel.BEGINNER)
        
        self.module_progress[session.module].update_progress(session)
        self._update_streak()
    
    def _update_streak(self) -> None:
        """Update practice streak based on recent sessions"""
        today = datetime.utcnow().date()
        recent_dates = set()
        
        for session in self.practice_history[-30:]:  # Last 30 sessions
            if session.end_time:
                recent_dates.add(session.end_time.date())
        
        # Calculate consecutive days
        streak = 0
        current_date = today
        
        while current_date in recent_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        self.practice_streak = streak
        self.longest_streak = max(self.longest_streak, streak)
    
    def get_weekly_practice_time(self) -> float:
        """Get practice time for current week"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_time = sum(
            session.duration_minutes
            for session in self.practice_history
            if session.start_time >= week_ago
        )
        return weekly_time
    
    def get_skill_distribution(self) -> Dict[str, float]:
        """Get distribution of skills across modules"""
        if not self.module_progress:
            return {}
        
        total_completion = sum(p.completion_percentage for p in self.module_progress.values())
        module_count = len(self.module_progress)
        
        return {
            module: progress.completion_percentage
            for module, progress in self.module_progress.items()
        }
    
    def get_learning_recommendations(self) -> List[Dict[str, Any]]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        # Find weakest module for improvement
        if self.module_progress:
            weakest_module = min(
                self.module_progress.items(),
                key=lambda x: x[1].completion_percentage
            )
            
            recommendations.append({
                "type": "module_focus",
                "module": weakest_module[0],
                "reason": f"Improve {weakest_module[0]} skills",
                "priority": "high"
            })
        
        # Practice streak recommendation
        if self.practice_streak == 0:
            recommendations.append({
                "type": "practice_reminder",
                "message": "Start a new practice streak today!",
                "priority": "medium"
            })
        
        # Time-based recommendations
        weekly_time = self.get_weekly_practice_time()
        if weekly_time < 60:  # Less than 1 hour per week
            recommendations.append({
                "type": "practice_time",
                "message": "Try to practice at least 10 minutes daily",
                "priority": "medium"
            })
        
        return recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user profile to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat(),
            "subscription_tier": self.subscription_tier.value,
            "subscription_expires": self.subscription_expires.isoformat() if self.subscription_expires else None,
            "preferences": {
                "language": self.preferences.language,
                "base_sa_frequency": self.preferences.base_sa_frequency,
                "preferred_tempo": self.preferences.preferred_tempo,
                "notification_settings": self.preferences.notification_settings,
                "audio_settings": self.preferences.audio_settings,
                "visual_settings": self.preferences.visual_settings
            },
            "learning_goals": [goal.value for goal in self.learning_goals],
            "overall_skill_level": self.overall_skill_level.value,
            "total_practice_time": self.total_practice_time,
            "practice_streak": self.practice_streak,
            "total_sessions": self.total_sessions,
            "module_progress": {
                module: {
                    "skill_level": progress.skill_level.value,
                    "completion_percentage": progress.completion_percentage,
                    "total_practice_time": progress.total_practice_time,
                    "average_accuracy": progress.average_accuracy,
                    "streak_days": progress.streak_days
                }
                for module, progress in self.module_progress.items()
            }
        }


# Database models (for SQLAlchemy or similar ORM)
class UserModel:
    """Database model for user data"""
    __tablename__ = 'users'
    
    # Primary fields
    id: str  # Primary key
    email: str  # Unique
    username: str  # Unique
    password_hash: str
    created_at: datetime
    updated_at: datetime
    
    # Profile data (JSON)
    profile_data: str  # JSON string of UserProfile
    
    # Subscription
    subscription_tier: str
    subscription_expires: Optional[datetime]
    
    # Quick access fields (denormalized for performance)
    total_practice_time: float
    practice_streak: int
    skill_level: str
    
    @classmethod
    def from_profile(cls, profile: UserProfile, password_hash: str):
        """Create UserModel from UserProfile"""
        return cls(
            id=profile.user_id,
            email=profile.email,
            username=profile.username,
            password_hash=password_hash,
            profile_data=json.dumps(profile.to_dict()),
            subscription_tier=profile.subscription_tier.value,
            subscription_expires=profile.subscription_expires,
            total_practice_time=profile.total_practice_time,
            practice_streak=profile.practice_streak,
            skill_level=profile.overall_skill_level.value
        )