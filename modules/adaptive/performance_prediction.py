"""
Performance Prediction System for Carnatic Music Platform

Advanced ML models to predict user performance, identify learning difficulties,
and provide proactive intervention recommendations for optimal learning outcomes.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math
from collections import deque
import logging

class PredictionType(Enum):
    SUCCESS_PROBABILITY = "success_probability"
    COMPLETION_TIME = "completion_time"
    DIFFICULTY_RATING = "difficulty_rating"
    RETENTION_PROBABILITY = "retention_probability"
    ENGAGEMENT_PREDICTION = "engagement_prediction"

class InterventionType(Enum):
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    PACING_MODIFICATION = "pacing_modification"
    CONTENT_DIVERSIFICATION = "content_diversification"
    MOTIVATIONAL_SUPPORT = "motivational_support"
    TECHNIQUE_REINFORCEMENT = "technique_reinforcement"
    CULTURAL_CONTEXT_ENHANCEMENT = "cultural_context_enhancement"

class RiskLevel(Enum):
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class PerformanceFeatures:
    user_id: int
    session_count: int
    avg_accuracy: float
    accuracy_trend: float  # Linear slope of recent accuracy
    consistency_score: float  # 1 - std dev of recent accuracy
    practice_frequency: float  # Sessions per week
    session_duration_avg: float  # Average minutes per session
    tempo_progression: float  # Rate of tempo increase
    mistake_frequency: Dict[str, int]  # Common mistake patterns
    engagement_indicators: Dict[str, float]  # Time ratios, completion rates
    skill_area_strengths: List[str]
    skill_area_weaknesses: List[str]
    learning_style_indicators: Dict[str, float]
    cultural_engagement: float
    last_session_timestamp: datetime

@dataclass
class PredictionResult:
    prediction_type: PredictionType
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    contributing_factors: Dict[str, float]
    risk_factors: List[str]
    recommendation_priority: int  # 1-5 scale

@dataclass
class InterventionRecommendation:
    intervention_type: InterventionType
    description: str
    rationale: str
    implementation_steps: List[str]
    expected_outcome: str
    urgency: RiskLevel
    estimated_effectiveness: float
    monitoring_metrics: List[str]

class PerformancePredictionEngine:
    """
    Advanced performance prediction system using ensemble machine learning
    approaches to predict user success, identify at-risk learners, and
    recommend proactive interventions for optimal learning outcomes.
    """

    def __init__(self):
        self.user_features: Dict[int, PerformanceFeatures] = {}
        self.historical_predictions: Dict[int, List[PredictionResult]] = {}

        # Model parameters (in real implementation, these would be trained)
        self.model_weights = {
            'accuracy_weight': 0.25,
            'consistency_weight': 0.20,
            'engagement_weight': 0.20,
            'practice_frequency_weight': 0.15,
            'progression_weight': 0.10,
            'cultural_weight': 0.10
        }

        # Thresholds for risk assessment
        self.risk_thresholds = {
            'accuracy_decline': -0.15,  # 15% decline over 5 sessions
            'consistency_low': 0.6,     # Below 60% consistency
            'engagement_drop': 0.4,     # Below 40% engagement
            'absence_days': 7,          # No practice for 7 days
            'mistake_spike': 3.0        # 3x increase in mistake frequency
        }

        self.logger = logging.getLogger(__name__)

    def extract_features(self, user_id: int, session_data: List[Dict[str, Any]]) -> PerformanceFeatures:
        """Extract comprehensive performance features from user session data"""

        if not session_data:
            raise ValueError("No session data provided")

        # Sort sessions by timestamp
        sessions = sorted(session_data, key=lambda x: x['timestamp'])
        recent_sessions = sessions[-10:]  # Last 10 sessions for trend analysis

        # Basic statistics
        session_count = len(sessions)
        accuracies = [s['accuracy'] for s in sessions]
        avg_accuracy = np.mean(accuracies)

        # Accuracy trend (linear regression slope)
        if len(recent_sessions) >= 3:
            x = np.arange(len(recent_sessions))
            y = [s['accuracy'] for s in recent_sessions]
            accuracy_trend = np.polyfit(x, y, 1)[0]  # Slope of linear fit
        else:
            accuracy_trend = 0.0

        # Consistency score
        recent_accuracies = [s['accuracy'] for s in recent_sessions]
        consistency_score = 1.0 - np.std(recent_accuracies) if recent_accuracies else 0.0

        # Practice frequency (sessions per week)
        if len(sessions) >= 2:
            time_span = (sessions[-1]['timestamp'] - sessions[0]['timestamp']).days
            practice_frequency = (len(sessions) / max(time_span, 1)) * 7  # Sessions per week
        else:
            practice_frequency = 1.0

        # Session duration analysis
        durations = [s.get('duration_minutes', 20) for s in sessions]
        session_duration_avg = np.mean(durations)

        # Tempo progression analysis
        tempos = [s.get('tempo', 60) for s in sessions if 'tempo' in s]
        if len(tempos) >= 2:
            tempo_progression = (tempos[-1] - tempos[0]) / len(tempos)
        else:
            tempo_progression = 0.0

        # Mistake pattern analysis
        mistake_frequency = {}
        for session in sessions:
            mistakes = session.get('mistakes', {})
            for mistake_type, count in mistakes.items():
                mistake_frequency[mistake_type] = mistake_frequency.get(mistake_type, 0) + count

        # Engagement indicators
        engagement_indicators = self._calculate_engagement_indicators(sessions)

        # Skill area analysis
        skill_strengths, skill_weaknesses = self._analyze_skill_areas(sessions)

        # Learning style indicators
        learning_style_indicators = self._analyze_learning_style(sessions)

        # Cultural engagement
        cultural_engagement = self._calculate_cultural_engagement(sessions)

        features = PerformanceFeatures(
            user_id=user_id,
            session_count=session_count,
            avg_accuracy=avg_accuracy,
            accuracy_trend=accuracy_trend,
            consistency_score=consistency_score,
            practice_frequency=practice_frequency,
            session_duration_avg=session_duration_avg,
            tempo_progression=tempo_progression,
            mistake_frequency=mistake_frequency,
            engagement_indicators=engagement_indicators,
            skill_area_strengths=skill_strengths,
            skill_area_weaknesses=skill_weaknesses,
            learning_style_indicators=learning_style_indicators,
            cultural_engagement=cultural_engagement,
            last_session_timestamp=sessions[-1]['timestamp']
        )

        self.user_features[user_id] = features
        return features

    def _calculate_engagement_indicators(self, sessions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate various engagement indicators from session data"""

        indicators = {
            'completion_rate': 0.0,
            'time_efficiency': 0.0,
            'voluntary_practice': 0.0,
            'exploration_rate': 0.0
        }

        if not sessions:
            return indicators

        # Completion rate
        completed_sessions = sum(1 for s in sessions if s.get('completed', False))
        indicators['completion_rate'] = completed_sessions / len(sessions)

        # Time efficiency (actual vs expected duration)
        time_ratios = []
        for session in sessions:
            actual_time = session.get('duration_minutes', 0)
            expected_time = session.get('expected_duration', 20)
            if expected_time > 0:
                time_ratios.append(min(actual_time / expected_time, 2.0))  # Cap at 200%

        indicators['time_efficiency'] = np.mean(time_ratios) if time_ratios else 0.0

        # Voluntary practice (sessions beyond required minimum)
        weekly_sessions = {}
        for session in sessions:
            week_key = session['timestamp'].strftime('%Y-%W')
            weekly_sessions[week_key] = weekly_sessions.get(week_key, 0) + 1

        extra_sessions = sum(max(0, count - 3) for count in weekly_sessions.values())  # >3 per week
        indicators['voluntary_practice'] = extra_sessions / len(sessions)

        # Exploration rate (variety in content types)
        content_types = set()
        for session in sessions:
            content_types.add(session.get('content_type', 'unknown'))

        indicators['exploration_rate'] = len(content_types) / max(len(sessions), 1)

        return indicators

    def _analyze_skill_areas(self, sessions: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Analyze skill area performance to identify strengths and weaknesses"""

        skill_performance = {}

        for session in sessions:
            exercise_performance = session.get('exercise_performance', {})
            for skill_area, metrics in exercise_performance.items():
                if skill_area not in skill_performance:
                    skill_performance[skill_area] = []
                skill_performance[skill_area].append(metrics.get('accuracy', 0))

        # Calculate average performance for each skill area
        skill_averages = {}
        for skill_area, performances in skill_performance.items():
            skill_averages[skill_area] = np.mean(performances)

        # Identify strengths (top 30%) and weaknesses (bottom 30%)
        if not skill_averages:
            return [], []

        sorted_skills = sorted(skill_averages.items(), key=lambda x: x[1], reverse=True)
        num_skills = len(sorted_skills)

        strengths = [skill for skill, _ in sorted_skills[:max(1, num_skills // 3)]]
        weaknesses = [skill for skill, _ in sorted_skills[-max(1, num_skills // 3):]]

        return strengths, weaknesses

    def _analyze_learning_style(self, sessions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze learning style indicators from session behavior"""

        indicators = {
            'visual': 0.0,
            'auditory': 0.0,
            'kinesthetic': 0.0,
            'analytical': 0.0
        }

        if not sessions:
            return indicators

        total_sessions = len(sessions)

        # Visual learning indicators
        visual_sessions = sum(1 for s in sessions if s.get('used_notation', False))
        indicators['visual'] = visual_sessions / total_sessions

        # Auditory learning indicators
        audio_sessions = sum(1 for s in sessions if s.get('audio_focus', False))
        indicators['auditory'] = audio_sessions / total_sessions

        # Kinesthetic learning indicators
        interactive_sessions = sum(1 for s in sessions if s.get('interactive_practice', False))
        indicators['kinesthetic'] = interactive_sessions / total_sessions

        # Analytical learning indicators
        theory_sessions = sum(1 for s in sessions if s.get('theory_content', False))
        indicators['analytical'] = theory_sessions / total_sessions

        return indicators

    def _calculate_cultural_engagement(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate user's engagement with cultural content"""

        if not sessions:
            return 0.0

        cultural_sessions = sum(1 for s in sessions if s.get('cultural_content', False))
        cultural_engagement = cultural_sessions / len(sessions)

        # Boost for cultural content completion
        cultural_completions = sum(1 for s in sessions
                                 if s.get('cultural_content', False) and s.get('completed', False))

        if cultural_sessions > 0:
            completion_boost = cultural_completions / cultural_sessions
            cultural_engagement = (cultural_engagement + completion_boost) / 2

        return cultural_engagement

    def predict_performance(
        self,
        user_id: int,
        prediction_type: PredictionType,
        context: Optional[Dict[str, Any]] = None
    ) -> PredictionResult:
        """Generate performance prediction for a user"""

        if user_id not in self.user_features:
            raise ValueError(f"No features available for user {user_id}")

        features = self.user_features[user_id]

        if prediction_type == PredictionType.SUCCESS_PROBABILITY:
            return self._predict_success_probability(features, context)
        elif prediction_type == PredictionType.COMPLETION_TIME:
            return self._predict_completion_time(features, context)
        elif prediction_type == PredictionType.DIFFICULTY_RATING:
            return self._predict_difficulty_rating(features, context)
        elif prediction_type == PredictionType.RETENTION_PROBABILITY:
            return self._predict_retention_probability(features, context)
        elif prediction_type == PredictionType.ENGAGEMENT_PREDICTION:
            return self._predict_engagement(features, context)
        else:
            raise ValueError(f"Unsupported prediction type: {prediction_type}")

    def _predict_success_probability(
        self,
        features: PerformanceFeatures,
        context: Optional[Dict[str, Any]]
    ) -> PredictionResult:
        """Predict probability of success for next learning activity"""

        # Base probability from historical accuracy
        base_prob = features.avg_accuracy

        # Adjust for recent trend
        trend_adjustment = features.accuracy_trend * 2  # Amplify trend impact
        base_prob += trend_adjustment

        # Adjust for consistency
        consistency_adjustment = (features.consistency_score - 0.7) * 0.3
        base_prob += consistency_adjustment

        # Adjust for practice frequency
        frequency_factor = min(features.practice_frequency / 4, 1.0)  # Optimal at 4 sessions/week
        frequency_adjustment = (frequency_factor - 0.5) * 0.2
        base_prob += frequency_adjustment

        # Adjust for engagement
        engagement_score = np.mean(list(features.engagement_indicators.values()))
        engagement_adjustment = (engagement_score - 0.5) * 0.2
        base_prob += engagement_adjustment

        # Context-specific adjustments
        if context:
            content_difficulty = context.get('content_difficulty', 3)
            difficulty_adjustment = (3 - content_difficulty) * 0.1  # Easier content = higher success
            base_prob += difficulty_adjustment

            # User strength/weakness match
            content_tags = context.get('content_tags', [])
            strength_match = any(tag in features.skill_area_strengths for tag in content_tags)
            weakness_match = any(tag in features.skill_area_weaknesses for tag in content_tags)

            if strength_match:
                base_prob += 0.1
            elif weakness_match:
                base_prob -= 0.1

        # Ensure probability is in valid range
        predicted_prob = max(0.05, min(0.95, base_prob))

        # Calculate confidence based on data amount and consistency
        data_confidence = min(features.session_count / 20, 1.0)
        trend_confidence = 1.0 - abs(features.accuracy_trend)  # Lower trend = higher confidence
        confidence = (data_confidence + trend_confidence) / 2

        # Confidence interval
        ci_width = 0.3 * (1 - confidence)
        confidence_interval = (
            max(0.0, predicted_prob - ci_width),
            min(1.0, predicted_prob + ci_width)
        )

        # Contributing factors
        contributing_factors = {
            'historical_accuracy': features.avg_accuracy,
            'recent_trend': features.accuracy_trend,
            'consistency': features.consistency_score,
            'practice_frequency': frequency_factor,
            'engagement': engagement_score
        }

        # Risk factors
        risk_factors = []
        if features.accuracy_trend < self.risk_thresholds['accuracy_decline']:
            risk_factors.append("declining_accuracy_trend")
        if features.consistency_score < self.risk_thresholds['consistency_low']:
            risk_factors.append("low_consistency")
        if engagement_score < self.risk_thresholds['engagement_drop']:
            risk_factors.append("low_engagement")

        # Recommendation priority
        priority = 1
        if risk_factors:
            priority = min(5, len(risk_factors) + 2)

        return PredictionResult(
            prediction_type=PredictionType.SUCCESS_PROBABILITY,
            predicted_value=predicted_prob,
            confidence_interval=confidence_interval,
            confidence_score=confidence,
            contributing_factors=contributing_factors,
            risk_factors=risk_factors,
            recommendation_priority=priority
        )

    def _predict_completion_time(
        self,
        features: PerformanceFeatures,
        context: Optional[Dict[str, Any]]
    ) -> PredictionResult:
        """Predict expected completion time for learning content"""

        # Base time from user's average session duration
        base_time = features.session_duration_avg

        # Adjust for user's learning pace
        pace_factor = 1.0
        if features.avg_accuracy > 0.8:
            pace_factor = 0.8  # Fast learners
        elif features.avg_accuracy < 0.6:
            pace_factor = 1.3  # Slower pace for struggling learners

        # Adjust for content difficulty
        if context:
            content_difficulty = context.get('content_difficulty', 3)
            difficulty_factor = 0.7 + (content_difficulty - 1) * 0.1  # 0.7x to 1.1x
            pace_factor *= difficulty_factor

            # Expected base duration from content
            expected_duration = context.get('expected_duration', base_time)
            base_time = expected_duration

        predicted_time = base_time * pace_factor

        # Confidence based on session count and consistency
        confidence = min(features.session_count / 15, 1.0) * features.consistency_score

        # Confidence interval
        ci_width = predicted_time * 0.4 * (1 - confidence)
        confidence_interval = (
            max(5.0, predicted_time - ci_width),
            predicted_time + ci_width
        )

        contributing_factors = {
            'avg_session_duration': features.session_duration_avg,
            'learning_pace': pace_factor,
            'consistency': features.consistency_score
        }

        risk_factors = []
        if predicted_time > base_time * 1.5:
            risk_factors.append("extended_completion_time")

        return PredictionResult(
            prediction_type=PredictionType.COMPLETION_TIME,
            predicted_value=predicted_time,
            confidence_interval=confidence_interval,
            confidence_score=confidence,
            contributing_factors=contributing_factors,
            risk_factors=risk_factors,
            recommendation_priority=2 if risk_factors else 1
        )

    def _predict_retention_probability(
        self,
        features: PerformanceFeatures,
        context: Optional[Dict[str, Any]]
    ) -> PredictionResult:
        """Predict probability of user continuing practice (retention)"""

        # Days since last session
        days_since_practice = (datetime.now() - features.last_session_timestamp).days

        # Base retention score
        retention_score = 0.8  # Default high retention

        # Adjust for recency
        if days_since_practice <= 3:
            recency_factor = 1.0
        elif days_since_practice <= 7:
            recency_factor = 0.8
        elif days_since_practice <= 14:
            recency_factor = 0.6
        else:
            recency_factor = 0.3

        retention_score *= recency_factor

        # Adjust for engagement
        engagement_score = np.mean(list(features.engagement_indicators.values()))
        retention_score *= (0.5 + 0.5 * engagement_score)

        # Adjust for practice frequency
        frequency_factor = min(features.practice_frequency / 3, 1.0)
        retention_score *= (0.7 + 0.3 * frequency_factor)

        # Adjust for success experience
        success_factor = features.avg_accuracy
        retention_score *= (0.6 + 0.4 * success_factor)

        # Cultural engagement boost
        retention_score += 0.1 * features.cultural_engagement

        # Ensure valid range
        predicted_retention = max(0.1, min(0.95, retention_score))

        confidence = min(features.session_count / 10, 1.0) * features.consistency_score

        ci_width = 0.25 * (1 - confidence)
        confidence_interval = (
            max(0.0, predicted_retention - ci_width),
            min(1.0, predicted_retention + ci_width)
        )

        contributing_factors = {
            'days_since_practice': days_since_practice,
            'engagement_score': engagement_score,
            'practice_frequency': features.practice_frequency,
            'success_rate': features.avg_accuracy,
            'cultural_engagement': features.cultural_engagement
        }

        risk_factors = []
        if days_since_practice >= self.risk_thresholds['absence_days']:
            risk_factors.append("extended_absence")
        if engagement_score < self.risk_thresholds['engagement_drop']:
            risk_factors.append("low_engagement")
        if features.avg_accuracy < 0.5:
            risk_factors.append("poor_success_rate")

        priority = 5 if days_since_practice > 14 else (3 if risk_factors else 1)

        return PredictionResult(
            prediction_type=PredictionType.RETENTION_PROBABILITY,
            predicted_value=predicted_retention,
            confidence_interval=confidence_interval,
            confidence_score=confidence,
            contributing_factors=contributing_factors,
            risk_factors=risk_factors,
            recommendation_priority=priority
        )

    def generate_intervention_recommendations(
        self,
        user_id: int,
        prediction_results: List[PredictionResult]
    ) -> List[InterventionRecommendation]:
        """Generate proactive intervention recommendations based on predictions"""

        if user_id not in self.user_features:
            return []

        features = self.user_features[user_id]
        recommendations = []

        # Analyze prediction results for risk patterns
        high_risk_predictions = [p for p in prediction_results if p.recommendation_priority >= 4]
        all_risk_factors = set()
        for pred in prediction_results:
            all_risk_factors.update(pred.risk_factors)

        # Generate specific interventions
        if "declining_accuracy_trend" in all_risk_factors:
            recommendations.append(self._create_difficulty_adjustment_intervention(features))

        if "low_engagement" in all_risk_factors:
            recommendations.append(self._create_engagement_intervention(features))

        if "extended_absence" in all_risk_factors:
            recommendations.append(self._create_retention_intervention(features))

        if "low_consistency" in all_risk_factors:
            recommendations.append(self._create_consistency_intervention(features))

        if features.skill_area_weaknesses:
            recommendations.append(self._create_skill_reinforcement_intervention(features))

        if features.cultural_engagement < 0.3:
            recommendations.append(self._create_cultural_engagement_intervention(features))

        # Sort by urgency and effectiveness
        recommendations.sort(key=lambda x: (x.urgency.value, -x.estimated_effectiveness))

        return recommendations

    def _create_difficulty_adjustment_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for difficulty adjustment"""

        return InterventionRecommendation(
            intervention_type=InterventionType.DIFFICULTY_ADJUSTMENT,
            description="Adjust content difficulty to match current skill level",
            rationale=f"User shows declining accuracy trend ({features.accuracy_trend:.3f}), indicating content may be too challenging",
            implementation_steps=[
                "Reduce content difficulty by one level",
                "Focus on foundational skills review",
                "Gradually increase difficulty as confidence rebuilds",
                "Monitor accuracy improvement over next 5 sessions"
            ],
            expected_outcome="Improved success rate and renewed confidence within 2 weeks",
            urgency=RiskLevel.HIGH,
            estimated_effectiveness=0.8,
            monitoring_metrics=["accuracy_trend", "consistency_score", "engagement_indicators"]
        )

    def _create_engagement_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for improving engagement"""

        engagement_score = np.mean(list(features.engagement_indicators.values()))

        return InterventionRecommendation(
            intervention_type=InterventionType.CONTENT_DIVERSIFICATION,
            description="Diversify content to reignite interest and engagement",
            rationale=f"Low engagement detected ({engagement_score:.2f}), user needs variety and motivation",
            implementation_steps=[
                "Introduce new content types (cultural stories, compositions)",
                "Add interactive elements and gamification",
                "Provide choice in learning path",
                "Incorporate user's learning style preferences",
                "Set achievable short-term goals"
            ],
            expected_outcome="Increased engagement and voluntary practice within 1 week",
            urgency=RiskLevel.MODERATE,
            estimated_effectiveness=0.75,
            monitoring_metrics=["completion_rate", "voluntary_practice", "session_duration"]
        )

    def _create_retention_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for retention at risk"""

        days_absent = (datetime.now() - features.last_session_timestamp).days

        return InterventionRecommendation(
            intervention_type=InterventionType.MOTIVATIONAL_SUPPORT,
            description="Proactive outreach and motivational support",
            rationale=f"User absent for {days_absent} days, at risk of dropout",
            implementation_steps=[
                "Send personalized encouragement message",
                "Offer flexible shorter sessions (10-15 minutes)",
                "Highlight progress made so far",
                "Provide easy 'comeback' exercises",
                "Schedule check-in after 3 days"
            ],
            expected_outcome="User returns to regular practice within 1 week",
            urgency=RiskLevel.CRITICAL,
            estimated_effectiveness=0.6,
            monitoring_metrics=["days_since_practice", "session_frequency", "engagement_score"]
        )

    def _create_consistency_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for improving consistency"""

        return InterventionRecommendation(
            intervention_type=InterventionType.PACING_MODIFICATION,
            description="Improve practice consistency through pacing adjustments",
            rationale=f"Low consistency score ({features.consistency_score:.2f}), need structured practice routine",
            implementation_steps=[
                "Establish regular practice schedule",
                "Break sessions into smaller, focused segments",
                "Implement warm-up routines",
                "Provide consistent feedback mechanisms",
                "Track daily progress with visual indicators"
            ],
            expected_outcome="Improved consistency score within 3 weeks",
            urgency=RiskLevel.MODERATE,
            estimated_effectiveness=0.7,
            monitoring_metrics=["consistency_score", "practice_frequency", "session_regularity"]
        )

    def _create_skill_reinforcement_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for skill area reinforcement"""

        weakness_areas = ", ".join(features.skill_area_weaknesses[:3])

        return InterventionRecommendation(
            intervention_type=InterventionType.TECHNIQUE_REINFORCEMENT,
            description="Targeted practice for identified weakness areas",
            rationale=f"Specific skill gaps identified in: {weakness_areas}",
            implementation_steps=[
                f"Create focused exercises for {weakness_areas}",
                "Provide additional instructional content",
                "Implement spaced repetition for weak areas",
                "Offer technique-specific feedback",
                "Balance weakness work with strength reinforcement"
            ],
            expected_outcome="Measurable improvement in weak skill areas within 4 weeks",
            urgency=RiskLevel.MODERATE,
            estimated_effectiveness=0.8,
            monitoring_metrics=["skill_area_performance", "mistake_frequency", "technique_scores"]
        )

    def _create_cultural_engagement_intervention(self, features: PerformanceFeatures) -> InterventionRecommendation:
        """Create intervention for cultural engagement"""

        return InterventionRecommendation(
            intervention_type=InterventionType.CULTURAL_CONTEXT_ENHANCEMENT,
            description="Enhance cultural connection to deepen engagement",
            rationale=f"Low cultural engagement ({features.cultural_engagement:.2f}), missing cultural context",
            implementation_steps=[
                "Introduce cultural stories behind ragas",
                "Provide historical context for exercises",
                "Add traditional performance videos",
                "Include cultural significance explanations",
                "Connect practice to festival traditions"
            ],
            expected_outcome="Increased cultural interest and deeper musical understanding",
            urgency=RiskLevel.LOW,
            estimated_effectiveness=0.6,
            monitoring_metrics=["cultural_engagement", "cultural_content_completion", "overall_engagement"]
        )

    def update_prediction_accuracy(
        self,
        user_id: int,
        prediction_result: PredictionResult,
        actual_outcome: float
    ) -> None:
        """Update prediction accuracy tracking for model improvement"""

        if user_id not in self.historical_predictions:
            self.historical_predictions[user_id] = []

        # Calculate prediction error
        prediction_error = abs(prediction_result.predicted_value - actual_outcome)

        # Store for model improvement
        accuracy_record = {
            'prediction_type': prediction_result.prediction_type,
            'predicted': prediction_result.predicted_value,
            'actual': actual_outcome,
            'error': prediction_error,
            'confidence': prediction_result.confidence_score,
            'timestamp': datetime.now()
        }

        self.historical_predictions[user_id].append(accuracy_record)

        # Log significant prediction errors
        if prediction_error > 0.3:
            self.logger.warning(
                f"High prediction error for user {user_id}: "
                f"predicted {prediction_result.predicted_value:.3f}, "
                f"actual {actual_outcome:.3f}"
            )

    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get overall model performance metrics"""

        all_predictions = []
        for user_predictions in self.historical_predictions.values():
            all_predictions.extend(user_predictions)

        if not all_predictions:
            return {"status": "insufficient_data"}

        # Calculate metrics by prediction type
        metrics_by_type = {}
        for pred_type in PredictionType:
            type_predictions = [p for p in all_predictions if p['prediction_type'] == pred_type]

            if type_predictions:
                errors = [p['error'] for p in type_predictions]
                confidences = [p['confidence'] for p in type_predictions]

                metrics_by_type[pred_type.value] = {
                    'mean_absolute_error': np.mean(errors),
                    'rmse': np.sqrt(np.mean([e**2 for e in errors])),
                    'prediction_count': len(type_predictions),
                    'avg_confidence': np.mean(confidences)
                }

        # Overall metrics
        all_errors = [p['error'] for p in all_predictions]
        overall_metrics = {
            'overall_mae': np.mean(all_errors),
            'overall_rmse': np.sqrt(np.mean([e**2 for e in all_errors])),
            'total_predictions': len(all_predictions),
            'accuracy_within_10pct': sum(1 for e in all_errors if e <= 0.1) / len(all_errors)
        }

        return {
            'overall_metrics': overall_metrics,
            'metrics_by_type': metrics_by_type,
            'last_updated': datetime.now().isoformat()
        }