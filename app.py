from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import numpy as np
import sounddevice as sd
import json
from carnatic_detector import CarnaticNoteDetector, carnatic_audio_callback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'music_detection_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global detector instance
detector = None
detection_thread = None
detection_active = False
audio_stream = None

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
    """Get detailed information about a specific shruti"""
    global detector
    if detector is None:
        detector = CarnaticNoteDetector()
    
    shruti_info = detector.get_shruti_info(shruti_name)
    if shruti_info:
        return jsonify(shruti_info)
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
    """Get detection history for analysis"""
    global detector
    if detector is None:
        return jsonify([])
    
    return jsonify(detector.export_detection_history())

@app.route('/api/set-base-frequency', methods=['POST'])
def set_base_frequency():
    """Set the base Sa frequency"""
    global detector
    data = request.get_json()
    
    if not data or 'frequency' not in data:
        return jsonify({'error': 'Frequency required'}), 400
    
    try:
        frequency = float(data['frequency'])
        if frequency < 100 or frequency > 500:
            return jsonify({'error': 'Frequency must be between 100-500 Hz'}), 400
        
        if detector is None:
            detector = CarnaticNoteDetector(base_frequency=frequency)
        else:
            detector.set_base_frequency(frequency)
        
        return jsonify({
            'success': True, 
            'base_frequency': frequency,
            'message': f'Base Sa frequency set to {frequency} Hz'
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid frequency value'}), 400

@socketio.on('set_base_frequency')
def handle_set_base_frequency(data):
    """Handle base frequency change via WebSocket"""
    global detector
    
    try:
        frequency = float(data.get('frequency', 261.63))
        
        if detector is None:
            detector = CarnaticNoteDetector(base_frequency=frequency)
        else:
            detector.set_base_frequency(frequency)
        
        emit('base_frequency_updated', {
            'base_frequency': frequency,
            'message': f'Sa tuned to {frequency} Hz'
        })
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('start_detection')
def start_detection(data=None):
    global detector, detection_thread, detection_active, audio_stream
    
    try:
        # Get base frequency from client (default Sa = C4)
        base_freq = 261.63
        if data and 'base_frequency' in data:
            base_freq = float(data['base_frequency'])
        
        print(f'Client started detection with Sa = {base_freq} Hz')
        
        # Initialize detector if not exists
        if detector is None:
            detector = CarnaticNoteDetector(base_frequency=base_freq)
        else:
            detector.set_base_frequency(base_freq)
        
        # Stop existing stream if running
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
        
        # Create enhanced callback
        def enhanced_callback(indata, frames, time_info, status):
            if not detection_active:
                return
                
            if status:
                print(f"Audio status: {status}", flush=True)
            
            result = detector.detect_shruti(indata, frames)
            
            if result and result.confidence > detector.confidence_threshold:
                # Format output for web interface
                output = {
                    'note': result.shruti.name,
                    'western_equiv': result.shruti.western_equiv,
                    'frequency': round(detector.shruti_frequencies.get(result.shruti.name, result.frequency), 2),
                    'detected_frequency': round(result.frequency, 2),
                    'magnitude': round(result.magnitude, 2),
                    'confidence': round(result.confidence, 3),
                    'cent_value': result.shruti.cent_value,
                    'raga_context': detector.get_raga_context(),
                    'timestamp': result.timestamp
                }
                
                # Emit to all connected clients
                socketio.emit('note_detected', output)
        
        # Start audio stream with error handling
        detection_active = True
        try:
            # Try to get available audio devices
            devices = sd.query_devices()
            input_device = None
            
            # Find first available input device
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_device = i
                    print(f"Found input device {i}: {device['name']}")
                    break
            
            if input_device is None:
                raise Exception("No audio input devices available in container")
            
            audio_stream = sd.InputStream(
                callback=enhanced_callback,
                blocksize=2048,
                samplerate=detector.sample_rate,
                channels=1,
                device=input_device
            )
            audio_stream.start()
            print(f"Audio stream started successfully with device {input_device}")
            
        except Exception as audio_error:
            print(f"Audio initialization failed: {audio_error}")
            detection_active = False
            # Send error to client with helpful message
            emit('detection_status', {
                'status': 'error', 
                'message': f'Docker container cannot access microphone on macOS. Please use the standalone Python script for microphone access: python3 standalone_carnatic.py'
            })
            socketio.emit('error', {
                'message': f'Docker container cannot access microphone on macOS. Please use the standalone Python script for microphone access: python3 standalone_carnatic.py'
            })
            return
        
        emit('detection_status', {
            'status': 'started', 
            'base_frequency': base_freq,
            'detector_type': 'carnatic'
        })
        
    except Exception as e:
        print(f"Error starting detection: {e}")
        emit('detection_status', {'status': 'error', 'message': str(e)})

@socketio.on('stop_detection')
def stop_detection():
    global detection_active, audio_stream
    
    try:
        print('Client stopped detection')
        detection_active = False
        
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
            audio_stream = None
        
        # Export detection history
        if detector:
            history = detector.export_detection_history()
            print(f"Session summary: {len(history)} detections")
        
        emit('detection_status', {'status': 'stopped'})
        
    except Exception as e:
        print(f"Error stopping detection: {e}")
        emit('detection_status', {'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('detection_status', {
        'status': 'connected',
        'detector_type': 'carnatic',
        'shruti_system': True
    })

@socketio.on('disconnect')
def handle_disconnect():
    global detection_active, audio_stream
    
    print('Client disconnected')
    
    # Clean up on disconnect
    detection_active = False
    if audio_stream is not None:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None

if __name__ == '__main__':
    print("Starting web server for client-side audio processing...")
    # Start the web server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)