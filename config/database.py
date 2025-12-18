"""
Database Configuration and Models for Carnatic Music Learning Platform
"""

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON,
    String, Text, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Database configuration
Base = declarative_base()

@dataclass
class DatabaseConfig:
    """Database configuration with environment-based settings"""

    # PostgreSQL Configuration - No defaults for sensitive values
    postgresql_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgresql_port: str = os.getenv('POSTGRES_PORT', '5432')
    postgresql_db: str = os.getenv('POSTGRES_DB', 'carnatic_learning')
    postgresql_user: str = os.getenv('POSTGRES_USER')
    postgresql_password: str = os.getenv('POSTGRES_PASSWORD')

    def __post_init__(self):
        """Validate required database configuration"""
        # Check for production requirements
        if os.getenv('FLASK_ENV') == 'production':
            required_vars = ['postgresql_user', 'postgresql_password']
            missing = [var for var in required_vars if not getattr(self, var)]
            if missing:
                raise ValueError(
                    f"Missing required database configuration in production: {missing}. "
                    f"Set POSTGRES_USER and POSTGRES_PASSWORD environment variables."
                )

        # Development fallbacks with warnings
        if not self.postgresql_user:
            self.postgresql_user = 'carnatic_user'
            print("⚠️  WARNING: Using default POSTGRES_USER - set environment variable for production")

        if not self.postgresql_password:
            self.postgresql_password = 'carnatic_pass'
            print("⚠️  WARNING: Using default POSTGRES_PASSWORD - set environment variable for production")

    # Redis Configuration
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    redis_password: Optional[str] = os.getenv('REDIS_PASSWORD')

    # Connection Pool Settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))

    @property
    def postgresql_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.postgresql_user}:{self.postgresql_password}@{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_db}"

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

# Database Models
class User(Base):
    """User model with comprehensive profile and progress tracking"""

    __tablename__ = 'users'

    # Primary fields
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    full_name = Column(String(200))
    profile_data = Column(JSON, default=dict)  # Flexible profile storage
    musical_background = Column(JSON, default=dict)
    learning_preferences = Column(JSON, default=dict)

    # Subscription and access
    subscription_level = Column(String(50), default='free')
    subscription_expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))

    # Relationships
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_subscription', 'subscription_level', 'is_active'),
        Index('idx_user_created', 'created_at'),
    )

class Exercise(Base):
    """Exercise model for different learning modules"""

    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True)

    # Exercise categorization
    type = Column(String(50), nullable=False, index=True)  # swara, sarali, janta, alankaram, etc.
    category = Column(String(50), nullable=False, index=True)
    difficulty_level = Column(Integer, nullable=False, index=True)  # 1-10 scale

    # Content and metadata
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_data = Column(JSON, nullable=False)  # Exercise-specific content
    requirements = Column(JSON, default=dict)  # Prerequisites and settings

    # Raga and Tala associations
    raga_id = Column(Integer, ForeignKey('ragas.id'))
    tala_id = Column(Integer, ForeignKey('talas.id'))

    # Performance metrics
    average_accuracy = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    estimated_duration = Column(Integer)  # minutes

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    progress_records = relationship("Progress", back_populates="exercise")
    recordings = relationship("Recording", back_populates="exercise")
    raga = relationship("Raga", back_populates="exercises")
    tala = relationship("Tala", back_populates="exercises")

class Progress(Base):
    """User progress tracking for exercises and modules"""

    __tablename__ = 'progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False, index=True)

    # Progress metrics
    completion_percentage = Column(Float, default=0.0)
    accuracy_metrics = Column(JSON, default=dict)  # Detailed accuracy data
    practice_time = Column(Integer, default=0)  # seconds
    attempt_count = Column(Integer, default=0)

    # Performance tracking
    best_accuracy = Column(Float, default=0.0)
    average_accuracy = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)

    # Session data
    last_practiced = Column(DateTime(timezone=True))
    streak_days = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="progress_records")
    exercise = relationship("Exercise", back_populates="progress_records")

    # Composite indexes for queries
    __table_args__ = (
        Index('idx_progress_user_exercise', 'user_id', 'exercise_id'),
        Index('idx_progress_updated', 'updated_at'),
        Index('idx_progress_completion', 'completion_percentage'),
    )

class Recording(Base):
    """Audio recording storage and analysis results"""

    __tablename__ = 'recordings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), index=True)

    # Recording metadata
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # bytes
    duration = Column(Float)  # seconds

    # Audio parameters
    sample_rate = Column(Integer, default=44100)
    channels = Column(Integer, default=1)
    format = Column(String(20), default='wav')

    # Analysis results
    analysis_results = Column(JSON, default=dict)  # Pitch detection, accuracy, etc.
    overall_accuracy = Column(Float)
    feedback_data = Column(JSON, default=dict)

    # Metadata
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True))
    is_processed = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="recordings")
    exercise = relationship("Exercise", back_populates="recordings")

class Raga(Base):
    """Raga information and characteristics"""

    __tablename__ = 'ragas'

    id = Column(Integer, primary_key=True)

    # Basic information
    name = Column(String(100), nullable=False, unique=True, index=True)
    transliterated_name = Column(String(100))
    melakarta_number = Column(Integer, index=True)  # 1-72 for melakarta ragas

    # Scale information
    arohanam = Column(String(50), nullable=False)  # Ascending scale
    avarohanam = Column(String(50), nullable=False)  # Descending scale
    jati = Column(String(20))  # Sampurna, Shadava, Audava

    # Characteristics
    characteristics = Column(JSON, default=dict)  # Emotional context, time, etc.
    pakad_phrases = Column(JSON, default=list)  # Characteristic phrases
    parent_raga_id = Column(Integer, ForeignKey('ragas.id'))  # For janya ragas

    # Audio samples and references
    audio_samples = Column(JSON, default=list)  # URLs to audio examples
    notation_examples = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    exercises = relationship("Exercise", back_populates="raga")
    compositions = relationship("Composition", back_populates="raga")
    child_ragas = relationship("Raga", remote_side=[id])  # Self-referential

class Tala(Base):
    """Tala (rhythmic cycle) information"""

    __tablename__ = 'talas'

    id = Column(Integer, primary_key=True)

    # Basic information
    name = Column(String(100), nullable=False, unique=True, index=True)
    beats_per_cycle = Column(Integer, nullable=False)
    subdivisions = Column(JSON, nullable=False)  # Beat subdivision pattern

    # Pattern information
    pattern = Column(String(200))  # Clap pattern representation
    notation = Column(String(100))  # Traditional notation

    # Characteristics
    common_speeds = Column(JSON, default=list)  # Common tempo ranges
    difficulty_level = Column(Integer, default=1)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    exercises = relationship("Exercise", back_populates="tala")
    compositions = relationship("Composition", back_populates="tala")

class Composition(Base):
    """Musical compositions (Geetams, Varnams, Kritis)"""

    __tablename__ = 'compositions'

    id = Column(Integer, primary_key=True)

    # Basic information
    title = Column(String(200), nullable=False, index=True)
    composer = Column(String(100), index=True)
    type = Column(String(50), nullable=False, index=True)  # geetam, varnam, kriti, etc.

    # Musical structure
    raga_id = Column(Integer, ForeignKey('ragas.id'), nullable=False)
    tala_id = Column(Integer, ForeignKey('talas.id'), nullable=False)
    difficulty = Column(Integer, nullable=False, index=True)  # 1-10 scale

    # Content
    lyrics = Column(JSON, default=dict)  # Multi-language lyrics
    notation = Column(JSON, default=dict)  # Both Carnatic and Western
    audio_references = Column(JSON, default=list)  # Reference recordings

    # Learning structure
    sections = Column(JSON, default=list)  # Pallavi, Anupallavi, Charanam
    teaching_notes = Column(Text)
    practice_tips = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    raga = relationship("Raga", back_populates="compositions")
    tala = relationship("Tala", back_populates="compositions")

class Achievement(Base):
    """User achievement and badge system"""

    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Achievement details
    badge_type = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Scoring
    points_awarded = Column(Integer, default=0)
    rarity_level = Column(String(20), default='common')  # common, rare, epic, legendary

    # Context
    related_exercise_id = Column(Integer, ForeignKey('exercises.id'))
    achievement_data = Column(JSON, default=dict)  # Context-specific data

    # Metadata
    earned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_visible = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="achievements")

class Group(Base):
    """Learning groups and collaborative sessions"""

    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)

    # Group information
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False, index=True)  # study_group, class, etc.

    # Management
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    instructor_id = Column(Integer, ForeignKey('users.id'))
    member_count = Column(Integer, default=0)
    max_members = Column(Integer, default=50)

    # Settings
    is_public = Column(Boolean, default=False)
    join_code = Column(String(20), unique=True)
    settings = Column(JSON, default=dict)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

# Database initialization and connection management
class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self.redis_client = None

    def initialize_postgresql(self) -> None:
        """Initialize PostgreSQL connection pool"""
        try:
            self.engine = create_engine(
                self.config.postgresql_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False  # Set to True for SQL debugging
            )

            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("PostgreSQL connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            redis_kwargs = {
                'host': self.config.redis_host,
                'port': self.config.redis_port,
                'db': self.config.redis_db,
                'decode_responses': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True
            }

            if self.config.redis_password:
                redis_kwargs['password'] = self.config.redis_password

            self.redis_client = redis.Redis(**redis_kwargs)

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def create_tables(self) -> None:
        """Create all database tables"""
        try:
            if not self.engine:
                raise RuntimeError("PostgreSQL engine not initialized")

            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()

    def get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client

    def health_check(self) -> Dict[str, bool]:
        """Check health of database connections"""
        health = {'postgresql': False, 'redis': False}

        # Check PostgreSQL
        try:
            with self.get_session() as session:
                session.execute('SELECT 1')
                health['postgresql'] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")

        # Check Redis
        try:
            self.redis_client.ping()
            health['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        return health

    def close_connections(self) -> None:
        """Close all database connections"""
        if self.engine:
            self.engine.dispose()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# Flask-SQLAlchemy integration
def init_db_with_flask(app) -> SQLAlchemy:
    """Initialize database with Flask app"""
    app.config['SQLALCHEMY_DATABASE_URI'] = db_manager.config.postgresql_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': db_manager.config.pool_size,
        'max_overflow': db_manager.config.max_overflow,
        'pool_timeout': db_manager.config.pool_timeout,
        'pool_recycle': db_manager.config.pool_recycle,
    }

    db = SQLAlchemy(app)
    return db

# Database utility functions
def seed_initial_data(session: Session) -> None:
    """Seed database with initial data"""
    try:
        # Create basic ragas
        basic_ragas = [
            {
                'name': 'Mayamalavagowla',
                'melakarta_number': 15,
                'arohanam': 'S R1 G3 M1 P D1 N3 S',
                'avarohanam': 'S N3 D1 P M1 G3 R1 S',
                'characteristics': {'time': 'morning', 'emotion': 'devotional'}
            },
            {
                'name': 'Sankarabharanam',
                'melakarta_number': 29,
                'arohanam': 'S R2 G3 M1 P D2 N3 S',
                'avarohanam': 'S N3 D2 P M1 G3 R2 S',
                'characteristics': {'time': 'evening', 'emotion': 'peaceful'}
            }
        ]

        for raga_data in basic_ragas:
            existing = session.query(Raga).filter_by(name=raga_data['name']).first()
            if not existing:
                raga = Raga(**raga_data)
                session.add(raga)

        # Create basic talas
        basic_talas = [
            {
                'name': 'Adi',
                'beats_per_cycle': 8,
                'subdivisions': [4, 2, 2],
                'pattern': '| | O |'
            },
            {
                'name': 'Rupaka',
                'beats_per_cycle': 6,
                'subdivisions': [2, 4],
                'pattern': 'O | |'
            }
        ]

        for tala_data in basic_talas:
            existing = session.query(Tala).filter_by(name=tala_data['name']).first()
            if not existing:
                tala = Tala(**tala_data)
                session.add(tala)

        session.commit()
        logger.info("Initial data seeded successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed initial data: {e}")
        raise

# Session context manager
@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()