"""
Analytics API Routes
Provides endpoints for accessing comprehensive user analytics and insights.
"""

from flask import Blueprint, request, jsonify, session
from typing import Dict, List, Any
import asyncio
from dataclasses import asdict

from .dashboard import AdvancedAnalytics, AnalyticsPeriod, PerformanceMetric, LearningInsight, PracticePattern, SwararAnalysis, ProgressPrediction

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# Initialize analytics engine
analytics_engine = AdvancedAnalytics()


@analytics_bp.route('/dashboard/<int:user_id>', methods=['GET'])
async def get_dashboard(user_id: int):
    """
    Retrieve comprehensive analytics dashboard for a specific user.
    Query parameters: period (daily, weekly, monthly, quarterly, yearly)
    """
    period_str = request.args.get('period', 'monthly').upper()
    try:
        period = AnalyticsPeriod[period_str]
    except KeyError:
        return jsonify({'error': 'Invalid period specified'}), 400

    dashboard_data = await analytics_engine.generate_user_dashboard(user_id, period)
    return jsonify(dashboard_data)


@analytics_bp.route('/metrics/<int:user_id>', methods=['GET'])
async def get_metrics(user_id: int):
    """
    Retrieve key performance metrics for a specific user.
    Query parameters: period (daily, weekly, monthly, quarterly, yearly)
    """
    period_str = request.args.get('period', 'monthly').upper()
    try:
        period = AnalyticsPeriod[period_str]
    except KeyError:
        return jsonify({'error': 'Invalid period specified'}), 400

    metrics = await analytics_engine._analyze_performance_metrics(user_id, period)
    return jsonify([asdict(m) for m in metrics])


@analytics_bp.route('/insights/<int:user_id>', methods=['GET'])
async def get_insights(user_id: int):
    """
    Retrieve actionable learning insights for a specific user.
    Query parameters: period (daily, weekly, monthly, quarterly, yearly)
    """
    period_str = request.args.get('period', 'monthly').upper()
    try:
        period = AnalyticsPeriod[period_str]
    except KeyError:
        return jsonify({'error': 'Invalid period specified'}), 400

    insights = await analytics_engine._generate_learning_insights(user_id, period)
    return jsonify([asdict(i) for i in insights])


@analytics_bp.route('/patterns/<int:user_id>', methods=['GET'])
async def get_patterns(user_id: int):
    """
    Retrieve practice patterns for a specific user.
    Query parameters: period (daily, weekly, monthly, quarterly, yearly)
    """
    period_str = request.args.get('period', 'monthly').upper()
    try:
        period = AnalyticsPeriod[period_str]
    except KeyError:
        return jsonify({'error': 'Invalid period specified'}), 400

    patterns = await analytics_engine._analyze_practice_patterns(user_id, period)
    return jsonify(asdict(patterns))


@analytics_bp.route('/swara-performance/<int:user_id>', methods=['GET'])
async def get_swara_performance(user_id: int):
    """
    Retrieve swara-specific performance analysis for a user.
    Query parameters: period (daily, weekly, monthly, quarterly, yearly)
    """
    period_str = request.args.get('period', 'monthly').upper()
    try:
        period = AnalyticsPeriod[period_str]
    except KeyError:
        return jsonify({'error': 'Invalid period specified'}), 400

    analysis = await analytics_engine._analyze_swara_performance(user_id, period)
    return jsonify([asdict(a) for a in analysis])


@analytics_bp.route('/predictions/<int:user_id>', methods=['GET'])
async def get_predictions(user_id: int):
    """
    Retrieve learning progress predictions for a user.
    """
    predictions = await analytics_engine._generate_progress_predictions(user_id)
    return jsonify([asdict(p) for p in predictions])
