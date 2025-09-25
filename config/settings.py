"""
Configuration settings for Carnatic Learning Application
"""

import os
import secrets
from datetime import timedelta
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # dotenv not installed, continue without it
    pass


class Config:
    """Base configuration"""

    # Generate secure secret if not provided
    _secret_key = os.environ.get('SECRET_KEY')
    if not _secret_key:
        if os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        # Generate temporary key for development
        _secret_key = secrets.token_urlsafe(32)
        print(f"⚠️  WARNING: Generated temporary SECRET_KEY for development: {_secret_key}")
        print("   Set SECRET_KEY environment variable for production deployment")

    SECRET_KEY = _secret_key
    
    # Database - Secure configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        if os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError("DATABASE_URL environment variable must be set in production")
        # Development fallback
        SQLALCHEMY_DATABASE_URI = 'sqlite:///carnatic_learning.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session - Security hardened
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.environ.get('SESSION_TIMEOUT_HOURS', 24))
    )
    SESSION_COOKIE_SECURE = os.environ.get('SECURE_COOKIES', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CORS - Environment configurable
    _cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000')
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(',')]

    # Audio processing - Environment configurable
    AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', 44100))
    AUDIO_BUFFER_SIZE = int(os.environ.get('AUDIO_BUFFER_SIZE', 2048))
    DEFAULT_SA_FREQUENCY = float(os.environ.get('DEFAULT_SA_FREQUENCY', 261.63))

    # File uploads - Security enhanced
    _max_upload_mb = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 16))
    MAX_CONTENT_LENGTH = _max_upload_mb * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg'}

    # Redis - Secure configuration
    REDIS_URL = os.environ.get('REDIS_URL')
    if not REDIS_URL:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = os.environ.get('REDIS_PORT', '6379')
        redis_db = os.environ.get('REDIS_DB', '0')
        redis_password = os.environ.get('REDIS_PASSWORD')

        if redis_password:
            REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            REDIS_URL = f"redis://{redis_host}:{redis_port}/{redis_db}"

    # JWT tokens - Separate key required
    _jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    if not _jwt_secret_key:
        if os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError("JWT_SECRET_KEY environment variable must be set in production")
        _jwt_secret_key = SECRET_KEY  # Development fallback

    JWT_SECRET_KEY = _jwt_secret_key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Security Configuration
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    WTF_CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'true').lower() == 'true'

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/carnatic.log')

    @classmethod
    def validate_production_config(cls):
        """Validate required environment variables in production"""
        if os.environ.get('FLASK_ENV') != 'production':
            return

        required_vars = [
            'SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET_KEY'
        ]

        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables for production: {missing}. "
                f"Please set these variables before deploying."
            )


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Enable detailed error messages
    PROPAGATE_EXCEPTIONS = True
    
    # Development-specific settings
    WTF_CSRF_ENABLED = False  # Disable CSRF for development API testing
    
    # Logging
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Speed up password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Security settings - Force secure configuration
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

    # Database - No fallbacks in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL must be set in production")

    # Validate all production requirements on class creation
    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.validate_production_config()
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')


class StagingConfig(ProductionConfig):
    """Staging configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}