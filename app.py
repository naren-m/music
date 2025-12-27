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
    print("🎵 Starting Carnatic Learning Application")
    print(f"🔗 Access the app at: http://localhost:{port}")

    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=port,
        use_reloader=True,
        log_output=True,
        allow_unsafe_werkzeug=True
    )