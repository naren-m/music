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

from config.database import get_db_session
from core.models.user import UserProfile
from config.database import User, Progress, Exercise, Recording, Achievement

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

    async def _analyze_streaks(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze practice streaks - consecutive days of practice"""
        try:
            with get_db_session() as db:
                # Get all practice sessions for the user
                all_progress = db.query(Progress).filter(
                    Progress.user_id == user_id
                ).order_by(Progress.created_at.desc()).all()

                if not all_progress:
                    return {
                        "current_streak": 0,
                        "longest_streak": 0,
                        "streak_insights": ["Start practicing to build your streak!"],
                        "streak_history": [],
                        "best_streak_dates": None
                    }

                # Extract unique practice dates
                practice_dates = sorted(set(p.created_at.date() for p in all_progress), reverse=True)

                if not practice_dates:
                    return {
                        "current_streak": 0,
                        "longest_streak": 0,
                        "streak_insights": [],
                        "streak_history": [],
                        "best_streak_dates": None
                    }

                # Calculate current streak
                today = datetime.now().date()
                current_streak = 0
                check_date = today

                for practice_date in practice_dates:
                    if practice_date == check_date or practice_date == check_date - timedelta(days=1):
                        current_streak += 1
                        check_date = practice_date - timedelta(days=1)
                    else:
                        break

                # Calculate longest streak
                longest_streak = 0
                current_run = 1
                best_streak_start = None
                best_streak_end = None
                current_run_start = practice_dates[0] if practice_dates else None

                for i in range(1, len(practice_dates)):
                    if practice_dates[i-1] - practice_dates[i] == timedelta(days=1):
                        current_run += 1
                    else:
                        if current_run > longest_streak:
                            longest_streak = current_run
                            best_streak_end = current_run_start
                            best_streak_start = practice_dates[i-1]
                        current_run = 1
                        current_run_start = practice_dates[i]

                # Check final run
                if current_run > longest_streak:
                    longest_streak = current_run
                    best_streak_end = current_run_start
                    best_streak_start = practice_dates[-1] if practice_dates else None

                # Generate streak insights
                insights = []
                if current_streak >= 7:
                    insights.append(f"Amazing! You're on a {current_streak}-day streak!")
                elif current_streak >= 3:
                    insights.append(f"Good momentum! {current_streak} days and counting.")
                elif current_streak == 0:
                    insights.append("Practice today to start a new streak!")
                else:
                    insights.append(f"You have a {current_streak}-day streak. Keep it up!")

                if longest_streak > current_streak:
                    insights.append(f"Your record is {longest_streak} days. Can you beat it?")

                # Calculate weekly streak history
                streak_history = []
                for week in range(4):  # Last 4 weeks
                    week_start = today - timedelta(days=today.weekday() + week*7)
                    week_end = week_start + timedelta(days=6)
                    week_practices = sum(1 for d in practice_dates if week_start <= d <= week_end)
                    streak_history.append({
                        "week_start": week_start.isoformat(),
                        "days_practiced": week_practices,
                        "percentage": round(week_practices / 7 * 100, 1)
                    })

                return {
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "streak_insights": insights,
                    "streak_history": streak_history[::-1],  # Oldest first
                    "best_streak_dates": {
                        "start": best_streak_start.isoformat() if best_streak_start else None,
                        "end": best_streak_end.isoformat() if best_streak_end else None
                    } if best_streak_start else None,
                    "practiced_today": today in practice_dates
                }

        except Exception as e:
            print(f"Error analyzing streaks: {e}")
            return {"current_streak": 0, "longest_streak": 0, "streak_insights": [], "streak_history": []}

    async def _analyze_accuracy_trends(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze accuracy trends over time with detailed breakdown"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not progress_data:
                    return {
                        "trend_data": [],
                        "trend_direction": "insufficient_data",
                        "average_accuracy": 0,
                        "best_accuracy": 0,
                        "worst_accuracy": 0,
                        "improvement_rate": 0,
                        "consistency_rating": "N/A"
                    }

                # Sort by date
                sorted_data = sorted(progress_data, key=lambda x: x.created_at)
                accuracies = [p.accuracy_score for p in sorted_data if p.accuracy_score is not None]

                if not accuracies:
                    return {
                        "trend_data": [],
                        "trend_direction": "no_data",
                        "average_accuracy": 0,
                        "best_accuracy": 0,
                        "worst_accuracy": 0,
                        "improvement_rate": 0,
                        "consistency_rating": "N/A"
                    }

                # Calculate trend line
                trend_line = self._calculate_trend_line(accuracies)

                # Prepare daily/session trend data
                trend_data = []
                for i, record in enumerate(sorted_data):
                    if record.accuracy_score is not None:
                        trend_data.append({
                            "date": record.created_at.isoformat(),
                            "accuracy": round(record.accuracy_score, 4),
                            "trend_value": round(trend_line[i], 4) if i < len(trend_line) else None
                        })

                # Determine overall trend direction
                if len(accuracies) >= 3:
                    first_half_avg = np.mean(accuracies[:len(accuracies)//2])
                    second_half_avg = np.mean(accuracies[len(accuracies)//2:])
                    improvement = second_half_avg - first_half_avg

                    if improvement > 0.05:
                        trend_direction = "improving"
                    elif improvement < -0.05:
                        trend_direction = "declining"
                    else:
                        trend_direction = "stable"

                    improvement_rate = round(improvement * 100, 2)  # As percentage points
                else:
                    trend_direction = "insufficient_data"
                    improvement_rate = 0

                # Consistency rating based on standard deviation
                std_dev = np.std(accuracies)
                if std_dev < 0.05:
                    consistency_rating = "Excellent"
                elif std_dev < 0.10:
                    consistency_rating = "Good"
                elif std_dev < 0.15:
                    consistency_rating = "Fair"
                else:
                    consistency_rating = "Needs Improvement"

                return {
                    "trend_data": trend_data,
                    "trend_direction": trend_direction,
                    "average_accuracy": round(np.mean(accuracies), 4),
                    "best_accuracy": round(max(accuracies), 4),
                    "worst_accuracy": round(min(accuracies), 4),
                    "improvement_rate": improvement_rate,
                    "consistency_rating": consistency_rating,
                    "standard_deviation": round(std_dev, 4),
                    "total_sessions": len(accuracies)
                }

        except Exception as e:
            print(f"Error analyzing accuracy trends: {e}")
            return {"trend_data": [], "trend_direction": "error", "average_accuracy": 0}

    async def _analyze_time_distribution(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze how practice time is distributed across hours and days"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not progress_data:
                    return {
                        "hourly_distribution": {},
                        "daily_distribution": {},
                        "peak_hours": [],
                        "peak_days": [],
                        "total_practice_time": 0,
                        "average_session_duration": 0,
                        "recommendations": ["Start practicing to see your time distribution"]
                    }

                # Hourly distribution
                hourly_distribution = {str(h).zfill(2): 0 for h in range(24)}
                hourly_sessions = {str(h).zfill(2): 0 for h in range(24)}

                # Daily distribution (0=Monday, 6=Sunday)
                daily_distribution = {day: 0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
                daily_sessions = {day: 0 for day in daily_distribution.keys()}

                total_time = 0
                session_durations = []

                for record in progress_data:
                    hour = str(record.created_at.hour).zfill(2)
                    day = record.created_at.strftime("%A")
                    duration = record.session_duration or 0

                    hourly_distribution[hour] += duration
                    hourly_sessions[hour] += 1
                    daily_distribution[day] += duration
                    daily_sessions[day] += 1
                    total_time += duration
                    if duration > 0:
                        session_durations.append(duration)

                # Find peak hours (top 3)
                peak_hours = sorted(
                    [(h, t) for h, t in hourly_distribution.items() if t > 0],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]

                peak_hours_formatted = []
                for hour, minutes in peak_hours:
                    h = int(hour)
                    time_label = f"{h:02d}:00-{(h+1)%24:02d}:00"
                    period_label = "Morning" if 6 <= h < 12 else "Afternoon" if 12 <= h < 17 else "Evening" if 17 <= h < 21 else "Night"
                    peak_hours_formatted.append({
                        "hour": time_label,
                        "period": period_label,
                        "total_minutes": round(minutes, 1),
                        "sessions": hourly_sessions[hour]
                    })

                # Find peak days
                peak_days = sorted(
                    [(d, t) for d, t in daily_distribution.items() if t > 0],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]

                peak_days_formatted = [
                    {"day": day, "total_minutes": round(minutes, 1), "sessions": daily_sessions[day]}
                    for day, minutes in peak_days
                ]

                # Generate recommendations
                recommendations = []
                avg_duration = np.mean(session_durations) if session_durations else 0

                if avg_duration < 10:
                    recommendations.append("Consider longer practice sessions (15-20 minutes)")

                weekend_time = daily_distribution["Saturday"] + daily_distribution["Sunday"]
                weekday_time = sum(daily_distribution[d] for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

                if weekend_time > weekday_time * 2:
                    recommendations.append("Try to distribute practice more evenly across the week")

                if len(peak_hours) > 0:
                    recommendations.append(f"Your most productive time is around {peak_hours[0][0]}:00")

                return {
                    "hourly_distribution": {h: round(t, 1) for h, t in hourly_distribution.items()},
                    "daily_distribution": {d: round(t, 1) for d, t in daily_distribution.items()},
                    "peak_hours": peak_hours_formatted,
                    "peak_days": peak_days_formatted,
                    "total_practice_time": round(total_time, 1),
                    "average_session_duration": round(avg_duration, 1),
                    "total_sessions": len(progress_data),
                    "recommendations": recommendations
                }

        except Exception as e:
            print(f"Error analyzing time distribution: {e}")
            return {"hourly_distribution": {}, "daily_distribution": {}, "peak_hours": [], "peak_days": []}

    async def _analyze_difficulty_progression(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Analyze progression through difficulty levels"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)
                progress_data = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not progress_data:
                    return {
                        "current_level": 1,
                        "progression_rate": 0,
                        "level_history": [],
                        "exercises_by_level": {},
                        "ready_for_advancement": False,
                        "advancement_criteria": {}
                    }

                # Extract difficulty levels from exercise data
                difficulty_levels = {
                    "beginner": 1,
                    "intermediate": 2,
                    "advanced": 3,
                    "expert": 4
                }

                level_sessions = {level: [] for level in difficulty_levels.keys()}
                level_accuracies = {level: [] for level in difficulty_levels.keys()}

                for record in progress_data:
                    if record.exercise_data:
                        level = record.exercise_data.get("difficulty", "beginner")
                        if level in level_sessions:
                            level_sessions[level].append(record)
                            if record.accuracy_score is not None:
                                level_accuracies[level].append(record.accuracy_score)

                # Determine current level based on recent activity
                current_level = "beginner"
                for level in ["expert", "advanced", "intermediate", "beginner"]:
                    if len(level_sessions[level]) >= 3:
                        current_level = level
                        break

                current_level_num = difficulty_levels.get(current_level, 1)

                # Calculate progression rate
                sorted_data = sorted(progress_data, key=lambda x: x.created_at)
                if len(sorted_data) >= 2:
                    first_quarter = sorted_data[:len(sorted_data)//4] if len(sorted_data) >= 4 else sorted_data[:1]
                    last_quarter = sorted_data[-len(sorted_data)//4:] if len(sorted_data) >= 4 else sorted_data[-1:]

                    first_avg_level = np.mean([
                        difficulty_levels.get(r.exercise_data.get("difficulty", "beginner"), 1)
                        for r in first_quarter if r.exercise_data
                    ]) if first_quarter else 1

                    last_avg_level = np.mean([
                        difficulty_levels.get(r.exercise_data.get("difficulty", "beginner"), 1)
                        for r in last_quarter if r.exercise_data
                    ]) if last_quarter else 1

                    progression_rate = last_avg_level - first_avg_level
                else:
                    progression_rate = 0

                # Check readiness for advancement
                current_accuracies = level_accuracies.get(current_level, [])
                avg_accuracy = np.mean(current_accuracies) if current_accuracies else 0
                session_count = len(level_sessions.get(current_level, []))

                ready_for_advancement = (
                    avg_accuracy >= 0.80 and
                    session_count >= 5 and
                    current_level != "expert"
                )

                advancement_criteria = {
                    "accuracy_threshold": 0.80,
                    "current_accuracy": round(avg_accuracy, 4),
                    "sessions_required": 5,
                    "current_sessions": session_count,
                    "accuracy_met": avg_accuracy >= 0.80,
                    "sessions_met": session_count >= 5
                }

                # Level history
                level_history = []
                for level, sessions in level_sessions.items():
                    if sessions:
                        level_history.append({
                            "level": level,
                            "level_number": difficulty_levels[level],
                            "sessions_completed": len(sessions),
                            "average_accuracy": round(np.mean(level_accuracies[level]), 4) if level_accuracies[level] else 0,
                            "first_attempt": min(s.created_at for s in sessions).isoformat(),
                            "last_attempt": max(s.created_at for s in sessions).isoformat()
                        })

                return {
                    "current_level": current_level,
                    "current_level_number": current_level_num,
                    "progression_rate": round(progression_rate, 2),
                    "level_history": sorted(level_history, key=lambda x: x["level_number"]),
                    "exercises_by_level": {level: len(sessions) for level, sessions in level_sessions.items()},
                    "ready_for_advancement": ready_for_advancement,
                    "advancement_criteria": advancement_criteria
                }

        except Exception as e:
            print(f"Error analyzing difficulty progression: {e}")
            return {"current_level": 1, "progression_rate": 0}

    async def _generate_comparative_analysis(self, user_id: int, period: AnalyticsPeriod) -> Dict:
        """Generate comparative analysis with peer performance (anonymized)"""
        try:
            with get_db_session() as db:
                current_start, current_end = self._get_period_dates(period)

                # Get user's data
                user_progress = self._get_period_progress_data(db, user_id, current_start, current_end)

                if not user_progress:
                    return {
                        "peer_comparison": {},
                        "ranking": None,
                        "percentile": None,
                        "insights": ["Practice more to see how you compare with others"]
                    }

                user_accuracies = [p.accuracy_score for p in user_progress if p.accuracy_score is not None]
                user_avg_accuracy = np.mean(user_accuracies) if user_accuracies else 0
                user_practice_time = sum(p.session_duration or 0 for p in user_progress)
                user_session_count = len(user_progress)

                # Get all users' aggregated data for the period (anonymized)
                all_users_data = db.query(
                    Progress.user_id,
                    func.avg(Progress.accuracy_score).label('avg_accuracy'),
                    func.sum(Progress.session_duration).label('total_time'),
                    func.count(Progress.id).label('session_count')
                ).filter(
                    Progress.created_at >= current_start,
                    Progress.created_at <= current_end
                ).group_by(Progress.user_id).all()

                if len(all_users_data) < 3:
                    return {
                        "peer_comparison": {
                            "user_accuracy": round(user_avg_accuracy, 4),
                            "user_practice_time": round(user_practice_time, 1),
                            "user_sessions": user_session_count
                        },
                        "ranking": None,
                        "percentile": None,
                        "insights": ["Not enough peer data for comparison"]
                    }

                # Calculate rankings
                accuracy_values = [u.avg_accuracy for u in all_users_data if u.avg_accuracy]
                time_values = [u.total_time for u in all_users_data if u.total_time]
                session_values = [u.session_count for u in all_users_data]

                accuracy_rank = sum(1 for v in accuracy_values if v > user_avg_accuracy) + 1
                accuracy_percentile = round((1 - accuracy_rank / len(accuracy_values)) * 100, 1) if accuracy_values else 0

                time_rank = sum(1 for v in time_values if v > user_practice_time) + 1
                time_percentile = round((1 - time_rank / len(time_values)) * 100, 1) if time_values else 0

                # Generate insights
                insights = []
                if accuracy_percentile >= 75:
                    insights.append(f"Your accuracy is in the top {100-accuracy_percentile:.0f}% of learners!")
                elif accuracy_percentile >= 50:
                    insights.append("Your accuracy is above average. Keep improving!")
                else:
                    insights.append("Focus on accuracy to move up the rankings.")

                if time_percentile >= 75:
                    insights.append(f"You practice more than {time_percentile:.0f}% of learners. Great dedication!")
                elif time_percentile < 25:
                    insights.append("Consider increasing your practice time.")

                return {
                    "peer_comparison": {
                        "user_accuracy": round(user_avg_accuracy, 4),
                        "peer_avg_accuracy": round(np.mean(accuracy_values), 4) if accuracy_values else 0,
                        "peer_top_accuracy": round(np.percentile(accuracy_values, 90), 4) if accuracy_values else 0,
                        "user_practice_time": round(user_practice_time, 1),
                        "peer_avg_practice_time": round(np.mean(time_values), 1) if time_values else 0,
                        "user_sessions": user_session_count,
                        "peer_avg_sessions": round(np.mean(session_values), 1) if session_values else 0
                    },
                    "accuracy_ranking": {
                        "rank": accuracy_rank,
                        "total_users": len(accuracy_values),
                        "percentile": accuracy_percentile
                    },
                    "time_ranking": {
                        "rank": time_rank,
                        "total_users": len(time_values),
                        "percentile": time_percentile
                    },
                    "insights": insights
                }

        except Exception as e:
            print(f"Error generating comparative analysis: {e}")
            return {"peer_comparison": {}, "ranking": None, "percentile": None}

    async def _generate_personalized_recommendations(self, user_id: int) -> List[str]:
        """Generate personalized recommendations based on user's learning patterns"""
        recommendations = []

        try:
            with get_db_session() as db:
                # Get recent progress data (last 30 days)
                cutoff = datetime.now() - timedelta(days=30)
                recent_progress = db.query(Progress).filter(
                    Progress.user_id == user_id,
                    Progress.created_at >= cutoff
                ).order_by(Progress.created_at.desc()).all()

                if not recent_progress:
                    return [
                        "Start with basic swara recognition exercises",
                        "Practice Sa-Pa-Sa patterns to build pitch awareness",
                        "Set a daily 10-minute practice goal",
                        "Use the tanpura drone feature for pitch reference"
                    ]

                # Analyze practice frequency
                practice_dates = set(p.created_at.date() for p in recent_progress)
                practice_frequency = len(practice_dates) / 30

                if practice_frequency < 0.3:
                    recommendations.append("Try to practice at least 3 times per week for consistent improvement")
                elif practice_frequency < 0.5:
                    recommendations.append("Good start! Increase practice frequency to 4-5 days per week")
                elif practice_frequency >= 0.8:
                    recommendations.append("Excellent consistency! Maintain your daily practice routine")

                # Analyze accuracy
                accuracies = [p.accuracy_score for p in recent_progress if p.accuracy_score is not None]
                if accuracies:
                    avg_accuracy = np.mean(accuracies)
                    recent_accuracy = np.mean(accuracies[:5]) if len(accuracies) >= 5 else avg_accuracy

                    if avg_accuracy < 0.6:
                        recommendations.append("Focus on slower, more deliberate practice with drone reference")
                        recommendations.append("Try single swara exercises before moving to patterns")
                    elif avg_accuracy < 0.75:
                        recommendations.append("Good progress! Work on consistency with sequential patterns")
                    elif avg_accuracy >= 0.85:
                        recommendations.append("Ready for advanced challenges! Try gamaka patterns or new ragas")

                    # Check for recent decline
                    if len(accuracies) >= 10:
                        early_avg = np.mean(accuracies[-10:-5])
                        late_avg = np.mean(accuracies[-5:])
                        if late_avg < early_avg - 0.1:
                            recommendations.append("Recent performance dip detected - review fundamentals and ensure proper warmup")

                # Analyze session duration
                durations = [p.session_duration for p in recent_progress if p.session_duration]
                if durations:
                    avg_duration = np.mean(durations)
                    if avg_duration < 10:
                        recommendations.append("Gradually increase sessions to 15-20 minutes for better progress")
                    elif avg_duration > 45:
                        recommendations.append("Long sessions are great! Consider breaking into multiple focused sessions")

                # Analyze weak areas from exercise data
                swara_performance = {}
                for record in recent_progress:
                    if record.exercise_data and 'target_swara' in record.exercise_data:
                        swara = record.exercise_data['target_swara']
                        if swara not in swara_performance:
                            swara_performance[swara] = []
                        if record.accuracy_score is not None:
                            swara_performance[swara].append(record.accuracy_score)

                if swara_performance:
                    weak_swaras = [
                        swara for swara, scores in swara_performance.items()
                        if len(scores) >= 3 and np.mean(scores) < 0.7
                    ]
                    if weak_swaras:
                        recommendations.append(f"Focus extra practice on: {', '.join(weak_swaras[:3])}")

                # If we still have room for recommendations
                if len(recommendations) < 3:
                    recommendations.extend([
                        "Record and listen back to your practice sessions",
                        "Join community challenges to stay motivated",
                        "Explore different ragas to broaden your musical vocabulary"
                    ][:3 - len(recommendations)])

                return recommendations[:6]  # Limit to 6 recommendations

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return [
                "Continue regular practice",
                "Focus on challenging swaras",
                "Set specific practice goals"
            ]
