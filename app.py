"""
Flask Application Factory - Production Ready
Carnatic Music Learning Platform with Security Integration
"""

import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from flask_session import Session

# Ensure project imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import security components
from api.error_handlers import register_error_handlers, security_middleware
from api.validation import ValidationError
from api.auth.middleware import AuthenticationError, RateLimitError


def create_app(config_name='development'):
    """
    Flask Application Factory with Security Integration

    Args:
        config_name: Configuration environment (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__,
                static_folder='frontend/build',
                static_url_path='/',
                template_folder='templates')

    # Configure logging
    setup_logging(app, config_name)

    # Load configuration
    load_config(app, config_name)

    # Enable CORS with security headers
    setup_cors(app)

    # Configure session management
    setup_sessions(app)

    # Register security middleware
    setup_security_middleware(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Log application startup
    app.logger.info(f"Carnatic Music Platform initialized in {config_name} mode")

    return app


def setup_logging(app, config_name):
    """Configure application logging with security considerations"""
    # Set log level based on environment
    if config_name == 'production':
        log_level = logging.WARNING
    elif config_name == 'testing':
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    # Configure logging format
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            # In production, add file handler with rotation
        ]
    )

    # Set Flask logger level
    app.logger.setLevel(log_level)

    # Disable sensitive information logging in production
    if config_name == 'production':
        logging.getLogger('werkzeug').setLevel(logging.WARNING)


def load_config(app, config_name):
    """Load configuration with environment variable support"""

    # Base configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'postgresql://localhost/carnatic_music'),
        'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'MAX_CONTENT_LENGTH': 2 * 1024 * 1024,  # 2MB max request size
        'PERMANENT_SESSION_LIFETIME': 86400,  # 24 hours
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'LOG_REQUESTS': True,
        'LOG_RESPONSES': False,
    })

    # Environment-specific configuration
    if config_name == 'development':
        app.config.update({
            'DEBUG': True,
            'SESSION_COOKIE_SECURE': False,  # Allow HTTP in development
            'LOG_REQUESTS': True,
            'LOG_RESPONSES': True,
        })

        # Generate development secret key if not provided
        if not app.config['SECRET_KEY']:
            import secrets
            app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
            app.logger.warning("Using auto-generated SECRET_KEY for development")

    elif config_name == 'production':
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
            'LOG_REQUESTS': True,
            'LOG_RESPONSES': False,
        })

        # Ensure required production settings
        if not app.config['SECRET_KEY']:
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production"
            )

        if len(app.config['SECRET_KEY']) < 32:
            raise RuntimeError(
                "SECRET_KEY must be at least 32 characters in production"
            )

    elif config_name == 'testing':
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key-not-for-production',
            'DATABASE_URL': 'sqlite:///:memory:',
            'LOG_REQUESTS': False,
            'LOG_RESPONSES': False,
        })


def setup_cors(app):
    """Configure CORS with security headers"""
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5003').split(',')

    CORS(app,
         origins=allowed_origins,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         supports_credentials=True)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


def setup_sessions(app):
    """Configure Flask-Session with Redis backend"""
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'carnatic:'

    # Initialize session
    Session(app)


def setup_security_middleware(app):
    """Configure security middleware"""
    @app.before_request
    def before_request():
        """Apply security checks to all requests"""
        security_middleware()


def register_blueprints(app):
    """Register API blueprints with error handling"""
    try:
        # Audio processing blueprint
        from api.audio.routes import audio_bp
        app.register_blueprint(audio_bp, url_prefix='/api/audio')
        app.logger.info("Registered audio processing blueprint")
    except ImportError as e:
        app.logger.error(f"Failed to import audio blueprint: {e}")

    try:
        # Authentication blueprint
        from api.auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.logger.info("Registered authentication blueprint")
    except ImportError as e:
        app.logger.error(f"Failed to import auth blueprint: {e}")

    # Register additional blueprints as they're created
    try:
        from api.exercises.routes import exercises_bp
        app.register_blueprint(exercises_bp, url_prefix='/api/exercises')
        app.logger.info("Registered exercises blueprint")
    except ImportError:
        app.logger.info("Exercises blueprint not available (optional)")

    try:
        from api.raga.routes import raga_bp
        app.register_blueprint(raga_bp, url_prefix='/api/raga')
        app.logger.info("Registered raga blueprint")
    except ImportError:
        app.logger.info("Raga blueprint not available (optional)")


def register_cli_commands(app):
    """Register CLI commands for development and deployment"""

    @app.cli.command()
    def init_db():
        """Initialize the database"""
        try:
            from migrations.init_db import main
            main()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization failed: {e}")

    @app.cli.command()
    def create_admin():
        """Create admin user"""
        # TODO: Implement admin user creation
        print("Admin user creation not implemented yet")

    @app.cli.command()
    def security_check():
        """Run security checks"""
        print("Running security checks...")

        # Check environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ Required environment variables are set")

        # Check secret key strength
        secret_key = os.environ.get('SECRET_KEY', '')
        if len(secret_key) < 32:
            print("❌ SECRET_KEY should be at least 32 characters")
        else:
            print("✅ SECRET_KEY length is adequate")

        print("Security check completed")


# Application factory function for compatibility with launch_server.py
def create_quick_app():
    """Create app with quick launch compatibility"""
    return create_app('development')


if __name__ == '__main__':
    # Development server
    app = create_app('development')
    app.run(host='0.0.0.0', port=5003, debug=True, threaded=True)