"""
Learning WebSocket Events
Real-time learning feedback and exercise management
"""

from flask_socketio import emit


def register_learning_events(socketio):
    """Register learning-related WebSocket events"""
    
    @socketio.on('exercise_feedback')
    def handle_exercise_feedback(data):
        """Provide real-time exercise feedback"""
        emit('feedback_update', data)
    
    @socketio.on('milestone_achieved')
    def handle_milestone_achieved(data):
        """Broadcast milestone achievement"""
        emit('milestone_notification', data)
    
    @socketio.on('progress_update')
    def handle_progress_update(data):
        """Update learning progress"""
        emit('progress_updated', data)