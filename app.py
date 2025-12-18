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
    print("🎵 Starting Carnatic Learning Application")
    print(f"🔗 Access the app at: http://localhost:5001")
    
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=5001,
        use_reloader=True,
        log_output=True
    )