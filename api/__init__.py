"""
Carnatic Learning API Package
Main Flask application with modular blueprints, security, and WebSocket support
"""

import os
import secrets
import logging
from typing import Tuple

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Import blueprints
from .auth.routes import auth_bp
from .learning.routes import learning_bp
from .audio.routes import audio_bp
from .social.routes import social_bp
from .analytics.routes import analytics_bp


def create_app(config_name: str = 'development') -> Tuple[Flask, SocketIO]:
    """
    Flask Application Factory with Security and WebSocket Integration

    Args:
        config_name: Configuration environment (development, production, testing)

    Returns:
        A tuple containing the Flask application instance and the SocketIO instance.
    """
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder)

    # Configure logging, config, CORS, and security headers
    setup_logging(app, config_name)
    load_config(app, config_name)
    setup_cors(app)

    # Initialize SocketIO
    socketio_instance = SocketIO(app, cors_allowed_origins=app.config.get('ALLOWED_ORIGINS'), async_mode='threading')

    # Register blueprints
    register_blueprints(app)
    register_main_routes(app)
    register_cli_commands(app)
    register_socketio_events(socketio_instance)
    
    app.logger.info(f"Carnatic Music Platform v2 initialized in {config_name} mode")

    return app, socketio_instance


def setup_logging(app: Flask, config_name: str) -> None:
    """Configure application logging."""
    log_level = logging.INFO
    if config_name == 'production':
        log_level = logging.WARNING
    elif config_name == 'testing':
        log_level = logging.ERROR

    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')
    app.logger.setLevel(log_level)
    if config_name == 'production':
        logging.getLogger('werkzeug').setLevel(logging.WARNING)


def load_config(app: Flask, config_name: str) -> None:
    """Load configuration from environment variables."""
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'postgresql://localhost/carnatic_music'),
        'MAX_CONTENT_LENGTH': 2 * 1024 * 1024,
        'ALLOWED_ORIGINS': os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5001').split(','),
    })
    if config_name == 'development':
        app.config['DEBUG'] = True
        if not app.config['SECRET_KEY']:
            app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
            app.logger.warning("Using auto-generated SECRET_KEY for development")
    elif config_name in ('production', 'testing'):
        app.config['DEBUG'] = False
        app.config['TESTING'] = config_name == 'testing'
        if not app.config['SECRET_KEY']:
            raise RuntimeError("SECRET_KEY environment variable must be set in production/testing")


def setup_cors(app: Flask) -> None:
    """Configure CORS and add security headers."""
    CORS(app,
         origins=app.config.get('ALLOWED_ORIGINS'),
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         supports_credentials=True)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def register_blueprints(app: Flask) -> None:
    """Register API blueprints."""
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(learning_bp, url_prefix='/api/v1/learning')
    app.register_blueprint(audio_bp, url_prefix='/api/v1/audio')
    app.register_blueprint(social_bp, url_prefix='/api/v1/social')
    app.register_blueprint(analytics_bp, url_prefix='/api/v1/analytics')
    app.logger.info("Registered API version 1 blueprints")

def register_main_routes(app: Flask) -> None:
    """Register main application routes."""
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/carnatic')
    def carnatic():
        return app.send_static_file('carnatic.html')

    @app.route('/learning')
    def learning_app():
        return app.send_static_file('learning.html')

    @app.route('/api/v1/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.ico')


def register_socketio_events(socketio_instance: SocketIO) -> None:
    """Register WebSocket events."""
    from .audio.websocket import register_audio_events
    from .learning.websocket import register_learning_events
    
    register_audio_events(socketio_instance)
    register_learning_events(socketio_instance)
    logging.getLogger(__name__).info("Registered WebSocket event handlers.")

def register_cli_commands(app: Flask) -> None:
    """Register CLI commands."""
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        try:
            from migrations.init_db import main
            main()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization failed: {e}")

    @app.cli.command()
    def security_check():
        """Run basic security checks."""
        print("Running security checks...")
        secret_key = app.config.get('SECRET_KEY', '')
        if len(secret_key) < 32:
            print("❌ SECRET_KEY should be at least 32 characters")
        else:
            print("✅ SECRET_KEY length is adequate")
        print("Security check completed")