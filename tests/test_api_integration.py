"""
API Integration Tests
Tests for Flask API endpoints and WebSocket functionality
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch
from flask import Flask
from flask_socketio import SocketIOTestClient
from api import create_app


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_guest_login(self, client):
        """Test guest session creation endpoint."""
        response = client.post('/api/auth/guest',
                             data=json.dumps({'human_verification': True}),
                             content_type='application/json',
                             headers={'User-Agent': 'Mozilla/5.0 (Test Client)'})
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user_id' in data
        assert data['user_type'] == 'guest'
    
    def test_session_info(self, client):
        """Test retrieving current session info."""
        # Authenticate as guest first
        self.test_guest_login(client)
        
        response = client.get('/api/auth/session',
                            headers={'User-Agent': 'Mozilla/5.0 (Test Client)'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is True
        assert 'user_id' in data
        assert data['user_type'] == 'guest'
    
    def test_verify_session(self, client):
        """Test verifying active session."""
        # Authenticate first
        self.test_guest_login(client)
        
        response = client.get('/api/auth/verify',
                            headers={'User-Agent': 'Mozilla/5.0 (Test Client)'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is True
    
    def test_logout_endpoint(self, client):
        """Test user logout endpoint."""
        # Authenticate first
        self.test_guest_login(client)
        
        response = client.post('/api/auth/logout',
                             headers={'User-Agent': 'Mozilla/5.0 (Test Client)'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logged_out'] is True


class TestLearningAPI:
    """Test learning module API endpoints."""
    
    @pytest.fixture
    def authenticated_client(self, client):
        """Get authenticated client by creating a user profile."""
        profile_data = {
            'email': 'learner@example.com',
            'username': 'learner123',
            'full_name': 'Learning User',
            'skill_level': 'intermediate',
            'learning_goals': ['beginner']
        }
        
        response = client.post('/api/v1/learning/profile',
                             data=json.dumps(profile_data),
                             content_type='application/json')
        assert response.status_code == 201
        return client
    
    def _start_exercise(self, client):
        exercise_data = {
            'exercise_type': 'single_swara'
        }
        response = client.post('/api/v1/learning/exercises/swara/start',
                             data=json.dumps(exercise_data),
                             content_type='application/json')
        return response

    def test_start_swara_exercise(self, authenticated_client):
        """Test starting swara recognition exercise."""
        client = authenticated_client
        response = self._start_exercise(client)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'exercise_config' in data
 
    def test_submit_exercise_result(self, authenticated_client):
        """Test stopping swara exercise and getting results."""
        client = authenticated_client
 
        # Start exercise first
        self._start_exercise(client)
         
        response = client.post('/api/v1/learning/exercises/swara/stop')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert 'overall_accuracy' in data['result']
    
    def test_get_user_progress(self, authenticated_client):
        """Test retrieving user progress analytics."""
        client = authenticated_client
        
        response = client.get('/api/v1/learning/progress/analytics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'overall_skill_level' in data
        assert 'total_practice_time' in data
        assert 'practice_streak' in data


class TestAudioAPI:
    """Test audio processing API endpoints."""
    
    def test_audio_config_endpoint(self, client):
        """Test audio configuration endpoint."""
        response = client.get('/api/audio/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sampleRate' in data
        assert 'fftSize' in data
        assert 'bufferSize' in data
    
    def test_detect_shruti_endpoint(self, client):
        """Test REST-based shruti detection endpoint."""
        shruti_data = {
            'frequency': 261.63,  # Sa (C4)
            'base_sa': 261.63
        }
        
        response = client.post('/api/v1/learning/detect/shruti',
                             data=json.dumps(shruti_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'detected_frequency' in data
        assert 'closest_shruti' in data
        assert data['closest_shruti']['name'] == 'Shadja'
    
    def test_invalid_shruti_data(self, client):
        """Test handling of invalid shruti detection data."""
        invalid_data = {
            # Missing frequency
            'base_sa': 261.63
        }
        
        response = client.post('/api/v1/learning/detect/shruti',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestWebSocketIntegration:
    """Test WebSocket real-time functionality."""
    
    @pytest.fixture
    def socketio_client(self, flask_app):
        """Create SocketIO test client."""
        return SocketIOTestClient(flask_app, flask_app.extensions['socketio'])
    
    def test_websocket_connection(self, socketio_client):
        """Test WebSocket connection."""
        received = socketio_client.get_received()
        assert len(received) > 0
        assert received[0]['name'] == 'connected'
        assert 'Connected to real-time audio service.' in received[0]['args'][0]['message']
    
    def test_start_exercise_event(self, socketio_client):
        """Test start exercise WebSocket event."""
        socketio_client.emit('start_exercise', {'exercise_type': 'free_practice'})
        received = socketio_client.get_received()
        
        # Expect connected first, then exercise_started
        assert len(received) > 1
        assert received[1]['name'] == 'exercise_started'
    
    def test_pitch_detection_stream(self, socketio_client):
        """Test real-time pitch detection streaming."""
        # Start free practice
        socketio_client.emit('start_exercise', {'exercise_type': 'free_practice'})
        
        # Generate a clean 261.63Hz (Sa) sine wave
        import numpy as np
        sample_rate = 44100
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
        audio_data = np.sin(2 * np.pi * 261.63 * t).tolist()
        
        audio_chunk = {
            'audio_data': audio_data,
            'timestamp': 1234567890
        }
        
        socketio_client.emit('audio_chunk', audio_chunk)
        received = socketio_client.get_received()
        
        # Should receive shruti_detected
        shruti_result = next(
            (msg for msg in received if msg['name'] == 'shruti_detected'), 
            None
        )
        assert shruti_result is not None
        assert 'frequency' in shruti_result['args'][0]
        assert shruti_result['args'][0]['shruti_name'] == 'Shadja'


class TestErrorHandlingAPI:
    """Test API error handling and edge cases."""
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get('/api/v1/learning/progress/analytics')
        assert response.status_code == 401
        
        response = client.post('/api/v1/learning/exercises/swara/start')
        assert response.status_code == 404
    
    def test_invalid_json_data(self, client):
        """Test handling of invalid JSON data."""
        # Get session first
        client.post('/api/v1/learning/profile',
                    data=json.dumps({
                        'email': 'learner@example.com',
                        'username': 'learner123',
                        'full_name': 'Learning User',
                        'skill_level': 'intermediate',
                        'learning_goals': ['beginner']
                    }),
                    content_type='application/json')

        response = client.post('/api/v1/learning/exercises/swara/start',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400


@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API performance characteristics."""
    
    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import time
        
        def make_request():
            start_time = time.time()
            response = client.post('/api/v1/learning/detect/shruti',
                                 data=json.dumps({'frequency': 261.63}),
                                 content_type='application/json')
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        assert all(status == 200 for status in status_codes)
        assert all(time < 1.0 for time in response_times)  # Under 1 second
    
    async def test_memory_efficiency(self, client):
        """Test memory efficiency during processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple audio requests
        for _ in range(50):
            client.post('/api/v1/learning/detect/shruti',
                       data=json.dumps({'frequency': 261.63}),
                       content_type='application/json')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024