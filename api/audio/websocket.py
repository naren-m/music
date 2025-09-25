"""
Audio WebSocket Events - Optimized for Real-time Performance
Real-time audio processing and shruti detection with connection pooling
"""

from flask_socketio import emit, join_room, leave_room, rooms
from flask import request
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import time
import numpy as np
import logging
from core.services.audio_engine import CarnaticAudioEngine, AudioConfig
from api.validation import validate_audio_data, validate_frequency_parameter, ValidationError
import weakref

from api.error_handlers import AudioProcessingError, log_security_event

logger = logging.getLogger(__name__)

# Global connection management for performance
active_sessions = {}
audio_engines = weakref.WeakValueDictionary()
connection_stats = defaultdict(lambda: {'messages': 0, 'last_activity': time.time()})
executor = ThreadPoolExecutor(max_workers=8)  # Shared thread pool


def register_audio_events(socketio):
    """Register optimized audio-related WebSocket events with connection pooling"""

    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection with session management"""
        session_id = request.sid
        user_id = auth.get('user_id') if auth else None

        # Initialize session data
        active_sessions[session_id] = {
            'user_id': user_id,
            'connected_at': time.time(),
            'audio_buffer': deque(maxlen=100),  # Circular buffer
            'last_detection': None,
            'performance_stats': {'processed_chunks': 0, 'avg_latency': 0}
        }

        # Create dedicated audio engine for this session
        config = AudioConfig(enable_parallel_processing=True)
        audio_engines[session_id] = CarnaticAudioEngine(config)

        # Join appropriate rooms
        join_room('audio_detection')
        if user_id:
            join_room(f'user_{user_id}')

        emit('connected', {
            'message': 'Connected to Carnatic Learning Server',
            'session_id': session_id,
            'performance_mode': 'optimized'
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection with cleanup"""
        session_id = request.sid

        if session_id and session_id in active_sessions:
            session_data = active_sessions[session_id]
            duration = time.time() - session_data['connected_at']

            # Log performance statistics
            stats = session_data['performance_stats']
            print(f'Client disconnected: {session_id}. '
                  f'Session duration: {duration:.1f}s, '
                  f'Processed chunks: {stats["processed_chunks"]}, '
                  f'Avg latency: {stats["avg_latency"]:.2f}ms')

            # Cleanup session data
            del active_sessions[session_id]
            if session_id in audio_engines:
                del audio_engines[session_id]

        leave_room('audio_detection')

    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        """Process audio chunk with security validation and performance optimization"""
        start_time = time.time()
        session_id = request.sid

        if session_id not in active_sessions or session_id not in audio_engines:
            emit('error', {'message': 'Session not found'})
            return

        try:
            # Validate input data structure
            if not isinstance(data, dict):
                emit('validation_error', {'message': 'Invalid data format'})
                return

            # Get and validate audio data
            audio_b64 = data.get('audio_data')
            if not audio_b64:
                emit('validation_error', {'message': 'No audio data provided'})
                return

            # Use validation middleware but with more lenient size limits for real-time
            try:
                # For real-time processing, allow smaller chunks
                if isinstance(audio_b64, str):
                    audio_array = validate_audio_data(audio_b64)
                elif isinstance(audio_b64, list):
                    # Direct array data (already decoded)
                    audio_array = np.array(audio_b64, dtype=np.float32)

                    # Basic validation for direct arrays
                    if len(audio_array) == 0:
                        emit('validation_error', {'message': 'Empty audio data'})
                        return

                    if len(audio_array) > 44100 * 5:  # Max 5 seconds for real-time
                        emit('validation_error', {'message': 'Audio chunk too large'})
                        return

                    if np.any(np.isnan(audio_array)) or np.any(np.isinf(audio_array)):
                        emit('validation_error', {'message': 'Invalid audio values'})
                        return

                else:
                    emit('validation_error', {'message': 'Invalid audio data format'})
                    return

            except ValidationError as e:
                logger.warning(f"WebSocket audio validation failed: {e.message}")
                emit('validation_error', {
                    'message': e.message,
                    'field': e.field
                })
                return

            # Get audio engine for this session
            engine = audio_engines[session_id]
            session_data = active_sessions[session_id]

            # Rate limiting check (simple)
            current_time = time.time()
            last_request = session_data.get('last_audio_request', 0)
            if current_time - last_request < 0.02:  # Max 50 requests per second
                log_security_event('WEBSOCKET_RATE_LIMIT', {
                    'session_id': session_id,
                    'requests_per_second': round(1 / (current_time - last_request), 2)
                })
                emit('rate_limit', {'message': 'Too many requests'})
                return
            session_data['last_audio_request'] = current_time

            # Process audio asynchronously for better performance
            future = executor.submit(engine.detect_shruti, audio_array)

            try:
                result = future.result(timeout=0.05)  # 50ms timeout for real-time

                if result:
                    # Update session statistics
                    processing_time = (time.time() - start_time) * 1000  # ms
                    stats = session_data['performance_stats']
                    stats['processed_chunks'] += 1
                    stats['avg_latency'] = (stats['avg_latency'] + processing_time) / 2

                    # Emit detection result with validation
                    emit('shruti_detected', {
                        'shruti_name': result.shruti.name if result.shruti else None,
                        'frequency': round(float(result.detected_frequency), 2),
                        'cent_deviation': round(float(result.cent_deviation), 1),
                        'confidence': round(float(result.confidence), 3),
                        'processing_time_ms': round(processing_time, 1),
                        'timestamp': result.timestamp
                    })

                    session_data['last_detection'] = result

            except TimeoutError:
                emit('processing_timeout', {'message': 'Audio processing timeout'})

        except Exception as e:
            logger.error(f"WebSocket audio processing error: {str(e)}")
            emit('processing_error', {'message': 'Audio processing failed'})

    @socketio.on('start_detection')
    def handle_start_detection(data):
        """Start audio detection with performance monitoring"""
        session_id = request.sid

        if session_id in active_sessions:
            # Reset performance stats
            active_sessions[session_id]['performance_stats'] = {
                'processed_chunks': 0,
                'avg_latency': 0,
                'detection_started_at': time.time()
            }

        emit('detection_started', {
            'status': 'Audio detection started',
            'buffer_size': 1024,  # Optimized buffer size
            'sample_rate': 44100,
            'expected_latency_ms': 25
        })

    @socketio.on('stop_detection')
    def handle_stop_detection():
        """Stop audio detection with session summary"""
        session_id = request.sid

        session_summary = {}
        if session_id in active_sessions:
            stats = active_sessions[session_id]['performance_stats']
            if 'detection_started_at' in stats:
                session_duration = time.time() - stats['detection_started_at']
                session_summary = {
                    'session_duration_s': round(session_duration, 1),
                    'total_chunks_processed': stats['processed_chunks'],
                    'average_latency_ms': round(stats['avg_latency'], 1),
                    'chunks_per_second': round(stats['processed_chunks'] / session_duration, 1) if session_duration > 0 else 0
                }

        emit('detection_stopped', {
            'status': 'Audio detection stopped',
            'session_summary': session_summary
        })

    @socketio.on('set_base_frequency')
    def handle_set_base_frequency(data):
        """Set base Sa frequency with comprehensive validation"""
        session_id = request.sid

        try:
            # Validate input data structure
            if not isinstance(data, dict):
                emit('validation_error', {'message': 'Invalid data format'})
                return

            frequency_value = data.get('frequency')
            if frequency_value is None:
                emit('validation_error', {'message': 'Frequency parameter required'})
                return

            # Use validation middleware
            validated_frequency = validate_frequency_parameter(frequency_value)

            if session_id in audio_engines:
                audio_engines[session_id].set_base_sa_frequency(validated_frequency)
                logger.info(f"Base frequency set to {validated_frequency}Hz for session {session_id}")

                emit('base_frequency_set', {
                    'frequency': validated_frequency,
                    'status': 'Base Sa frequency updated successfully'
                })
            else:
                emit('error', {'message': 'Session not found'})

        except ValidationError as e:
            logger.warning(f"Frequency validation failed: {e.message}")
            emit('validation_error', {
                'message': e.message,
                'field': e.field or 'frequency'
            })
        except Exception as e:
            logger.error(f"Frequency setting error: {str(e)}")
            emit('error', {'message': 'Failed to set frequency'})

    @socketio.on('get_session_stats')
    def handle_get_session_stats():
        """Get real-time session performance statistics"""
        session_id = request.sid

        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            engine_stats = audio_engines[session_id].get_detection_statistics() if session_id in audio_engines else {}

            stats = {
                'session_stats': session_data['performance_stats'],
                'audio_engine_stats': engine_stats,
                'connection_health': {
                    'connected_duration_s': round(time.time() - session_data['connected_at'], 1),
                    'buffer_utilization': len(session_data['audio_buffer']) / 100,
                    'last_activity': connection_stats[session_id]['last_activity']
                }
            }

            emit('session_stats', stats)
        else:
            emit('error', {'message': 'Session not found'})

    # Performance monitoring event
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for latency measurement"""
        emit('pong', {'timestamp': time.time()})

    # Background task for cleanup
    def cleanup_inactive_sessions():
        """Clean up inactive sessions periodically"""
        current_time = time.time()
        inactive_threshold = 300  # 5 minutes

        sessions_to_remove = []
        for session_id, session_data in active_sessions.items():
            if current_time - session_data['connected_at'] > inactive_threshold:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            if session_id in active_sessions:
                del active_sessions[session_id]
            if session_id in audio_engines:
                del audio_engines[session_id]

    # Start cleanup task
    @socketio.on('start_cleanup_task')
    def start_cleanup():
        """Start background cleanup task"""
        socketio.start_background_task(lambda: [
            time.sleep(60), cleanup_inactive_sessions()
        ] and None or start_cleanup())