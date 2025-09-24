"""
Carnatic Learning API Package
Main Flask application with modular blueprints
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
from typing import Optional

# Import blueprints
from .auth.routes import auth_bp
from .learning.routes import learning_bp
from .audio.routes import audio_bp
from .social.routes import social_bp

# Global SocketIO instance
socketio: Optional[SocketIO] = None


def create_app(config_name: str = 'development'):
    """Application factory pattern"""
    import os
    # Set static folder to project root static directory
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder)
    
    # Load configuration
    config_object = get_config(config_name)
    app.config.from_object(config_object)
    
    # Initialize extensions
    CORS(app, cors_allowed_origins="*")
    
    socketio_instance = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(learning_bp, url_prefix='/api/v1/learning')
    app.register_blueprint(audio_bp, url_prefix='/api/v1/audio')
    app.register_blueprint(social_bp, url_prefix='/api/v1/social')
    
    # Register main routes
    register_main_routes(app)
    
    # Register WebSocket events
    register_socketio_events(socketio_instance)
    
    return app, socketio_instance


def get_config(config_name: str):
    """Get configuration object"""
    from config.settings import config
    return config.get(config_name, config['development'])


def register_main_routes(app: Flask):
    """Register main application routes"""
    
    @app.route('/')
    def index():
        """Western note detection interface"""
        return app.send_static_file('index.html')
    
    @app.route('/carnatic')
    def carnatic():
        """Carnatic shruti detection interface"""
        return app.send_static_file('carnatic.html')
    
    @app.route('/learning')
    def learning_app():
        """New learning application interface"""
        return app.send_static_file('learning.html')
    
    @app.route('/api/v1/health')
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'version': '2.0.0'}
    
    @app.route('/favicon.ico')
    def favicon():
        """Favicon route"""
        return app.send_static_file('favicon.ico')


def register_socketio_events(socketio_instance):
    """Register WebSocket events"""
    from .audio.websocket import register_audio_events
    from .learning.websocket import register_learning_events
    
    register_audio_events(socketio_instance)
    register_learning_events(socketio_instance)