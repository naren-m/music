from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
# Note: No audio processing imports needed - using client-side Web Audio API

app = Flask(__name__)
app.config['SECRET_KEY'] = 'music_detection_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# No global audio variables needed - using client-side processing

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/carnatic')
def carnatic():
    return render_template('carnatic.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/shruti/<shruti_name>')
def get_shruti_info(shruti_name):
    """Get detailed information about a specific shruti - client-side processing"""
    # Return static shruti information for client-side processing
    shruti_info = {
        'Shadja': {'cents': 0, 'western': 'Sa', 'frequency_ratio': 1.0},
        'Suddha Ri': {'cents': 90, 'western': 'R₁', 'frequency_ratio': 1.053},
        'Chatussruti Ri': {'cents': 182, 'western': 'R₂', 'frequency_ratio': 1.122},
        # Add more as needed
    }
    
    if shruti_name in shruti_info:
        return jsonify(shruti_info[shruti_name])
    return jsonify({'error': 'Shruti not found'}), 404

@app.route('/api/ragas')
def get_ragas():
    """Get list of supported ragas"""
    ragas = {
        'Sankarabharanam': {
            'shrutis': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Suddha Ma', 'Panchama', 'Shatsruti Dha', 'Kakali Ni'],
            'description': 'Major scale, equivalent to Western Ionian mode',
            'aroha': 'S R₂ G₃ M₁ P D₂ N₃ Ṡ',
            'avaroha': 'Ṡ N₃ D₂ P M₁ G₃ R₂ S'
        },
        'Kharaharapriya': {
            'shrutis': ['Shadja', 'Chatussruti Ri', 'Sadharana Ga', 'Suddha Ma', 'Panchama', 'Chatussruti Dha', 'Kaisika Ni'],
            'description': 'Natural minor scale, janya of 22nd melakarta',
            'aroha': 'S R₂ G₂ M₁ P D₂ N₂ Ṡ',
            'avaroha': 'Ṡ N₂ D₂ P M₁ G₂ R₂ S'
        },
        'Mayamalavagowla': {
            'shrutis': ['Shadja', 'Suddha Ri', 'Antara Ga', 'Suddha Ma', 'Panchama', 'Suddha Dha', 'Kakali Ni'],
            'description': '15th melakarta, morning raga',
            'aroha': 'S R₁ G₃ M₁ P D₁ N₃ Ṡ',
            'avaroha': 'Ṡ N₃ D₁ P M₁ G₃ R₁ S'
        },
        'Mohanam': {
            'shrutis': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Panchama', 'Shatsruti Dha'],
            'description': 'Pentatonic scale, janya of Sankarabharanam',
            'aroha': 'S R₂ G₃ P D₂ Ṡ',
            'avaroha': 'Ṡ D₂ P G₃ R₂ S'
        },
        'Kalyani': {
            'shrutis': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Prati Ma', 'Panchama', 'Shatsruti Dha', 'Kakali Ni'],
            'description': '65th melakarta, Lydian mode',
            'aroha': 'S R₂ G₃ M₂ P D₂ N₃ Ṡ',
            'avaroha': 'Ṡ N₃ D₂ P M₂ G₃ R₂ S'
        }
    }
    return jsonify(ragas)

@app.route('/api/detection-history')
def get_detection_history():
    """Get detection history - managed client-side"""
    return jsonify({
        'message': 'Detection history managed by client-side JavaScript',
        'history': []
    })

@app.route('/api/set-base-frequency', methods=['POST'])
def set_base_frequency():
    """Set the base Sa frequency - client-side processing"""
    data = request.get_json()
    
    if not data or 'frequency' not in data:
        return jsonify({'error': 'Frequency required'}), 400
    
    try:
        frequency = float(data['frequency'])
        if frequency < 100 or frequency > 500:
            return jsonify({'error': 'Frequency must be between 100-500 Hz'}), 400
        
        return jsonify({
            'success': True, 
            'base_frequency': frequency,
            'message': f'Base Sa frequency set to {frequency} Hz (client-side processing)'
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid frequency value'}), 400

@socketio.on('set_base_frequency')
def handle_set_base_frequency(data):
    """Handle base frequency change via WebSocket - client-side processing"""
    try:
        frequency = float(data.get('frequency', 261.63))
        
        emit('base_frequency_updated', {
            'base_frequency': frequency,
            'message': f'Sa tuned to {frequency} Hz (client-side processing)'
        })
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('start_detection')
def start_detection(data=None):
    """Handle client-side detection start - pure web interface only"""
    try:
        # Get base frequency from client (default Sa = C4)
        base_freq = 261.63
        if data and 'base_frequency' in data:
            base_freq = float(data['base_frequency'])
        
        print(f'Client started detection with Sa = {base_freq} Hz (client-side processing)')
        
        # Send success response - no server audio processing needed
        emit('detection_status', {
            'status': 'started', 
            'base_frequency': base_freq,
            'detector_type': 'client_side_carnatic',
            'message': 'Audio processing active in browser'
        })
        
    except Exception as e:
        print(f"Error in start_detection handler: {e}")
        emit('detection_status', {'status': 'error', 'message': str(e)})

@socketio.on('stop_detection')
def stop_detection():
    """Handle client-side detection stop - no server cleanup needed"""
    try:
        print('Client stopped detection (client-side processing)')
        emit('detection_status', {'status': 'stopped'})
        
    except Exception as e:
        print(f"Error in stop_detection handler: {e}")
        emit('detection_status', {'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    print('Client connected - client-side audio processing ready')
    emit('detection_status', {
        'status': 'connected',
        'detector_type': 'client_side_carnatic',
        'shruti_system': True,
        'audio_processing': 'browser_web_audio_api'
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected - no server cleanup needed for client-side audio')

if __name__ == '__main__':
    print("Starting web server for client-side audio processing...")
    print("🎤 Client-side microphone access requires HTTPS in production")
    print("🔒 For local development, use: https://localhost:5000")
    print("📱 For mobile testing, generate SSL certificates")
    
    # Start the web server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)