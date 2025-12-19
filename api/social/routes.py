"""
Social API Routes
Handles community features, groups, collaboration, and social discovery.
Provides user search, activity feeds, leaderboards, and practice challenges.
"""

from flask import Blueprint, request, jsonify, session, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import joinedload
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from config.database import get_db_session, Group, User, FriendRequest, Exercise, Progress, Achievement


social_bp = Blueprint('social', __name__, url_prefix='/api/v1/social')


# ============================================================================
# Enums and Data Classes
# ============================================================================

class ActivityType(str, Enum):
    """Types of activities in the feed."""
    ACHIEVEMENT_EARNED = "achievement_earned"
    PRACTICE_SESSION = "practice_session"
    MILESTONE_REACHED = "milestone_reached"
    GROUP_JOINED = "group_joined"
    FRIEND_ADDED = "friend_added"
    CHALLENGE_COMPLETED = "challenge_completed"
    STREAK_ACHIEVED = "streak_achieved"


class ChallengeStatus(str, Enum):
    """Status of a practice challenge."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class PracticeChallenge:
    """Represents a practice challenge between users or groups."""
    challenge_id: str
    creator_id: int
    challenge_type: str  # 'accuracy', 'duration', 'streak', 'shruti_mastery'
    target_value: float
    start_date: datetime
    end_date: datetime
    participants: List[int] = field(default_factory=list)
    status: str = ChallengeStatus.PENDING
    results: Dict[int, float] = field(default_factory=dict)


# In-memory challenge storage (in production, use database)
_active_challenges: Dict[str, PracticeChallenge] = {}


# ============================================================================
# User Search and Discovery
# ============================================================================

@social_bp.route('/users/search', methods=['GET'])
def search_users():
    """
    Search for users by username or full name.

    Query Params:
        q: Search query (min 2 characters)
        limit: Max results (default 20, max 50)
        offset: Pagination offset
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 50)
    offset = int(request.args.get('offset', 0))
    current_user_id = session.get('user_id', 1)

    if len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400

    try:
        with get_db_session() as db:
            # Search users by username or full name (case-insensitive)
            search_pattern = f"%{query.lower()}%"
            users = db.query(User).filter(
                and_(
                    User.id != current_user_id,
                    User.is_active == True,
                    or_(
                        func.lower(User.username).like(search_pattern),
                        func.lower(User.full_name).like(search_pattern)
                    )
                )
            ).offset(offset).limit(limit).all()

            # Get friendship status for each user
            results = []
            for user in users:
                friendship = db.query(FriendRequest).filter(
                    or_(
                        and_(FriendRequest.sender_id == current_user_id,
                             FriendRequest.receiver_id == user.id),
                        and_(FriendRequest.sender_id == user.id,
                             FriendRequest.receiver_id == current_user_id)
                    )
                ).first()

                friendship_status = 'none'
                if friendship:
                    if friendship.status == 'accepted':
                        friendship_status = 'friends'
                    elif friendship.status == 'pending':
                        if friendship.sender_id == current_user_id:
                            friendship_status = 'request_sent'
                        else:
                            friendship_status = 'request_received'

                results.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'friendship_status': friendship_status,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })

            return jsonify({
                'query': query,
                'results': results,
                'count': len(results),
                'offset': offset,
                'limit': limit
            })

    except Exception as e:
        current_app.logger.error(f"Error searching users: {e}")
        return jsonify({'error': 'Failed to search users'}), 500


@social_bp.route('/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id: int):
    """
    Get public profile of a user.
    Shows practice stats, achievements, and mutual friends.
    """
    current_user_id = session.get('user_id', 1)

    try:
        with get_db_session() as db:
            user = db.query(User).filter_by(id=user_id, is_active=True).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Check friendship status
            friendship = db.query(FriendRequest).filter(
                or_(
                    and_(FriendRequest.sender_id == current_user_id,
                         FriendRequest.receiver_id == user_id),
                    and_(FriendRequest.sender_id == user_id,
                         FriendRequest.receiver_id == current_user_id)
                ),
                FriendRequest.status == 'accepted'
            ).first()
            is_friend = friendship is not None

            # Get user's practice stats
            total_sessions = db.query(func.count(Exercise.id)).filter(
                Exercise.user_id == user_id
            ).scalar() or 0

            total_practice_time = db.query(func.sum(Exercise.duration_minutes)).filter(
                Exercise.user_id == user_id
            ).scalar() or 0

            avg_accuracy = db.query(func.avg(Exercise.accuracy_score)).filter(
                Exercise.user_id == user_id
            ).scalar() or 0.0

            # Get achievement count
            achievement_count = db.query(func.count(Achievement.id)).filter(
                Achievement.user_id == user_id
            ).scalar() or 0

            # Get recent achievements (public)
            recent_achievements = db.query(Achievement).filter(
                Achievement.user_id == user_id
            ).order_by(desc(Achievement.earned_date)).limit(5).all()

            # Get mutual friends count
            current_user_friends = db.query(FriendRequest).filter(
                or_(
                    FriendRequest.sender_id == current_user_id,
                    FriendRequest.receiver_id == current_user_id
                ),
                FriendRequest.status == 'accepted'
            ).all()

            current_friend_ids = set()
            for fr in current_user_friends:
                if fr.sender_id == current_user_id:
                    current_friend_ids.add(fr.receiver_id)
                else:
                    current_friend_ids.add(fr.sender_id)

            target_user_friends = db.query(FriendRequest).filter(
                or_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.receiver_id == user_id
                ),
                FriendRequest.status == 'accepted'
            ).all()

            target_friend_ids = set()
            for fr in target_user_friends:
                if fr.sender_id == user_id:
                    target_friend_ids.add(fr.receiver_id)
                else:
                    target_friend_ids.add(fr.sender_id)

            mutual_friends = current_friend_ids.intersection(target_friend_ids)

            return jsonify({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'is_friend': is_friend,
                'member_since': user.created_at.isoformat() if user.created_at else None,
                'stats': {
                    'total_sessions': total_sessions,
                    'total_practice_minutes': round(total_practice_time, 1),
                    'average_accuracy': round(avg_accuracy, 2),
                    'achievement_count': achievement_count
                },
                'recent_achievements': [
                    {
                        'name': ach.name,
                        'icon': ach.icon,
                        'earned_date': ach.earned_date.isoformat()
                    } for ach in recent_achievements
                ],
                'mutual_friends_count': len(mutual_friends)
            })

    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get user profile'}), 500


# ============================================================================
# Activity Feed
# ============================================================================

@social_bp.route('/feed', methods=['GET'])
def get_activity_feed():
    """
    Get activity feed showing recent activities from friends and self.

    Query Params:
        limit: Max items (default 20, max 50)
        offset: Pagination offset
        include_self: Include own activities (default true)
    """
    current_user_id = session.get('user_id', 1)
    limit = min(int(request.args.get('limit', 20)), 50)
    offset = int(request.args.get('offset', 0))
    include_self = request.args.get('include_self', 'true').lower() == 'true'

    try:
        with get_db_session() as db:
            # Get friend IDs
            friendships = db.query(FriendRequest).filter(
                or_(
                    FriendRequest.sender_id == current_user_id,
                    FriendRequest.receiver_id == current_user_id
                ),
                FriendRequest.status == 'accepted'
            ).all()

            friend_ids = []
            for fr in friendships:
                if fr.sender_id == current_user_id:
                    friend_ids.append(fr.receiver_id)
                else:
                    friend_ids.append(fr.sender_id)

            relevant_user_ids = friend_ids.copy()
            if include_self:
                relevant_user_ids.append(current_user_id)

            if not relevant_user_ids:
                return jsonify({
                    'activities': [],
                    'count': 0,
                    'offset': offset,
                    'limit': limit
                })

            activities = []

            # Get recent practice sessions
            recent_exercises = db.query(Exercise).filter(
                Exercise.user_id.in_(relevant_user_ids)
            ).order_by(desc(Exercise.started_at)).limit(limit * 2).all()

            for exercise in recent_exercises:
                user = db.query(User).filter_by(id=exercise.user_id).first()
                if user:
                    activities.append({
                        'type': ActivityType.PRACTICE_SESSION,
                        'user_id': user.id,
                        'username': user.username,
                        'timestamp': exercise.started_at.isoformat() if exercise.started_at else None,
                        'data': {
                            'module': exercise.module,
                            'duration_minutes': exercise.duration_minutes,
                            'accuracy_score': exercise.accuracy_score
                        }
                    })

            # Get recent achievements
            recent_achievements = db.query(Achievement).filter(
                Achievement.user_id.in_(relevant_user_ids)
            ).order_by(desc(Achievement.earned_date)).limit(limit).all()

            for ach in recent_achievements:
                user = db.query(User).filter_by(id=ach.user_id).first()
                if user:
                    activities.append({
                        'type': ActivityType.ACHIEVEMENT_EARNED,
                        'user_id': user.id,
                        'username': user.username,
                        'timestamp': ach.earned_date.isoformat(),
                        'data': {
                            'achievement_name': ach.name,
                            'icon': ach.icon,
                            'points': ach.points
                        }
                    })

            # Get recent friendships (for current user only)
            recent_friendships = db.query(FriendRequest).filter(
                or_(
                    FriendRequest.sender_id == current_user_id,
                    FriendRequest.receiver_id == current_user_id
                ),
                FriendRequest.status == 'accepted',
                FriendRequest.responded_at != None
            ).order_by(desc(FriendRequest.responded_at)).limit(10).all()

            for fr in recent_friendships:
                other_user_id = fr.receiver_id if fr.sender_id == current_user_id else fr.sender_id
                other_user = db.query(User).filter_by(id=other_user_id).first()
                if other_user:
                    activities.append({
                        'type': ActivityType.FRIEND_ADDED,
                        'user_id': current_user_id,
                        'username': 'You',
                        'timestamp': fr.responded_at.isoformat() if fr.responded_at else None,
                        'data': {
                            'friend_id': other_user.id,
                            'friend_username': other_user.username
                        }
                    })

            # Sort all activities by timestamp
            activities.sort(
                key=lambda x: x['timestamp'] if x['timestamp'] else '1970-01-01',
                reverse=True
            )

            # Apply pagination
            paginated = activities[offset:offset + limit]

            return jsonify({
                'activities': paginated,
                'count': len(paginated),
                'total': len(activities),
                'offset': offset,
                'limit': limit
            })

    except Exception as e:
        current_app.logger.error(f"Error getting activity feed: {e}")
        return jsonify({'error': 'Failed to get activity feed'}), 500


# ============================================================================
# Leaderboards
# ============================================================================

@social_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Get leaderboard rankings.

    Query Params:
        type: Leaderboard type ('accuracy', 'practice_time', 'achievements', 'streak')
        scope: 'global', 'friends', or 'weekly'
        limit: Max results (default 20, max 100)
    """
    leaderboard_type = request.args.get('type', 'accuracy')
    scope = request.args.get('scope', 'global')
    limit = min(int(request.args.get('limit', 20)), 100)
    current_user_id = session.get('user_id', 1)

    valid_types = ['accuracy', 'practice_time', 'achievements', 'streak']
    if leaderboard_type not in valid_types:
        return jsonify({'error': f'Invalid type. Valid: {valid_types}'}), 400

    try:
        with get_db_session() as db:
            # Determine user filter based on scope
            user_filter = None
            if scope == 'friends':
                friendships = db.query(FriendRequest).filter(
                    or_(
                        FriendRequest.sender_id == current_user_id,
                        FriendRequest.receiver_id == current_user_id
                    ),
                    FriendRequest.status == 'accepted'
                ).all()

                friend_ids = [current_user_id]
                for fr in friendships:
                    if fr.sender_id == current_user_id:
                        friend_ids.append(fr.receiver_id)
                    else:
                        friend_ids.append(fr.sender_id)
                user_filter = friend_ids

            # Time filter for weekly scope
            time_filter = None
            if scope == 'weekly':
                time_filter = datetime.now(timezone.utc) - timedelta(days=7)

            rankings = []

            if leaderboard_type == 'accuracy':
                # Rank by average accuracy
                query = db.query(
                    Exercise.user_id,
                    func.avg(Exercise.accuracy_score).label('avg_accuracy'),
                    func.count(Exercise.id).label('session_count')
                ).group_by(Exercise.user_id)

                if user_filter:
                    query = query.filter(Exercise.user_id.in_(user_filter))
                if time_filter:
                    query = query.filter(Exercise.started_at >= time_filter)

                # Require minimum sessions for ranking
                results = query.having(func.count(Exercise.id) >= 5).order_by(
                    desc('avg_accuracy')
                ).limit(limit).all()

                for rank, (user_id, avg_acc, sessions) in enumerate(results, 1):
                    user = db.query(User).filter_by(id=user_id).first()
                    if user:
                        rankings.append({
                            'rank': rank,
                            'user_id': user.id,
                            'username': user.username,
                            'value': round(avg_acc, 2),
                            'session_count': sessions,
                            'is_current_user': user.id == current_user_id
                        })

            elif leaderboard_type == 'practice_time':
                # Rank by total practice time
                query = db.query(
                    Exercise.user_id,
                    func.sum(Exercise.duration_minutes).label('total_time'),
                    func.count(Exercise.id).label('session_count')
                ).group_by(Exercise.user_id)

                if user_filter:
                    query = query.filter(Exercise.user_id.in_(user_filter))
                if time_filter:
                    query = query.filter(Exercise.started_at >= time_filter)

                results = query.order_by(desc('total_time')).limit(limit).all()

                for rank, (user_id, total_time, sessions) in enumerate(results, 1):
                    user = db.query(User).filter_by(id=user_id).first()
                    if user:
                        rankings.append({
                            'rank': rank,
                            'user_id': user.id,
                            'username': user.username,
                            'value': round(total_time, 1),
                            'session_count': sessions,
                            'is_current_user': user.id == current_user_id
                        })

            elif leaderboard_type == 'achievements':
                # Rank by achievement points
                query = db.query(
                    Achievement.user_id,
                    func.sum(Achievement.points).label('total_points'),
                    func.count(Achievement.id).label('achievement_count')
                ).group_by(Achievement.user_id)

                if user_filter:
                    query = query.filter(Achievement.user_id.in_(user_filter))
                if time_filter:
                    query = query.filter(Achievement.earned_date >= time_filter)

                results = query.order_by(desc('total_points')).limit(limit).all()

                for rank, (user_id, total_points, count) in enumerate(results, 1):
                    user = db.query(User).filter_by(id=user_id).first()
                    if user:
                        rankings.append({
                            'rank': rank,
                            'user_id': user.id,
                            'username': user.username,
                            'value': total_points or 0,
                            'achievement_count': count,
                            'is_current_user': user.id == current_user_id
                        })

            elif leaderboard_type == 'streak':
                # Calculate current practice streaks
                all_users = db.query(User).filter_by(is_active=True)
                if user_filter:
                    all_users = all_users.filter(User.id.in_(user_filter))
                all_users = all_users.all()

                streak_data = []
                for user in all_users:
                    exercises = db.query(Exercise).filter(
                        Exercise.user_id == user.id
                    ).order_by(desc(Exercise.started_at)).all()

                    if not exercises:
                        continue

                    # Calculate current streak
                    current_streak = 0
                    today = datetime.now(timezone.utc).date()

                    practice_dates = set()
                    for ex in exercises:
                        if ex.started_at:
                            practice_dates.add(ex.started_at.date())

                    check_date = today
                    while check_date in practice_dates:
                        current_streak += 1
                        check_date -= timedelta(days=1)

                    if current_streak > 0:
                        streak_data.append({
                            'user': user,
                            'streak': current_streak,
                            'last_practice': max(practice_dates) if practice_dates else None
                        })

                streak_data.sort(key=lambda x: x['streak'], reverse=True)

                for rank, item in enumerate(streak_data[:limit], 1):
                    rankings.append({
                        'rank': rank,
                        'user_id': item['user'].id,
                        'username': item['user'].username,
                        'value': item['streak'],
                        'last_practice': item['last_practice'].isoformat() if item['last_practice'] else None,
                        'is_current_user': item['user'].id == current_user_id
                    })

            # Find current user's rank if not in top results
            current_user_rank = None
            for r in rankings:
                if r['is_current_user']:
                    current_user_rank = r['rank']
                    break

            return jsonify({
                'type': leaderboard_type,
                'scope': scope,
                'rankings': rankings,
                'current_user_rank': current_user_rank,
                'total_participants': len(rankings)
            })

    except Exception as e:
        current_app.logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to get leaderboard'}), 500


# ============================================================================
# Practice Challenges
# ============================================================================

@social_bp.route('/challenges', methods=['GET'])
def get_challenges():
    """Get all challenges the current user is participating in."""
    current_user_id = session.get('user_id', 1)

    user_challenges = []
    for challenge_id, challenge in _active_challenges.items():
        if current_user_id in challenge.participants or challenge.creator_id == current_user_id:
            user_challenges.append({
                'challenge_id': challenge.challenge_id,
                'type': challenge.challenge_type,
                'target_value': challenge.target_value,
                'start_date': challenge.start_date.isoformat(),
                'end_date': challenge.end_date.isoformat(),
                'status': challenge.status,
                'participant_count': len(challenge.participants),
                'is_creator': challenge.creator_id == current_user_id,
                'my_progress': challenge.results.get(current_user_id, 0)
            })

    return jsonify({
        'challenges': user_challenges,
        'count': len(user_challenges)
    })


@social_bp.route('/challenges', methods=['POST'])
def create_challenge():
    """
    Create a new practice challenge.

    Body:
        challenge_type: 'accuracy', 'duration', 'streak', 'shruti_mastery'
        target_value: Target value to achieve
        duration_days: Challenge duration in days (1-30)
        invite_friends: List of friend IDs to invite (optional)
    """
    current_user_id = session.get('user_id', 1)
    data = request.get_json() or {}

    challenge_type = data.get('challenge_type', 'accuracy')
    target_value = data.get('target_value', 90.0)
    duration_days = min(max(data.get('duration_days', 7), 1), 30)
    invite_friends = data.get('invite_friends', [])

    valid_types = ['accuracy', 'duration', 'streak', 'shruti_mastery']
    if challenge_type not in valid_types:
        return jsonify({'error': f'Invalid challenge type. Valid: {valid_types}'}), 400

    try:
        challenge_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc)

        challenge = PracticeChallenge(
            challenge_id=challenge_id,
            creator_id=current_user_id,
            challenge_type=challenge_type,
            target_value=target_value,
            start_date=now,
            end_date=now + timedelta(days=duration_days),
            participants=[current_user_id] + invite_friends,
            status=ChallengeStatus.ACTIVE
        )

        _active_challenges[challenge_id] = challenge

        return jsonify({
            'message': 'Challenge created successfully',
            'challenge_id': challenge_id,
            'type': challenge_type,
            'target_value': target_value,
            'start_date': challenge.start_date.isoformat(),
            'end_date': challenge.end_date.isoformat(),
            'participants': challenge.participants
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error creating challenge: {e}")
        return jsonify({'error': 'Failed to create challenge'}), 500


@social_bp.route('/challenges/<challenge_id>', methods=['GET'])
def get_challenge_details(challenge_id: str):
    """Get detailed information about a specific challenge."""
    current_user_id = session.get('user_id', 1)

    challenge = _active_challenges.get(challenge_id)
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    if current_user_id not in challenge.participants and challenge.creator_id != current_user_id:
        return jsonify({'error': 'Not authorized to view this challenge'}), 403

    try:
        with get_db_session() as db:
            # Get participant details
            participants_info = []
            for participant_id in challenge.participants:
                user = db.query(User).filter_by(id=participant_id).first()
                if user:
                    participants_info.append({
                        'user_id': user.id,
                        'username': user.username,
                        'progress': challenge.results.get(participant_id, 0),
                        'completed': challenge.results.get(participant_id, 0) >= challenge.target_value
                    })

            # Sort by progress
            participants_info.sort(key=lambda x: x['progress'], reverse=True)

            return jsonify({
                'challenge_id': challenge.challenge_id,
                'type': challenge.challenge_type,
                'target_value': challenge.target_value,
                'start_date': challenge.start_date.isoformat(),
                'end_date': challenge.end_date.isoformat(),
                'status': challenge.status,
                'creator_id': challenge.creator_id,
                'participants': participants_info,
                'my_progress': challenge.results.get(current_user_id, 0),
                'time_remaining': max(0, (challenge.end_date - datetime.now(timezone.utc)).total_seconds())
            })

    except Exception as e:
        current_app.logger.error(f"Error getting challenge details: {e}")
        return jsonify({'error': 'Failed to get challenge details'}), 500


@social_bp.route('/challenges/<challenge_id>/join', methods=['POST'])
def join_challenge(challenge_id: str):
    """Join an existing challenge."""
    current_user_id = session.get('user_id', 1)

    challenge = _active_challenges.get(challenge_id)
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    if challenge.status != ChallengeStatus.ACTIVE:
        return jsonify({'error': 'Challenge is not active'}), 400

    if current_user_id in challenge.participants:
        return jsonify({'error': 'Already participating in this challenge'}), 409

    challenge.participants.append(current_user_id)
    challenge.results[current_user_id] = 0

    return jsonify({
        'message': 'Successfully joined challenge',
        'challenge_id': challenge_id
    })


@social_bp.route('/challenges/<challenge_id>/progress', methods=['POST'])
def update_challenge_progress(challenge_id: str):
    """
    Update progress in a challenge.

    Body:
        progress_value: Current progress value
    """
    current_user_id = session.get('user_id', 1)
    data = request.get_json() or {}

    challenge = _active_challenges.get(challenge_id)
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    if current_user_id not in challenge.participants:
        return jsonify({'error': 'Not participating in this challenge'}), 403

    if challenge.status != ChallengeStatus.ACTIVE:
        return jsonify({'error': 'Challenge is not active'}), 400

    progress_value = data.get('progress_value', 0)
    challenge.results[current_user_id] = max(
        challenge.results.get(current_user_id, 0),
        progress_value
    )

    completed = challenge.results[current_user_id] >= challenge.target_value

    return jsonify({
        'message': 'Progress updated',
        'current_progress': challenge.results[current_user_id],
        'target_value': challenge.target_value,
        'completed': completed
    })


# ============================================================================
# Group Management (Enhanced)
# ============================================================================

@social_bp.route('/groups', methods=['POST'])
def create_group():
    """
    Create a new practice group.

    Body:
        name: Group name (required)
        description: Group description
        type: 'study', 'competition', 'casual' (default: 'casual')
        is_public: Whether group is publicly visible (default: true)
        max_members: Maximum members (default: 50, max: 100)
    """
    current_user_id = session.get('user_id', 1)
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    if not name or len(name) < 3:
        return jsonify({'error': 'Group name must be at least 3 characters'}), 400

    description = data.get('description', '')
    group_type = data.get('type', 'casual')
    is_public = data.get('is_public', True)
    max_members = min(data.get('max_members', 50), 100)

    valid_types = ['study', 'competition', 'casual']
    if group_type not in valid_types:
        return jsonify({'error': f'Invalid group type. Valid: {valid_types}'}), 400

    try:
        with get_db_session() as db:
            # Check if group name already exists
            existing = db.query(Group).filter_by(name=name).first()
            if existing:
                return jsonify({'error': 'A group with this name already exists'}), 409

            # Generate unique join code
            join_code = secrets.token_urlsafe(6)

            new_group = Group(
                name=name,
                description=description,
                type=group_type,
                is_public=is_public,
                max_members=max_members,
                member_count=1,  # Creator is first member
                created_by=current_user_id,
                join_code=join_code,
                is_active=True
            )

            db.add(new_group)
            db.commit()

            return jsonify({
                'message': 'Group created successfully',
                'group': {
                    'id': new_group.id,
                    'name': new_group.name,
                    'description': new_group.description,
                    'type': new_group.type,
                    'is_public': new_group.is_public,
                    'max_members': new_group.max_members,
                    'join_code': new_group.join_code,
                    'created_at': new_group.created_at.isoformat()
                }
            }), 201

    except IntegrityError:
        return jsonify({'error': 'Failed to create group - name may already exist'}), 409
    except Exception as e:
        current_app.logger.error(f"Error creating group: {e}")
        return jsonify({'error': 'Failed to create group'}), 500


@social_bp.route('/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id: int):
    """
    Update group settings (creator only).

    Body:
        name: New group name
        description: New description
        is_public: Update visibility
        max_members: Update max members
    """
    current_user_id = session.get('user_id', 1)
    data = request.get_json() or {}

    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(id=group_id, is_active=True).first()
            if not group:
                return jsonify({'error': 'Group not found'}), 404

            if group.created_by != current_user_id:
                return jsonify({'error': 'Only the group creator can update settings'}), 403

            if 'name' in data:
                name = data['name'].strip()
                if len(name) >= 3:
                    group.name = name

            if 'description' in data:
                group.description = data['description']

            if 'is_public' in data:
                group.is_public = bool(data['is_public'])

            if 'max_members' in data:
                new_max = min(data['max_members'], 100)
                if new_max >= group.member_count:
                    group.max_members = new_max

            group.updated_at = datetime.now(timezone.utc)
            db.commit()

            return jsonify({
                'message': 'Group updated successfully',
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'is_public': group.is_public,
                    'max_members': group.max_members,
                    'updated_at': group.updated_at.isoformat()
                }
            })

    except Exception as e:
        current_app.logger.error(f"Error updating group: {e}")
        return jsonify({'error': 'Failed to update group'}), 500


@social_bp.route('/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id: int):
    """Delete a group (creator only)."""
    current_user_id = session.get('user_id', 1)

    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(id=group_id).first()
            if not group:
                return jsonify({'error': 'Group not found'}), 404

            if group.created_by != current_user_id:
                return jsonify({'error': 'Only the group creator can delete the group'}), 403

            # Soft delete
            group.is_active = False
            group.updated_at = datetime.now(timezone.utc)
            db.commit()

            return jsonify({'message': 'Group deleted successfully'})

    except Exception as e:
        current_app.logger.error(f"Error deleting group: {e}")
        return jsonify({'error': 'Failed to delete group'}), 500


@social_bp.route('/groups/join/<join_code>', methods=['POST'])
def join_group_by_code(join_code: str):
    """Join a group using its unique join code."""
    current_user_id = session.get('user_id', 1)

    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(join_code=join_code, is_active=True).first()
            if not group:
                return jsonify({'error': 'Invalid join code'}), 404

            if group.member_count >= group.max_members:
                return jsonify({'error': 'Group is full'}), 400

            # In production, check if user is already a member via GroupMembership table
            group.member_count += 1
            db.commit()

            return jsonify({
                'message': f'Successfully joined group {group.name}',
                'group_id': group.id
            })

    except Exception as e:
        current_app.logger.error(f"Error joining group by code: {e}")
        return jsonify({'error': 'Failed to join group'}), 500


@social_bp.route('/groups/my', methods=['GET'])
def get_my_groups():
    """Get groups the current user has created or joined."""
    current_user_id = session.get('user_id', 1)

    try:
        with get_db_session() as db:
            # Get groups created by user
            created_groups = db.query(Group).filter_by(
                created_by=current_user_id,
                is_active=True
            ).all()

            # In production, also query GroupMembership table for joined groups
            # For now, just return created groups

            return jsonify({
                'created_groups': [
                    {
                        'id': g.id,
                        'name': g.name,
                        'description': g.description,
                        'type': g.type,
                        'member_count': g.member_count,
                        'is_creator': True
                    } for g in created_groups
                ],
                'joined_groups': []  # Would be populated from GroupMembership
            })

    except Exception as e:
        current_app.logger.error(f"Error getting user groups: {e}")
        return jsonify({'error': 'Failed to get groups'}), 500


@social_bp.route('/groups', methods=['GET'])
def get_groups():
    """Get available practice groups"""
    try:
        with get_db_session() as db:
            groups = db.query(Group).filter_by(is_active=True).all()
            return jsonify([
                {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'type': group.type,
                    'member_count': group.member_count,
                    'is_public': group.is_public,
                    'created_by': group.created_by,
                    'created_at': group.created_at.isoformat()
                } for group in groups
            ])
    except Exception as e:
        current_app.logger.error(f"Error getting groups: {e}")
        return jsonify({'error': 'Failed to retrieve groups'}), 500


@social_bp.route('/groups/<int:group_id>', methods=['GET'])
def get_group_details(group_id: int):
    """Get details of a specific group"""
    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(id=group_id, is_active=True).first()
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            
            return jsonify({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'type': group.type,
                'member_count': group.member_count,
                'max_members': group.max_members,
                'is_public': group.is_public,
                'created_by': group.created_by,
                'join_code': group.join_code,
                'created_at': group.created_at.isoformat(),
                'updated_at': group.updated_at.isoformat()
            })
    except Exception as e:
        current_app.logger.error(f"Error getting group details: {e}")
        return jsonify({'error': 'Failed to retrieve group details'}), 500


@social_bp.route('/groups/<int:group_id>/join', methods=['POST'])
def join_group(group_id: int):
    """Join a specific group"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(id=group_id, is_active=True).first()
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Assuming a GroupMembership table or direct user-group relationship
            # For now, just increment member count (to be replaced by actual membership logic)
            if group.member_count >= group.max_members:
                return jsonify({'error': 'Group is full'}), 400

            # This is a simplification; ideally, there would be a many-to-many relationship
            # or a GroupMembership model to track actual members.
            group.member_count += 1
            db.add(group)
            db.commit()
            
            return jsonify({'message': f'Successfully joined group {group.name}'}), 200
    except Exception as e:
        current_app.logger.error(f"Error joining group {group_id}: {e}")
        return jsonify({'error': 'Failed to join group'}), 500


@social_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
def leave_group(group_id: int):
    """Leave a specific group"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            group = db.query(Group).filter_by(id=group_id, is_active=True).first()
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Assuming a GroupMembership table or direct user-group relationship
            # For now, just decrement member count
            if group.member_count > 0:
                group.member_count -= 1
                db.add(group)
                db.commit()
            
            return jsonify({'message': f'Successfully left group {group.name}'}), 200
    except Exception as e:
        current_app.logger.error(f"Error leaving group {group_id}: {e}")
        return jsonify({'error': 'Failed to leave group'}), 500


@social_bp.route('/friends', methods=['GET'])
def get_friends():
    """Get list of user's accepted friends"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            # Find accepted friend requests where current user is sender or receiver
            friendships = db.query(FriendRequest).filter(
                (FriendRequest.sender_id == user_id) | (FriendRequest.receiver_id == user_id),
                FriendRequest.status == 'accepted'
            ).all()
            
            friend_ids = []
            for fr in friendships:
                if fr.sender_id == user_id:
                    friend_ids.append(fr.receiver_id)
                else:
                    friend_ids.append(fr.sender_id)
            
            friends = db.query(User).filter(User.id.in_(friend_ids)).all()
            
            return jsonify([
                {
                    'id': friend.id,
                    'username': friend.username,
                    'full_name': friend.full_name,
                    'email': friend.email # Potentially restrict
                } for friend in friends
            ])
    except Exception as e:
        current_app.logger.error(f"Error getting friends for user {user_id}: {e}")
        return jsonify({'error': 'Failed to retrieve friends'}), 500


@social_bp.route('/friends/<int:target_user_id>', methods=['POST'])
def send_friend_request(target_user_id: int):
    """Send a friend request to another user"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    if user_id == target_user_id:
        return jsonify({'error': 'Cannot send friend request to yourself'}), 400
    
    try:
        with get_db_session() as db:
            target_user = db.query(User).filter_by(id=target_user_id).first()
            if not target_user:
                return jsonify({'error': 'Target user not found'}), 404
            
            # Check if request already exists (pending or accepted)
            existing_request = db.query(FriendRequest).filter(
                ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == target_user_id)) |
                ((FriendRequest.sender_id == target_user_id) & (FriendRequest.receiver_id == user_id)),
            ).first()
            
            if existing_request:
                if existing_request.status == 'pending':
                    return jsonify({'error': 'Friend request already sent or received'}), 409
                elif existing_request.status == 'accepted':
                    return jsonify({'error': 'Already friends with this user'}), 409
            
            new_request = FriendRequest(
                sender_id=user_id,
                receiver_id=target_user_id,
                status='pending'
            )
            db.add(new_request)
            db.commit()
            
            return jsonify({
                'message': 'Friend request sent successfully',
                'request_id': new_request.id,
                'status': 'pending'
            }), 201
            
    except Exception as e:
        current_app.logger.error(f"Error sending friend request from {user_id} to {target_user_id}: {e}")
        return jsonify({'error': 'Failed to send friend request'}), 500


@social_bp.route('/friend_requests', methods=['GET'])
def get_pending_friend_requests():
    """Get pending friend requests for the current user"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            pending_requests = db.query(FriendRequest).filter_by(
                receiver_id=user_id,
                status='pending'
            ).all()
            
            requests_data = []
            for fr in pending_requests:
                sender = db.query(User).filter_by(id=fr.sender_id).first()
                if sender:
                    requests_data.append({
                        'request_id': fr.id,
                        'sender_id': fr.sender_id,
                        'sender_username': sender.username,
                        'sent_at': fr.sent_at.isoformat()
                    })
            return jsonify(requests_data)
            
    except Exception as e:
        current_app.logger.error(f"Error getting pending friend requests for user {user_id}: {e}")
        return jsonify({'error': 'Failed to retrieve friend requests'}), 500


@social_bp.route('/friend_requests/<int:request_id>/accept', methods=['POST'])
def accept_friend_request(request_id: int):
    """Accept a pending friend request"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            friend_request = db.query(FriendRequest).filter_by(id=request_id, receiver_id=user_id).first()
            
            if not friend_request:
                return jsonify({'error': 'Friend request not found or not for current user'}), 404
            
            if friend_request.status != 'pending':
                return jsonify({'error': f'Friend request already {friend_request.status}'}), 400
            
            friend_request.status = 'accepted'
            friend_request.responded_at = datetime.now(timezone.utc)
            db.add(friend_request)
            db.commit()
            
            return jsonify({'message': 'Friend request accepted'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Error accepting friend request {request_id} for user {user_id}: {e}")
        return jsonify({'error': 'Failed to accept friend request'}), 500


@social_bp.route('/friend_requests/<int:request_id>/decline', methods=['POST'])
def decline_friend_request(request_id: int):
    """Decline a pending friend request"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            friend_request = db.query(FriendRequest).filter_by(id=request_id, receiver_id=user_id).first()
            
            if not friend_request:
                return jsonify({'error': 'Friend request not found or not for current user'}), 404
            
            if friend_request.status != 'pending':
                return jsonify({'error': f'Friend request already {friend_request.status}'}), 400
            
            friend_request.status = 'declined'
            friend_request.responded_at = datetime.now(timezone.utc)
            db.add(friend_request)
            db.commit()
            
            return jsonify({'message': 'Friend request declined'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Error declining friend request {request_id} for user {user_id}: {e}")
        return jsonify({'error': 'Failed to decline friend request'}), 500


@social_bp.route('/friends/<int:target_user_id>', methods=['DELETE'])
def remove_friend(target_user_id: int):
    """Remove an existing friend connection"""
    user_id = session.get('user_id', 1)  # Placeholder
    
    try:
        with get_db_session() as db:
            # Find the accepted friend request between the two users
            friend_request = db.query(FriendRequest).filter(
                ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == target_user_id)) |
                ((FriendRequest.sender_id == target_user_id) & (FriendRequest.receiver_id == user_id)),
                FriendRequest.status == 'accepted'
            ).first()
            
            if not friend_request:
                return jsonify({'error': 'Friendship not found'}), 404
            
            # Delete the friend request record (effectively ending the friendship)
            db.delete(friend_request)
            db.commit()
            
            return jsonify({'message': 'Friend removed successfully'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Error removing friend {target_user_id} for user {user_id}: {e}")
        return jsonify({'error': 'Failed to remove friend'}), 500