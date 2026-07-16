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

    # Debug and the auto-reloader stay gated to development. The Socket.IO
    # server uses async_mode='threading' (Werkzeug), so a production container
    # must opt in to the threaded server explicitly via ALLOW_UNSAFE_WERKZEUG=1
    # (set in the Docker image); this keeps dev semantics unchanged.
    allow_werkzeug = is_dev or os.environ.get(
        'ALLOW_UNSAFE_WERKZEUG', '').lower() in ('1', 'true', 'yes')
    socketio.run(
        app,
        debug=is_dev,
        host='0.0.0.0',
        port=port,
        use_reloader=is_dev,
        log_output=True,
        allow_unsafe_werkzeug=allow_werkzeug
    )