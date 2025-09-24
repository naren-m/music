"""
Carnatic Learning Application - Version 2.0
Enhanced Flask application with modular architecture, 22-shruti system, and learning modules
"""

import os
from api import create_app

# Create application using factory pattern
app, socketio = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Development server
    print("🎵 Starting Carnatic Learning Application v2.0")
    print("🏗️ Enhanced architecture with 22-shruti system")
    print("📚 Swara Recognition training module enabled")
    print("🌐 WebSocket real-time feedback active")
    print("🎯 Ready for comprehensive music learning!")
    print(f"🔗 Access the app at: http://localhost:5001")
    print(f"🎼 Learning interface: http://localhost:5001/learning")
    print(f"🎶 Carnatic interface: http://localhost:5001/carnatic")
    
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=5001,
        use_reloader=True,
        log_output=True,
        allow_unsafe_werkzeug=True
    )