"""
Core AI/ML Adaptive Learning Engine for Carnatic Music Platform

Implements intelligent difficulty progression, performance prediction,
and personalized learning path optimization using machine learning.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
import logging

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    ANALYTICAL = "analytical"

class SkillLevel(Enum):
    BEGINNER = 0
    NOVICE = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4

@dataclass
class UserPerformanceMetrics:
    user_id: int
    skill_level: SkillLevel
    learning_style: LearningStyle
    accuracy_history: List[float] = field(default_factory=list)
    tempo_progress: List[int] = field(default_factory=list)
    practice_duration: List[int] = field(default_factory=list)  # minutes
    mistake_patterns: Dict[str, int] = field(default_factory=dict)
    strength_areas: List[str] = field(default_factory=list)
    weakness_areas: List[str] = field(default_factory=list)
    engagement_score: float = 0.0
    retention_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class AdaptiveRecommendation:
    exercise_type: str
    difficulty_level: int
    suggested_tempo: int
    focus_areas: List[str]
    estimated_duration: int  # minutes
    confidence_score: float
    reasoning: str
    cultural_context: Optional[str] = None

class AdaptiveLearningEngine:
    """
    AI-powered adaptive learning engine that personalizes the Carnatic music
    learning experience based on individual performance patterns and preferences.
    """

    def __init__(self):
        self.user_profiles: Dict[int, UserPerformanceMetrics] = {}
        self.performance_weights = {
            'accuracy': 0.35,
            'consistency': 0.25,
            'progress_rate': 0.20,
            'retention': 0.15,
            'engagement': 0.05
        }
        self.difficulty_thresholds = {
            SkillLevel.BEGINNER: {'accuracy': 0.6, 'consistency': 0.5},
            SkillLevel.NOVICE: {'accuracy': 0.7, 'consistency': 0.6},
            SkillLevel.INTERMEDIATE: {'accuracy': 0.8, 'consistency': 0.7},
            SkillLevel.ADVANCED: {'accuracy': 0.85, 'consistency': 0.8},
            SkillLevel.EXPERT: {'accuracy': 0.9, 'consistency': 0.85}
        }

        # Exercise complexity mappings
        self.exercise_complexity = {
            'sarali_varisai': {
                'basic_arohanam': 1,
                'basic_avarohanam': 1,
                'combined_sequences': 2,
                'tempo_variations': 3,
                'rhythmic_patterns': 4
            },
            'janta_varisai': {
                'simple_doubles': 2,
                'transition_focus': 3,
                'complex_patterns': 4,
                'speed_building': 5
            },
            'alankaram': {
                'basic_patterns': 3,
                'ornamentation': 4,
                'raga_specific': 5,
                'advanced_combinations': 6
            }
        }

        self.logger = logging.getLogger(__name__)

    def initialize_user_profile(self, user_id: int, initial_assessment: Dict[str, Any]) -> UserPerformanceMetrics:
        """Initialize a new user profile based on initial assessment"""

        # Determine initial skill level from assessment
        initial_skill = self._assess_initial_skill_level(initial_assessment)

        # Identify learning style preferences
        learning_style = self._identify_learning_style(initial_assessment)

        profile = UserPerformanceMetrics(
            user_id=user_id,
            skill_level=initial_skill,
            learning_style=learning_style,
            engagement_score=0.7,  # Neutral starting engagement
            retention_rate=0.5     # Will be updated as user practices
        )

        self.user_profiles[user_id] = profile
        self.logger.info(f"Initialized profile for user {user_id}: {initial_skill}, {learning_style}")

        return profile

    def _assess_initial_skill_level(self, assessment: Dict[str, Any]) -> SkillLevel:
        """Determine initial skill level from assessment results"""

        total_score = 0
        max_score = 0

        # Basic pitch recognition (25 points)
        pitch_accuracy = assessment.get('pitch_accuracy', 0.5)
        total_score += pitch_accuracy * 25
        max_score += 25

        # Rhythm sense (25 points)
        rhythm_score = assessment.get('rhythm_accuracy', 0.5)
        total_score += rhythm_score * 25
        max_score += 25

        # Prior musical experience (25 points)
        experience_years = assessment.get('musical_experience_years', 0)
        experience_score = min(experience_years / 5, 1.0) * 25
        total_score += experience_score
        max_score += 25

        # Cultural familiarity with Carnatic music (25 points)
        cultural_familiarity = assessment.get('carnatic_familiarity', 0.3)
        total_score += cultural_familiarity * 25
        max_score += 25

        percentage = (total_score / max_score) * 100

        if percentage < 30:
            return SkillLevel.BEGINNER
        elif percentage < 50:
            return SkillLevel.NOVICE
        elif percentage < 70:
            return SkillLevel.INTERMEDIATE
        elif percentage < 85:
            return SkillLevel.ADVANCED
        else:
            return SkillLevel.EXPERT

    def _identify_learning_style(self, assessment: Dict[str, Any]) -> LearningStyle:
        """Identify primary learning style from assessment responses"""

        style_scores = {
            LearningStyle.VISUAL: 0,
            LearningStyle.AUDITORY: 0,
            LearningStyle.KINESTHETIC: 0,
            LearningStyle.ANALYTICAL: 0
        }

        # Learning preference questions
        preferences = assessment.get('learning_preferences', {})

        if preferences.get('prefers_visual_notation', False):
            style_scores[LearningStyle.VISUAL] += 2
        if preferences.get('learns_by_listening', False):
            style_scores[LearningStyle.AUDITORY] += 2
        if preferences.get('needs_physical_practice', False):
            style_scores[LearningStyle.KINESTHETIC] += 2
        if preferences.get('likes_theory_explanations', False):
            style_scores[LearningStyle.ANALYTICAL] += 2

        # Performance patterns
        if assessment.get('visual_memory_strong', False):
            style_scores[LearningStyle.VISUAL] += 1
        if assessment.get('audio_memory_strong', False):
            style_scores[LearningStyle.AUDITORY] += 1
        if assessment.get('motor_memory_strong', False):
            style_scores[LearningStyle.KINESTHETIC] += 1

        return max(style_scores, key=style_scores.get)

    def update_performance_metrics(
        self,
        user_id: int,
        session_data: Dict[str, Any]
    ) -> None:
        """Update user performance metrics after a practice session"""

        if user_id not in self.user_profiles:
            self.logger.warning(f"No profile found for user {user_id}")
            return

        profile = self.user_profiles[user_id]

        # Update accuracy history
        session_accuracy = session_data.get('accuracy', 0.0)
        profile.accuracy_history.append(session_accuracy)
        if len(profile.accuracy_history) > 50:  # Keep last 50 sessions
            profile.accuracy_history = profile.accuracy_history[-50:]

        # Update tempo progress
        session_tempo = session_data.get('tempo', 60)
        profile.tempo_progress.append(session_tempo)
        if len(profile.tempo_progress) > 50:
            profile.tempo_progress = profile.tempo_progress[-50:]

        # Update practice duration
        duration = session_data.get('duration_minutes', 0)
        profile.practice_duration.append(duration)
        if len(profile.practice_duration) > 50:
            profile.practice_duration = profile.practice_duration[-50:]

        # Update mistake patterns
        mistakes = session_data.get('mistakes', {})
        for mistake_type, count in mistakes.items():
            if mistake_type in profile.mistake_patterns:
                profile.mistake_patterns[mistake_type] += count
            else:
                profile.mistake_patterns[mistake_type] = count

        # Update engagement and retention
        self._update_engagement_score(profile, session_data)
        self._update_retention_rate(profile, session_data)

        # Reassess skill level
        self._reassess_skill_level(profile)

        # Update strengths and weaknesses
        self._analyze_strengths_weaknesses(profile, session_data)

        profile.last_updated = datetime.now()
        self.logger.info(f"Updated metrics for user {user_id}")

    def _update_engagement_score(self, profile: UserPerformanceMetrics, session_data: Dict[str, Any]) -> None:
        """Update engagement score based on session patterns"""

        current_engagement = profile.engagement_score

        # Factors that increase engagement
        duration = session_data.get('duration_minutes', 0)
        completed_exercises = session_data.get('completed_exercises', 0)
        voluntary_extra_practice = session_data.get('extra_practice', False)

        engagement_delta = 0

        # Duration factor (positive for 10-45 mins, negative for very short/long)
        if 10 <= duration <= 45:
            engagement_delta += 0.02
        elif duration < 5:
            engagement_delta -= 0.05
        elif duration > 60:
            engagement_delta -= 0.02

        # Completion factor
        if completed_exercises > 0:
            engagement_delta += 0.01 * min(completed_exercises, 5)

        # Voluntary practice bonus
        if voluntary_extra_practice:
            engagement_delta += 0.03

        # Apply smoothing (0.8 weight to current, 0.2 to new)
        profile.engagement_score = 0.8 * current_engagement + 0.2 * min(1.0, max(0.0, current_engagement + engagement_delta))

    def _update_retention_rate(self, profile: UserPerformanceMetrics, session_data: Dict[str, Any]) -> None:
        """Update retention rate based on performance consistency"""

        if len(profile.accuracy_history) < 3:
            return

        # Calculate consistency over recent sessions
        recent_accuracy = profile.accuracy_history[-5:]  # Last 5 sessions
        consistency = 1.0 - np.std(recent_accuracy)  # Lower std = higher consistency

        # Update retention rate with smoothing
        profile.retention_rate = 0.7 * profile.retention_rate + 0.3 * max(0.0, min(1.0, consistency))

    def _reassess_skill_level(self, profile: UserPerformanceMetrics) -> None:
        """Reassess user skill level based on recent performance"""

        if len(profile.accuracy_history) < 5:
            return

        recent_avg_accuracy = np.mean(profile.accuracy_history[-10:])
        consistency = 1.0 - np.std(profile.accuracy_history[-10:])

        current_thresholds = self.difficulty_thresholds[profile.skill_level]

        # Check if ready to advance
        if (recent_avg_accuracy >= current_thresholds['accuracy'] and
            consistency >= current_thresholds['consistency']):

            if profile.skill_level.value < SkillLevel.EXPERT.value:
                new_level = SkillLevel(profile.skill_level.value + 1)
                profile.skill_level = new_level
                self.logger.info(f"User {profile.user_id} advanced to {new_level}")

        # Check if needs to step back (struggling consistently)
        elif (recent_avg_accuracy < current_thresholds['accuracy'] * 0.8 and
              profile.skill_level.value > SkillLevel.BEGINNER.value):

            new_level = SkillLevel(profile.skill_level.value - 1)
            profile.skill_level = new_level
            self.logger.info(f"User {profile.user_id} adjusted to {new_level}")

    def _analyze_strengths_weaknesses(self, profile: UserPerformanceMetrics, session_data: Dict[str, Any]) -> None:
        """Analyze user's strengths and areas needing improvement"""

        strengths = []
        weaknesses = []

        # Analyze by exercise type performance
        exercise_performance = session_data.get('exercise_performance', {})

        for exercise_type, metrics in exercise_performance.items():
            accuracy = metrics.get('accuracy', 0)
            consistency = metrics.get('consistency', 0)

            combined_score = (accuracy + consistency) / 2

            if combined_score >= 0.8:
                if exercise_type not in strengths:
                    strengths.append(exercise_type)
            elif combined_score <= 0.6:
                if exercise_type not in weaknesses:
                    weaknesses.append(exercise_type)

        # Update profile
        profile.strength_areas = list(set(profile.strength_areas + strengths))
        profile.weakness_areas = list(set(profile.weakness_areas + weaknesses))

        # Remove weaknesses that have become strengths
        profile.weakness_areas = [w for w in profile.weakness_areas if w not in strengths]

    def get_next_recommendation(self, user_id: int) -> Optional[AdaptiveRecommendation]:
        """Generate next exercise recommendation based on user profile"""

        if user_id not in self.user_profiles:
            self.logger.warning(f"No profile found for user {user_id}")
            return None

        profile = self.user_profiles[user_id]

        # Determine focus areas
        focus_areas = self._determine_focus_areas(profile)

        # Select appropriate exercise type
        exercise_type = self._select_exercise_type(profile, focus_areas)

        # Calculate difficulty and tempo
        difficulty_level = self._calculate_difficulty(profile, exercise_type)
        suggested_tempo = self._suggest_tempo(profile, exercise_type)

        # Estimate duration
        estimated_duration = self._estimate_session_duration(profile)

        # Generate reasoning
        reasoning = self._generate_reasoning(profile, exercise_type, focus_areas)

        # Cultural context based on current level
        cultural_context = self._get_cultural_context(exercise_type, difficulty_level)

        recommendation = AdaptiveRecommendation(
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
            suggested_tempo=suggested_tempo,
            focus_areas=focus_areas,
            estimated_duration=estimated_duration,
            confidence_score=self._calculate_confidence(profile),
            reasoning=reasoning,
            cultural_context=cultural_context
        )

        self.logger.info(f"Generated recommendation for user {user_id}: {exercise_type} at level {difficulty_level}")

        return recommendation

    def _determine_focus_areas(self, profile: UserPerformanceMetrics) -> List[str]:
        """Determine what areas the user should focus on"""

        focus_areas = []

        # Priority 1: Address weaknesses
        if profile.weakness_areas:
            focus_areas.extend(profile.weakness_areas[:2])  # Top 2 weaknesses

        # Priority 2: Build on strengths for confidence
        if len(focus_areas) < 2 and profile.strength_areas:
            focus_areas.append(profile.strength_areas[0])  # Primary strength

        # Priority 3: Based on skill level progression
        skill_based_focus = {
            SkillLevel.BEGINNER: ['pitch_accuracy', 'basic_rhythm'],
            SkillLevel.NOVICE: ['swara_transitions', 'tempo_control'],
            SkillLevel.INTERMEDIATE: ['ornamentation', 'raga_understanding'],
            SkillLevel.ADVANCED: ['complex_patterns', 'improvisation'],
            SkillLevel.EXPERT: ['advanced_techniques', 'composition']
        }

        skill_areas = skill_based_focus.get(profile.skill_level, ['general_practice'])
        for area in skill_areas:
            if area not in focus_areas:
                focus_areas.append(area)
                if len(focus_areas) >= 3:  # Limit to 3 focus areas
                    break

        return focus_areas

    def _select_exercise_type(self, profile: UserPerformanceMetrics, focus_areas: List[str]) -> str:
        """Select the most appropriate exercise type"""

        # Exercise type priorities based on skill level
        skill_exercises = {
            SkillLevel.BEGINNER: ['sarali_varisai'],
            SkillLevel.NOVICE: ['sarali_varisai', 'janta_varisai'],
            SkillLevel.INTERMEDIATE: ['janta_varisai', 'alankaram'],
            SkillLevel.ADVANCED: ['alankaram', 'raga_exercises'],
            SkillLevel.EXPERT: ['advanced_alankaram', 'composition_practice']
        }

        available_exercises = skill_exercises.get(profile.skill_level, ['sarali_varisai'])

        # Consider focus areas and weaknesses
        if 'basic_rhythm' in focus_areas or 'pitch_accuracy' in focus_areas:
            return 'sarali_varisai'
        elif 'swara_transitions' in focus_areas:
            return 'janta_varisai'
        elif 'ornamentation' in focus_areas or 'raga_understanding' in focus_areas:
            return 'alankaram'

        # Default to most appropriate for skill level
        return available_exercises[0]

    def _calculate_difficulty(self, profile: UserPerformanceMetrics, exercise_type: str) -> int:
        """Calculate appropriate difficulty level"""

        base_difficulty = {
            SkillLevel.BEGINNER: 1,
            SkillLevel.NOVICE: 2,
            SkillLevel.INTERMEDIATE: 3,
            SkillLevel.ADVANCED: 4,
            SkillLevel.EXPERT: 5
        }

        difficulty = base_difficulty.get(profile.skill_level, 1)

        # Adjust based on recent performance
        if len(profile.accuracy_history) >= 3:
            recent_accuracy = np.mean(profile.accuracy_history[-3:])

            if recent_accuracy >= 0.9:
                difficulty += 1
            elif recent_accuracy <= 0.6:
                difficulty = max(1, difficulty - 1)

        # Ensure difficulty is within valid range for exercise type
        max_difficulty = max(self.exercise_complexity.get(exercise_type, {1: 1}).values())
        difficulty = min(difficulty, max_difficulty)

        return difficulty

    def _suggest_tempo(self, profile: UserPerformanceMetrics, exercise_type: str) -> int:
        """Suggest appropriate tempo based on user's progress"""

        base_tempo = {
            SkillLevel.BEGINNER: 60,
            SkillLevel.NOVICE: 70,
            SkillLevel.INTERMEDIATE: 80,
            SkillLevel.ADVANCED: 90,
            SkillLevel.EXPERT: 100
        }

        tempo = base_tempo.get(profile.skill_level, 60)

        # Adjust based on recent tempo progress
        if profile.tempo_progress:
            recent_tempo = np.mean(profile.tempo_progress[-5:])
            max_recent = max(profile.tempo_progress[-5:]) if len(profile.tempo_progress) >= 5 else tempo

            # If consistently performing well at higher tempos, suggest increase
            if len(profile.accuracy_history) >= 3 and np.mean(profile.accuracy_history[-3:]) >= 0.8:
                tempo = min(max_recent + 5, 120)  # Max 120 BPM
            else:
                tempo = max(int(recent_tempo * 0.9), 50)  # Reduce tempo if struggling

        return tempo

    def _estimate_session_duration(self, profile: UserPerformanceMetrics) -> int:
        """Estimate optimal session duration based on engagement and skill level"""

        base_duration = {
            SkillLevel.BEGINNER: 15,
            SkillLevel.NOVICE: 20,
            SkillLevel.INTERMEDIATE: 25,
            SkillLevel.ADVANCED: 30,
            SkillLevel.EXPERT: 35
        }

        duration = base_duration.get(profile.skill_level, 20)

        # Adjust based on engagement and recent practice patterns
        if profile.engagement_score >= 0.8:
            duration += 10
        elif profile.engagement_score <= 0.4:
            duration = max(10, duration - 10)

        # Consider recent practice duration patterns
        if profile.practice_duration:
            avg_recent_duration = np.mean(profile.practice_duration[-5:])
            # Adjust toward user's natural practice length
            duration = int(0.7 * duration + 0.3 * avg_recent_duration)

        return max(10, min(60, duration))  # Between 10-60 minutes

    def _generate_reasoning(self, profile: UserPerformanceMetrics, exercise_type: str, focus_areas: List[str]) -> str:
        """Generate human-readable reasoning for the recommendation"""

        skill_level_desc = profile.skill_level.name.lower()

        reasoning_parts = [
            f"Based on your {skill_level_desc} level proficiency"
        ]

        if profile.weakness_areas:
            reasoning_parts.append(f"focusing on improving {', '.join(profile.weakness_areas[:2])}")

        if len(profile.accuracy_history) >= 3:
            recent_accuracy = np.mean(profile.accuracy_history[-3:])
            if recent_accuracy >= 0.85:
                reasoning_parts.append("with challenging variations due to strong recent performance")
            elif recent_accuracy <= 0.65:
                reasoning_parts.append("with supportive pacing to build confidence")

        learning_style_msg = {
            LearningStyle.VISUAL: "including visual notation support",
            LearningStyle.AUDITORY: "emphasizing listening and repetition",
            LearningStyle.KINESTHETIC: "with hands-on practice focus",
            LearningStyle.ANALYTICAL: "with detailed theoretical explanations"
        }

        reasoning_parts.append(learning_style_msg.get(profile.learning_style, ""))

        return ", ".join(reasoning_parts) + "."

    def _get_cultural_context(self, exercise_type: str, difficulty_level: int) -> Optional[str]:
        """Provide cultural context for the recommended exercise"""

        cultural_contexts = {
            'sarali_varisai': {
                1: "Begin with the foundational practice that every Carnatic musician learns - the simple ascent and descent of swaras.",
                2: "Explore the beauty of swara sequences that form the backbone of Carnatic music tradition.",
                3: "Practice with the devotion and precision that characterizes traditional Carnatic pedagogy."
            },
            'janta_varisai': {
                1: "Experience the doubled swara patterns that develop clarity in Carnatic pronunciation.",
                2: "Master the transitions that create the flowing nature of Carnatic melody.",
                3: "Embrace the rhythmic emphasis that brings life to each swara combination."
            },
            'alankaram': {
                1: "Begin exploring the ornamental patterns that beautify Carnatic music.",
                2: "Develop the aesthetic sense that distinguishes accomplished Carnatic musicians.",
                3: "Practice the sophisticated embellishments that express the raga's character."
            }
        }

        return cultural_contexts.get(exercise_type, {}).get(difficulty_level)

    def _calculate_confidence(self, profile: UserPerformanceMetrics) -> float:
        """Calculate confidence score for the recommendation"""

        confidence = 0.7  # Base confidence

        # Increase confidence with more data
        data_points = len(profile.accuracy_history)
        if data_points >= 10:
            confidence += 0.2
        elif data_points >= 5:
            confidence += 0.1

        # Increase confidence with consistent performance
        if len(profile.accuracy_history) >= 3:
            consistency = 1.0 - np.std(profile.accuracy_history[-5:])
            confidence += 0.1 * consistency

        # Adjust for engagement
        confidence += 0.1 * profile.engagement_score

        return min(1.0, confidence)

    def get_learning_analytics(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate comprehensive learning analytics for a user"""

        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]

        # Calculate trend analysis
        accuracy_trend = self._calculate_trend(profile.accuracy_history)
        tempo_trend = self._calculate_trend(profile.tempo_progress)
        duration_trend = self._calculate_trend(profile.practice_duration)

        # Performance insights
        insights = self._generate_performance_insights(profile)

        analytics = {
            'user_id': user_id,
            'current_skill_level': profile.skill_level.name,
            'learning_style': profile.learning_style.name,
            'engagement_score': profile.engagement_score,
            'retention_rate': profile.retention_rate,
            'performance_trends': {
                'accuracy': accuracy_trend,
                'tempo': tempo_trend,
                'practice_duration': duration_trend
            },
            'strengths': profile.strength_areas,
            'areas_for_improvement': profile.weakness_areas,
            'common_mistakes': dict(sorted(profile.mistake_patterns.items(),
                                         key=lambda x: x[1], reverse=True)[:5]),
            'insights': insights,
            'total_sessions': len(profile.accuracy_history),
            'average_accuracy': np.mean(profile.accuracy_history) if profile.accuracy_history else 0,
            'last_updated': profile.last_updated.isoformat()
        }

        return analytics

    def _calculate_trend(self, data: List[float]) -> Dict[str, Any]:
        """Calculate trend analysis for a metric"""

        if len(data) < 2:
            return {'direction': 'insufficient_data', 'magnitude': 0}

        # Simple linear trend calculation
        x = np.arange(len(data))
        y = np.array(data)

        slope = np.corrcoef(x, y)[0, 1] if len(data) > 2 else (y[-1] - y[0]) / len(data)

        direction = 'improving' if slope > 0.1 else 'declining' if slope < -0.1 else 'stable'
        magnitude = abs(slope)

        return {
            'direction': direction,
            'magnitude': magnitude,
            'recent_average': np.mean(data[-5:]) if len(data) >= 5 else np.mean(data),
            'overall_average': np.mean(data)
        }

    def _generate_performance_insights(self, profile: UserPerformanceMetrics) -> List[str]:
        """Generate actionable insights based on user performance"""

        insights = []

        # Engagement insights
        if profile.engagement_score >= 0.8:
            insights.append("High engagement - consider introducing more challenging material")
        elif profile.engagement_score <= 0.4:
            insights.append("Low engagement detected - recommend shorter sessions or varied content")

        # Consistency insights
        if profile.accuracy_history and len(profile.accuracy_history) >= 5:
            consistency = 1.0 - np.std(profile.accuracy_history[-10:])
            if consistency >= 0.8:
                insights.append("Excellent consistency - ready for skill level advancement")
            elif consistency <= 0.5:
                insights.append("Inconsistent performance - focus on foundational practice")

        # Practice pattern insights
        if profile.practice_duration:
            avg_duration = np.mean(profile.practice_duration)
            if avg_duration < 15:
                insights.append("Consider longer practice sessions for better retention")
            elif avg_duration > 45:
                insights.append("Long practice sessions detected - ensure adequate breaks")

        # Learning style insights
        style_recommendations = {
            LearningStyle.VISUAL: "Incorporate more visual notation and pattern recognition",
            LearningStyle.AUDITORY: "Emphasize listening exercises and repetitive practice",
            LearningStyle.KINESTHETIC: "Include more interactive and hands-on practice elements",
            LearningStyle.ANALYTICAL: "Provide detailed theoretical explanations and structure"
        }

        insights.append(style_recommendations[profile.learning_style])

        return insights

    def export_user_data(self, user_id: int) -> Optional[str]:
        """Export user profile data as JSON"""

        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]

        # Convert to serializable format
        data = {
            'user_id': profile.user_id,
            'skill_level': profile.skill_level.value,
            'learning_style': profile.learning_style.value,
            'accuracy_history': profile.accuracy_history,
            'tempo_progress': profile.tempo_progress,
            'practice_duration': profile.practice_duration,
            'mistake_patterns': profile.mistake_patterns,
            'strength_areas': profile.strength_areas,
            'weakness_areas': profile.weakness_areas,
            'engagement_score': profile.engagement_score,
            'retention_rate': profile.retention_rate,
            'last_updated': profile.last_updated.isoformat()
        }

        return json.dumps(data, indent=2)