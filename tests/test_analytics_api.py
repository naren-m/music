"""
Tests for the Analytics API endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, MagicMock
import os
import json
import random
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import User, Progress, Exercise, Group, FriendRequest, get_db_session, init_db_with_flask, db_manager, Base, DatabaseConfig
from api import create_app
from api.analytics.dashboard import AdvancedAnalytics, AnalyticsPeriod

class TestDatabaseConfig(DatabaseConfig):
    """Test-specific database configuration for in-memory SQLite."""
    postgresql_host: str = 'sqlite'
    postgresql_db: str = ':memory:'
    postgresql_user: str = 'test'
    postgresql_password: str = 'test'
    pool_size: int = None
    max_overflow: int = None
    pool_timeout: int = None
    pool_recycle: int = None

@pytest.fixture(scope="session")
def app_with_db():
    """Create Flask application for testing with a fresh in-memory SQLite DB."""
    os.environ['SECRET_KEY'] = 'test-secret-key-for-env' # Set environment variable for testing
    app, _ = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', # Explicitly set SQLite in-memory DB
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'a-super-secret-key-for-testing', # Set a dummy secret key
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {'connect_args': {'check_same_thread': False}} # SQLite specific for threading
    })

    with app.app_context():
        # Store original db_manager state to restore later
        original_db_manager_config = db_manager.config
        original_db_manager_engine = db_manager.engine
        original_db_manager_session_factory = db_manager.session_factory
        
        # Create a mock db_manager instance and configure it for SQLite
        mock_db_manager_instance = MagicMock()
        mock_db_manager_instance.config = TestDatabaseConfig()
        
        # Define the side effect for initialize_postgresql
        def mock_init_postgresql():
            mock_db_manager_instance.engine = create_engine(
                'sqlite:///:memory:', connect_args={'check_same_thread': False}
            )
            mock_db_manager_instance.session_factory = sessionmaker(bind=mock_db_manager_instance.engine)
        
        mock_db_manager_instance.initialize_postgresql.side_effect = mock_init_postgresql
        
        # Patch the global db_manager with our mock instance
        with patch('config.database.db_manager', new=mock_db_manager_instance):
            # Now call the mocked initialize (which sets up engine/session_factory on the mock)
            mock_db_manager_instance.initialize_postgresql()

            # Initialize Flask-SQLAlchemy extension with the app
            db = init_db_with_flask(app)
            
            db.create_all() # Create tables using Flask-SQLAlchemy
            
            yield app
            
            # Teardown
            db.session.remove() # Important for Flask-SQLAlchemy session management
            db.drop_all() # Drop tables using Flask-SQLAlchemy

        # Restore original db_manager state
        db_manager.config = original_db_manager_config
        db_manager.engine = original_db_manager_engine
        db_manager.session_factory = original_db_manager_session_factory

@pytest.fixture(scope="function")
def client(app_with_db):
    """Create Flask test client."""
    return app_with_db.test_client()

@pytest.fixture(scope="function")
def db_session(app_with_db):
    """Provide a transactional test database session."""
    # Use the session provided by Flask-SQLAlchemy
    with app_with_db.app_context():
        connection = app_with_db.extensions['sqlalchemy'].db.engine.connect()
        transaction = connection.begin()
        # Bind a session to this connection
        session = app_with_db.extensions['sqlalchemy'].db.session_factory(bind=connection)

        # Patch get_db_session to return our test session
        with patch('config.database.get_db_session') as mock_get_db_session:
            mock_get_db_session.return_value.__enter__.return_value = session
            mock_get_db_session.return_value.__exit__.return_value = None # Ensure context manager exits cleanly
            yield session
        
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def sample_user(db_session):
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        full_name="Test User",
        created_at=datetime.now(timezone.utc) - timedelta(days=30)
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_exercise(db_session):
    exercise = Exercise(
        id=101,
        type="swara",
        category="basic",
        difficulty_level=1,
        title="Basic Sa Practice",
        description="Practice the root note Sa",
        content_data={},
        created_at=datetime.now(timezone.utc) - timedelta(days=30)
    )
    db_session.add(exercise)
    db_session.commit()
    return exercise

@pytest.fixture
def sample_progress_data(db_session, sample_user, sample_exercise):
    progress_list = []
    for i in range(10):
        # Create a streak of 5 days leading up to today
        if i >= 5:
            created_at_date = datetime.now(timezone.utc) - timedelta(days=9 - i) # Use actual dates for the first 5
        else:
            created_at_date = datetime.now(timezone.utc) - timedelta(days=4 - i) # Consecutive days for the last 5
        
        progress = Progress(
            user_id=sample_user.id,
            exercise_id=sample_exercise.id,
            completion_percentage=0.5 + (i * 0.05),
            accuracy_metrics={'cent_deviation': random.uniform(5, 20), 'target_swara': 'Sa'},
            practice_time=600 + (i * 30),
            attempt_count=i + 1,
            average_accuracy=0.6 + (i * 0.03),
            best_accuracy=0.7 + (i * 0.02),
            created_at=created_at_date,
            last_practiced=created_at_date,
            streak_days=i+1,
            total_sessions=i+1
        )
        progress_list.append(progress)
        db_session.add(progress)
    db_session.commit()
    return progress_list

def test_get_dashboard_empty_data(client, db_session, sample_user):
    """Test fetching a dashboard for a user with no progress data."""
    response = client.get(f"/api/v1/analytics/dashboard/{sample_user.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data['user_id'] == sample_user.id
    assert data['period'] == 'monthly'
    assert not data['performance_metrics']
    assert "You haven't practiced recently. Regular practice is key to improvement." in data['learning_insights'][0]['description'] # Assuming default empty insight

def test_get_dashboard_with_data(client, db_session, sample_user, sample_progress_data):
    """Test fetching a dashboard for a user with progress data."""
    response = client.get(f"/api/v1/analytics/dashboard/{sample_user.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data['user_id'] == sample_user.id
    assert data['period'] == 'monthly'
    assert len(data['performance_metrics']) > 0
    assert len(data['learning_insights']) > 0
    assert data['streak_analysis']['current_streak'] > 0
    
    # Check a specific metric
    accuracy_metric = next((m for m in data['performance_metrics'] if m['metric_name'] == 'Average Accuracy'), None)
    assert accuracy_metric is not None
    assert accuracy_metric['current_value'] > 0

def test_get_dashboard_invalid_period(client):
    """Test fetching a dashboard with an invalid period parameter."""
    response = client.get("/api/v1/analytics/dashboard/1?period=invalid")
    assert response.status_code == 400
    assert "Invalid period specified" in response.get_json()['error']

def test_get_metrics(client, db_session, sample_user, sample_progress_data):
    """Test fetching performance metrics."""
    response = client.get(f"/api/v1/analytics/metrics/{sample_user.id}?period=weekly")
    assert response.status_code == 200
    metrics = response.get_json()
    assert len(metrics) > 0
    assert next((m for m in metrics if m['metric_name'] == 'Average Accuracy'), None) is not None

def test_get_insights(client, db_session, sample_user, sample_progress_data):
    """Test fetching learning insights."""
    response = client.get(f"/api/v1/analytics/insights/{sample_user.id}")
    assert response.status_code == 200
    insights = response.get_json()
    assert len(insights) > 0
    assert insights[0]['category'] == 'Consistency' # Assuming default insight for no recent data is not returned due to existing data.

def test_get_swara_performance(client, db_session, sample_user, sample_progress_data):
    """Test fetching swara performance analysis."""
    response = client.get(f"/api/v1/analytics/swara-performance/{sample_user.id}")
    assert response.status_code == 200
    swara_analysis = response.get_json()
    # This will be empty because sample_progress_data doesn't have 'target_swara' in exercise_data
    assert len(swara_analysis) == 0

# Test for other analytics endpoints can be added similarly.
