"""
Advanced Analytics and Progress Tracking Dashboard

Comprehensive analytics system providing detailed insights into learning
progress, performance trends, and personalized recommendations.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import math

from ..database import get_db_session
from ..models import User, Progress, Exercise, Recording, UserAchievement

class AnalyticsPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class MetricType(Enum):
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    PRACTICE_TIME = "practice_time"
    STREAK = "streak"
    IMPROVEMENT = "improvement"
    DIFFICULTY = "difficulty"

@dataclass
class PerformanceMetric:
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # "improving", "declining", "stable"
    confidence: float
    recommendations: List[str]

@dataclass
class LearningInsight:
    category: str
    title: str
    description: str
    severity: str  # "info", "warning", "critical", "positive"
    data_points: Dict[str, Any]
    action_items: List[str]
    priority: int

@dataclass
class PracticePattern:
    pattern_type: str
    frequency: str
    preferred_times: List[str]
    session_duration_avg: int
    consistency_score: float
    recommendations: List[str]

@dataclass
class SwararAnalysis:
    swara: str
    accuracy_trend: List[float]
    practice_frequency: int
    difficulty_score: float
    mastery_level: str  # "beginner", "intermediate", "advanced", "mastered"
    common_issues: List[str]
    improvement_suggestions: List[str]

@dataclass
class ProgressPrediction:
    target_skill: str
    current_level: float
    predicted_timeline: int  # days to achieve target
    confidence: float
    milestones: List[Dict[str, Any]]
    factors_affecting: List[str]

class AdvancedAnalytics:
    """
    Advanced analytics engine providing deep insights into
    user learning patterns and performance.
    """

    def __init__(self):
        self.analysis_cache = {}
        self.cache_duration = timedelta(hours=6)

    async def generate_user_dashboard(self, user_id: int, period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY) -> Dict[str, Any]:
        """Generate comprehensive analytics dashboard for user"""
        try:
            # Check cache first
            cache_key = f"dashboard_{user_id}_{period.value}"
            if self._is_cache_valid(cache_key):
                return self.analysis_cache[cache_key]['data']

            # Generate all analytics components
            dashboard_data = {
                'user_id': user_id,
                'period': period.value,
                'generated_at': datetime.now().isoformat(),
                'performance_metrics': await self._analyze_performance_metrics(user_id, period),
                'learning_insights': await self._generate_learning_insights(user_id, period),
                'practice_patterns': await self._analyze_practice_patterns(user_id, period),
                'swara_analysis': await self._analyze_swara_performance(user_id, period),
                'progress_predictions': await self._generate_progress_predictions(user_id),
                'streak_analysis': await self._analyze_streaks(user_id, period),
                'accuracy_trends': await self._analyze_accuracy_trends(user_id, period),
                'time_distribution': await self._analyze_time_distribution(user_id, period),
                'difficulty_progression': await self._analyze_difficulty_progression(user_id, period),
                'comparative_analysis': await self._generate_comparative_analysis(user_id, period),
                'recommendations': await self._generate_personalized_recommendations(user_id)
            }

            # Cache results
            self.analysis_cache[cache_key] = {
                'data': dashboard_data,
                'timestamp': datetime.now()
            }

            return dashboard_data

        except Exception as e:
            print(f"Error generating dashboard for user {user_id}: {e}")
            return self._generate_empty_dashboard(user_id, period)

    async def _analyze_performance_metrics(self, user_id: int, period: AnalyticsPeriod) -> List[PerformanceMetric]:
        """Analyze key performance metrics with trends"""
        try:
            with get_db_session() as db:
                # Get data for current and previous periods
                current_start, current_end = self._get_period_dates(period)
                previous_start, previous_end = self._get_previous_period_dates(period)

                current_data = self._get_period_progress_data(db, user_id, current_start, current_end)
                previous_data = self._get_period_progress_data(db, user_id, previous_start, previous_end)

                metrics = []

                # Accuracy metric
                current_accuracy = np.mean([p.accuracy_score for p in current_data]) if current_data else 0
                previous_accuracy = np.mean([p.accuracy_score for p in previous_data]) if previous_data else 0
                accuracy_change = ((current_accuracy - previous_accuracy) / previous_accuracy * 100) if previous_accuracy > 0 else 0

                metrics.append(PerformanceMetric(
                    metric_name="Average Accuracy",
                    current_value=current_accuracy,
                    previous_value=previous_accuracy,
                    change_percent=accuracy_change,
                    trend=self._determine_trend(accuracy_change),
                    confidence=0.85,
                    recommendations=self._get_accuracy_recommendations(current_accuracy, accuracy_change)
                ))

                # Practice time metric
                current_time = sum([(p.session_duration or 0) for p in current_data])
                previous_time = sum([(p.session_duration or 0) for p in previous_data])
                time_change = ((current_time - previous_time) / previous_time * 100) if previous_time > 0 else 0

                metrics.append(PerformanceMetric(
                    metric_name="Practice Time (minutes)",
                    current_value=current_time,
                    previous_value=previous_time,
                    change_percent=time_change,
                    trend=self._determine_trend(time_change),
                    confidence=0.95,
                    recommendations=self._get_time_recommendations(current_time, time_change)
                ))

                # Consistency metric
                current_consistency = self._calculate_consistency_score(current_data)
                previous_consistency = self._calculate_consistency_score(previous_data)
                consistency_change = ((current_consistency - previous_consistency) / previous_consistency * 100) if previous_consistency > 0 else 0

                metrics.append(PerformanceMetric(
                    metric_name="Consistency Score",
                    current_value=current_consistency,
                    previous_value=previous_consistency,
                    change_percent=consistency_change,
                    trend=self._determine_trend(consistency_change),
                    confidence=0.75,
                    recommendations=self._get_consistency_recommendations(current_consistency, consistency_change)
                ))

                return metrics

        except Exception as e:
            print(f"Error analyzing performance metrics: {e}")
            return []

    async def _generate_learning_insights(self, user_id: int, period: AnalyticsPeriod) -> List[LearningInsight]:
        """Generate actionable learning insights"""
        insights = []

        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not progress_data:
                    insights.append(LearningInsight(
                        category="Practice",
                        title="No recent practice sessions",
                        description="You haven't practiced recently. Regular practice is key to improvement.",
                        severity="warning",
                        data_points={},
                        action_items=["Schedule daily practice time", "Start with 10-15 minutes per day"],
                        priority=1
                    ))
                    return insights

                # Analyze accuracy patterns
                accuracies = [p.accuracy_score for p in progress_data if p.accuracy_score]
                if accuracies:
                    avg_accuracy = np.mean(accuracies)
                    accuracy_std = np.std(accuracies)

                    if accuracy_std > 0.15:
                        insights.append(LearningInsight(
                            category="Performance",
                            title="Inconsistent accuracy detected",
                            description=f"Your accuracy varies significantly (std: {accuracy_std:.2f}). This suggests inconsistent practice conditions or techniques.",
                            severity="warning",
                            data_points={"average_accuracy": avg_accuracy, "std_deviation": accuracy_std},
                            action_items=[
                                "Practice in a quiet, consistent environment",
                                "Warm up before each session",
                                "Focus on slower, more deliberate practice"
                            ],
                            priority=2
                        ))

                    if avg_accuracy < 0.7:
                        insights.append(LearningInsight(
                            category="Accuracy",
                            title="Below target accuracy",
                            description=f"Your average accuracy ({avg_accuracy:.1%}) is below the recommended 70% threshold.",
                            severity="critical",
                            data_points={"current_accuracy": avg_accuracy, "target_accuracy": 0.7},
                            action_items=[
                                "Slow down your practice tempo",
                                "Focus on pitch accuracy over speed",
                                "Use a drone or tuner for reference"
                            ],
                            priority=1
                        ))

                # Analyze practice frequency
                practice_days = len(set(p.created_at.date() for p in progress_data))
                period_days = (current_end - current_start).days
                practice_frequency = practice_days / period_days

                if practice_frequency < 0.5:
                    insights.append(LearningInsight(
                        category="Consistency",
                        title="Low practice frequency",
                        description=f"You practiced on only {practice_days} out of {period_days} days ({practice_frequency:.1%}).",
                        severity="warning",
                        data_points={"practice_days": practice_days, "total_days": period_days},
                        action_items=[
                            "Set up a daily practice routine",
                            "Start with shorter, more frequent sessions",
                            "Use practice reminders"
                        ],
                        priority=2
                    ))

                # Analyze session durations
                durations = [p.session_duration for p in progress_data if p.session_duration]
                if durations:
                    avg_duration = np.mean(durations)
                    if avg_duration < 10:
                        insights.append(LearningInsight(
                            category="Practice Duration",
                            title="Short practice sessions",
                            description=f"Your average session is only {avg_duration:.1f} minutes. Longer sessions may be more beneficial.",
                            severity="info",
                            data_points={"average_duration": avg_duration},
                            action_items=[
                                "Gradually increase session length to 15-20 minutes",
                                "Include warmup and cooldown time",
                                "Focus on one skill per session"
                            ],
                            priority=3
                        ))

                # Positive insights
                if accuracies and np.mean(accuracies) > 0.85:
                    insights.append(LearningInsight(
                        category="Achievement",
                        title="Excellent accuracy!",
                        description=f"Your accuracy ({np.mean(accuracies):.1%}) is excellent! You're making great progress.",
                        severity="positive",
                        data_points={"accuracy": np.mean(accuracies)},
                        action_items=[
                            "Consider advancing to more challenging exercises",
                            "Explore new ragas or advanced patterns",
                            "Help other students with your expertise"
                        ],
                        priority=4
                    ))

                return sorted(insights, key=lambda x: x.priority)

        except Exception as e:
            print(f"Error generating learning insights: {e}")
            return []

    async def _analyze_practice_patterns(self, user_id: int, period: AnalyticsPeriod) -> PracticePattern:
        """Analyze user's practice patterns and habits"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not progress_data:
                    return PracticePattern(
                        pattern_type="Irregular",
                        frequency="None",
                        preferred_times=[],
                        session_duration_avg=0,
                        consistency_score=0.0,
                        recommendations=["Start with regular daily practice"]
                    )

                # Analyze practice times
                practice_hours = [p.created_at.hour for p in progress_data]
                hour_counts = {}
                for hour in practice_hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1

                preferred_times = []
                max_count = max(hour_counts.values()) if hour_counts else 0
                for hour, count in hour_counts.items():
                    if count >= max_count * 0.6:  # At least 60% of max frequency
                        time_label = self._hour_to_time_label(hour)
                        preferred_times.append(time_label)

                # Calculate frequency
                practice_days = len(set(p.created_at.date() for p in progress_data))
                period_days = (current_end - current_start).days
                frequency_score = practice_days / period_days

                if frequency_score >= 0.8:
                    frequency = "Daily"
                elif frequency_score >= 0.5:
                    frequency = "Regular"
                elif frequency_score >= 0.3:
                    frequency = "Occasional"
                else:
                    frequency = "Irregular"

                # Average session duration
                durations = [p.session_duration for p in progress_data if p.session_duration]
                avg_duration = int(np.mean(durations)) if durations else 0

                # Consistency score
                consistency_score = self._calculate_consistency_score(progress_data)

                # Generate recommendations
                recommendations = []
                if frequency_score < 0.5:
                    recommendations.append("Try to practice more regularly, even if for shorter periods")
                if avg_duration < 15:
                    recommendations.append("Consider slightly longer practice sessions (15-20 minutes)")
                if consistency_score < 0.7:
                    recommendations.append("Focus on maintaining consistent practice quality")
                if len(preferred_times) == 0:
                    recommendations.append("Establish a consistent practice time each day")

                return PracticePattern(
                    pattern_type=frequency,
                    frequency=f"{practice_days} days in {period_days} days",
                    preferred_times=preferred_times,
                    session_duration_avg=avg_duration,
                    consistency_score=consistency_score,
                    recommendations=recommendations
                )

        except Exception as e:
            print(f"Error analyzing practice patterns: {e}")
            return PracticePattern("Unknown", "Unknown", [], 0, 0.0, [])

    async def _analyze_swara_performance(self, user_id: int, period: AnalyticsPeriod) -> List[SwararAnalysis]:
        """Analyze performance for individual swaras"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                swara_data = {}
                for record in progress_data:
                    if record.exercise_data and 'target_swara' in record.exercise_data:
                        swara = record.exercise_data['target_swara']
                        if swara not in swara_data:
                            swara_data[swara] = []
                        swara_data[swara].append({
                            'accuracy': record.accuracy_score,
                            'date': record.created_at,
                            'duration': record.session_duration or 0
                        })

                analyses = []
                for swara, records in swara_data.items():
                    if len(records) < 2:
                        continue

                    accuracies = [r['accuracy'] for r in records]
                    avg_accuracy = np.mean(accuracies)
                    accuracy_trend = self._calculate_trend_line([r['accuracy'] for r in sorted(records, key=lambda x: x['date'])])

                    # Determine mastery level
                    if avg_accuracy >= 0.9 and len(records) >= 5:
                        mastery_level = "mastered"
                    elif avg_accuracy >= 0.8:
                        mastery_level = "advanced"
                    elif avg_accuracy >= 0.7:
                        mastery_level = "intermediate"
                    else:
                        mastery_level = "beginner"

                    # Calculate difficulty score based on consistency and accuracy
                    accuracy_std = np.std(accuracies)
                    difficulty_score = 1.0 - avg_accuracy + accuracy_std

                    # Generate issues and suggestions
                    common_issues = []
                    suggestions = []

                    if avg_accuracy < 0.7:
                        common_issues.append("Low accuracy")
                        suggestions.append(f"Practice {swara} with drone reference")

                    if accuracy_std > 0.15:
                        common_issues.append("Inconsistent performance")
                        suggestions.append("Focus on steady, controlled practice")

                    if len(records) < 5:
                        common_issues.append("Insufficient practice")
                        suggestions.append(f"Practice {swara} more frequently")

                    analyses.append(SwararAnalysis(
                        swara=swara,
                        accuracy_trend=accuracy_trend,
                        practice_frequency=len(records),
                        difficulty_score=difficulty_score,
                        mastery_level=mastery_level,
                        common_issues=common_issues,
                        improvement_suggestions=suggestions
                    ))

                return sorted(analyses, key=lambda x: x.difficulty_score, reverse=True)

        except Exception as e:
            print(f"Error analyzing swara performance: {e}")
            return []

    async def _generate_progress_predictions(self, user_id: int) -> List[ProgressPrediction]:
        """Generate ML-based predictions for learning progress"""
        predictions = []

        try:
            with get_db_session() as db:
                # Get historical data for modeling
                progress_data = db.query(Progress).filter(
                    Progress.user_id == user_id,
                    Progress.created_at >= datetime.now() - timedelta(days=90)
                ).all()

                if len(progress_data) < 10:
                    return []  # Need sufficient data for predictions

                # Predict swara mastery
                swara_predictions = self._predict_swara_mastery(progress_data)
                predictions.extend(swara_predictions)

                # Predict level advancement
                level_prediction = self._predict_level_advancement(progress_data)
                if level_prediction:
                    predictions.append(level_prediction)

                return predictions

        except Exception as e:
            print(f"Error generating progress predictions: {e}")
            return []

    def _predict_swara_mastery(self, progress_data: List[Progress]) -> List[ProgressPrediction]:
        """Predict when user will master each swara"""
        predictions = []

        swara_progress = {}
        for record in progress_data:
            if record.exercise_data and 'target_swara' in record.exercise_data:
                swara = record.exercise_data['target_swara']
                if swara not in swara_progress:
                    swara_progress[swara] = []
                swara_progress[swara].append({
                    'accuracy': record.accuracy_score,
                    'date': record.created_at
                })

        for swara, records in swara_progress.items():
            if len(records) < 5:
                continue

            sorted_records = sorted(records, key=lambda x: x['date'])
            accuracies = [r['accuracy'] for r in sorted_records]

            current_accuracy = np.mean(accuracies[-3:])  # Last 3 sessions
            if current_accuracy >= 0.9:
                continue  # Already mastered

            # Simple linear regression for prediction
            improvement_rate = self._calculate_improvement_rate(accuracies)
            if improvement_rate <= 0:
                continue

            sessions_needed = max(1, int((0.9 - current_accuracy) / improvement_rate))
            days_needed = sessions_needed * 2  # Assuming practice every other day

            confidence = min(0.8, len(records) / 20.0)  # Higher confidence with more data

            predictions.append(ProgressPrediction(
                target_skill=f"{swara} Mastery",
                current_level=current_accuracy,
                predicted_timeline=days_needed,
                confidence=confidence,
                milestones=[
                    {"accuracy": 0.8, "days": int(days_needed * 0.6)},
                    {"accuracy": 0.85, "days": int(days_needed * 0.8)},
                    {"accuracy": 0.9, "days": days_needed}
                ],
                factors_affecting=["Practice frequency", "Session quality", "Consistency"]
            ))

        return predictions

    def _predict_level_advancement(self, progress_data: List[Progress]) -> Optional[ProgressPrediction]:
        """Predict when user will advance to next difficulty level"""
        # Simplified level advancement prediction
        recent_accuracy = [p.accuracy_score for p in progress_data[-10:]]
        if not recent_accuracy:
            return None

        avg_recent_accuracy = np.mean(recent_accuracy)
        if avg_recent_accuracy < 0.75:
            return None  # Not ready for advancement

        # Predict advancement to next level
        return ProgressPrediction(
            target_skill="Next Difficulty Level",
            current_level=avg_recent_accuracy,
            predicted_timeline=14,  # 2 weeks
            confidence=0.7,
            milestones=[
                {"milestone": "Consistent 80% accuracy", "days": 7},
                {"milestone": "Complete current level exercises", "days": 14}
            ],
            factors_affecting=["Current performance", "Practice consistency"]
        )

    # Helper methods
    def _get_period_dates(self, period: AnalyticsPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for the specified period"""
        now = datetime.now()

        if period == AnalyticsPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == AnalyticsPeriod.WEEKLY:
            days_since_monday = now.weekday()
            start = now - timedelta(days=days_since_monday)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == AnalyticsPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == AnalyticsPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3 + 1
            start = now.replace(month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        else:  # YEARLY
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now

        return start, end

    def _get_previous_period_dates(self, period: AnalyticsPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for the previous period"""
        current_start, current_end = self._get_period_dates(period)
        period_length = current_end - current_start

        previous_end = current_start
        previous_start = previous_end - period_length

        return previous_start, previous_end

    def _get_period_progress_data(self, db: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Progress]:
        """Get progress data for specified period"""
        return db.query(Progress).filter(
            Progress.user_id == user_id,
            Progress.created_at >= start_date,
            Progress.created_at <= end_date
        ).all()

    def _calculate_consistency_score(self, progress_data: List[Progress]) -> float:
        """Calculate consistency score based on practice patterns"""
        if not progress_data:
            return 0.0

        accuracies = [p.accuracy_score for p in progress_data if p.accuracy_score]
        if not accuracies:
            return 0.0

        # Consistency is inverse of standard deviation
        std_dev = np.std(accuracies)
        consistency = max(0.0, 1.0 - std_dev)

        return consistency

    def _determine_trend(self, change_percent: float) -> str:
        """Determine trend direction"""
        if change_percent > 5:
            return "improving"
        elif change_percent < -5:
            return "declining"
        else:
            return "stable"

    def _calculate_trend_line(self, values: List[float]) -> List[float]:
        """Calculate linear trend line for values"""
        if len(values) < 2:
            return values

        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        trend_line = np.polyval(coeffs, x).tolist()

        return trend_line

    def _calculate_improvement_rate(self, accuracies: List[float]) -> float:
        """Calculate rate of improvement per session"""
        if len(accuracies) < 2:
            return 0.0

        x = np.arange(len(accuracies))
        slope = np.polyfit(x, accuracies, 1)[0]

        return max(0.0, slope)

    def _hour_to_time_label(self, hour: int) -> str:
        """Convert hour to readable time label"""
        if 6 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    def _get_accuracy_recommendations(self, current_accuracy: float, change_percent: float) -> List[str]:
        """Get recommendations based on accuracy metrics"""
        recommendations = []

        if current_accuracy < 0.7:
            recommendations.append("Focus on slower, more precise practice")
            recommendations.append("Use drone or tuner for pitch reference")
        elif current_accuracy < 0.8:
            recommendations.append("Good progress! Try slightly more challenging exercises")
        else:
            recommendations.append("Excellent accuracy! Consider advancing to next level")

        if change_percent < -10:
            recommendations.append("Recent decline detected - review fundamentals")
        elif change_percent > 10:
            recommendations.append("Great improvement! Maintain current practice routine")

        return recommendations

    def _get_time_recommendations(self, current_time: int, change_percent: float) -> List[str]:
        """Get recommendations based on practice time"""
        recommendations = []

        if current_time < 300:  # Less than 5 hours
            recommendations.append("Try to increase practice time gradually")
        elif current_time > 1200:  # More than 20 hours
            recommendations.append("Great dedication! Ensure you're not overexerting")

        if change_percent < -20:
            recommendations.append("Practice time has decreased - try to maintain consistency")

        return recommendations

    def _get_consistency_recommendations(self, consistency: float, change_percent: float) -> List[str]:
        """Get recommendations based on consistency score"""
        recommendations = []

        if consistency < 0.6:
            recommendations.append("Focus on steady, controlled practice")
            recommendations.append("Practice in consistent environment")
        else:
            recommendations.append("Good consistency! Keep up the stable practice")

        return recommendations

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.analysis_cache:
            return False

        cache_time = self.analysis_cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_duration

    def _generate_empty_dashboard(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Generate empty dashboard for error cases"""
        return {
            'user_id': user_id,
            'period': period.value,
            'generated_at': datetime.now().isoformat(),
            'error': 'Unable to generate analytics data',
            'performance_metrics': [],
            'learning_insights': [],
            'practice_patterns': {},
            'swara_analysis': [],
            'progress_predictions': [],
            'recommendations': ["Start practicing regularly to see analytics"]
        }

    # Additional analysis methods would continue here...
    async def _analyze_streaks(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze practice streaks"""
        # Implementation for streak analysis
        return {"current_streak": 0, "longest_streak": 0, "streak_insights": []}

    async def _analyze_accuracy_trends(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze accuracy trends over time"""
        # Implementation for accuracy trend analysis
        return {"trend_data": [], "trend_direction": "stable"}

    async def _analyze_time_distribution(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze how practice time is distributed"""
        # Implementation for time distribution analysis
        return {"distribution": {}, "peak_hours": []}

    async def _analyze_difficulty_progression(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze progression through difficulty levels"""
        # Implementation for difficulty progression analysis
        return {"current_level": 1, "progression_rate": 0}

    async def _generate_comparative_analysis(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Generate comparative analysis with peer performance"""
        # Implementation for comparative analysis
        return {"peer_comparison": {}, "ranking": 0}

    async def _generate_personalized_recommendations(self, user_id: int) -> List[str]:
        """Generate personalized recommendations"""
        # Implementation for personalized recommendations
        return ["Continue regular practice", "Focus on challenging swaras"]

# Initialize analytics engine
analytics_engine = AdvancedAnalytics()

# Export functions for API use
async def get_user_analytics_dashboard(user_id: int, period: str = "monthly") -> Dict:
    """Get comprehensive analytics dashboard for user"""
    period_enum = AnalyticsPeriod(period)
    return await analytics_engine.generate_user_dashboard(user_id, period_enum)

async def get_performance_metrics(user_id: int, period: str = "monthly") -> List[Dict]:
    """Get performance metrics for user"""
    period_enum = AnalyticsPeriod(period)
    metrics = await analytics_engine._analyze_performance_metrics(user_id, period_enum)
    return [asdict(metric) for metric in metrics]

async def get_learning_insights(user_id: int, period: str = "monthly") -> List[Dict]:
    """Get learning insights for user"""
    period_enum = AnalyticsPeriod(period)
    insights = await analytics_engine._generate_learning_insights(user_id, period_enum)
    return [asdict(insight) for insight in insights]