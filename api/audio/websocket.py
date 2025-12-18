"""
Audio WebSocket Events
Handles basic client connections and disconnections for the audio namespace.
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
import logging

logger = logging.getLogger(__name__)

def register_audio_events(socketio):
    """Register basic audio-related WebSocket events."""

    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection."""
        session_id = request.sid
        user_id = auth.get('user_id') if auth else None
        
        logger.info(f"Client connected: {session_id}, User: {user_id}")
        join_room('audio_detection')
        if user_id:
            join_room(f'user_{user_id}')
            
        emit('connected', {
            'message': 'Connected to real-time audio service.',
            'session_id': session_id
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        session_id = request.sid
        logger.info(f"Client disconnected: {session_id}")
        # Rooms are automatically left on disconnect, but being explicit can be useful.
        leave_room('audio_detection')

    @socketio.on('set_base_frequency')
    def handle_set_base_frequency(data):
        """
        Placeholder for setting base frequency. In the new architecture,
        this might notify other clients or save a user's preference.
        """
        session_id = request.sid
        frequency = data.get('frequency')
        logger.info(f"Session {session_id} requested to set base frequency to {frequency}Hz.")
        # This is where logic would go to persist this preference or notify other clients.
        emit('base_frequency_set', {'frequency': frequency, 'status': 'acknowledged'})

    # Placeholder for receiving detection results from the client
    @socketio.on('detection_result')
    def handle_detection_result(data):
        """
        Receives shruti detection results from the client.
        This aligns with the new architecture where the client does the processing.
        The server can then process, store, or broadcast these results.
        """
        session_id = request.sid
        logger.debug(f"Received detection result from {session_id}: {data}")
        # For now, just acknowledge receipt.
        emit('result_received', {'status': 'ok', 'timestamp': data.get('timestamp')})

    @socketio.on('ping')
    def handle_ping():
        """Handle ping for latency measurement."""
        emit('pong', {'timestamp': time.time()})