"""
Carnatic Learning Application
Main application entry point.
"""

import os
from api import create_app

# Create application using factory pattern
app, socketio = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5002))
    is_dev = os.environ.get('FLASK_ENV', 'development') == 'development'
    print("🎵 Starting Carnatic Learning Application")
    print(f"🔗 Access the app at: http://localhost:{port}")

    # Debug, the auto-reloader, and Werkzeug's unsafe dev server are gated to
    # development only. In any other environment run this under a real WSGI/ASGI
    # server (e.g. gunicorn with an eventlet/gevent worker) rather than __main__.
    socketio.run(
        app,
        debug=is_dev,
        host='0.0.0.0',
        port=port,
        use_reloader=is_dev,
        log_output=True,
        allow_unsafe_werkzeug=is_dev
    )