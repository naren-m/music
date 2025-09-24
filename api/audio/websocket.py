"""
Audio WebSocket Events
Real-time audio processing and shruti detection
"""

from flask_socketio import emit
import json


def register_audio_events(socketio):
    """Register audio-related WebSocket events"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        emit('connected', {'message': 'Connected to Carnatic Learning Server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected from audio service')
    
    @socketio.on('start_detection')
    def handle_start_detection(data):
        """Start audio detection"""
        emit('detection_started', {'status': 'Audio detection started'})
    
    @socketio.on('stop_detection')
    def handle_stop_detection():
        """Stop audio detection"""
        emit('detection_stopped', {'status': 'Audio detection stopped'})
    
    @socketio.on('set_base_frequency')
    def handle_set_base_frequency(data):
        """Set base Sa frequency"""
        frequency = data.get('frequency', 261.63)
        emit('base_frequency_set', {'frequency': frequency})