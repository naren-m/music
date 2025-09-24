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
from api import create_app, socketio


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_register_endpoint(self, client):
        """Test user registration endpoint."""
        user_data = {
            'email': 'test@example.com',
            'password': 'securepassword123',
            'name': 'Test User',
            'skill_level': 'beginner'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user_id' in data
        assert data['email'] == user_data['email']
    
    def test_login_endpoint(self, client):
        """Test user login endpoint."""
        # First register a user
        self.test_register_endpoint(client)
        
        login_data = {
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user_profile' in data
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_logout_endpoint(self, client):
        """Test user logout endpoint."""
        # Login first
        self.test_login_endpoint(client)
        
        response = client.post('/api/auth/logout')
        assert response.status_code == 200
    
    def test_password_strength_validation(self, client):
        """Test password strength validation."""
        weak_password_data = {
            'email': 'test2@example.com',
            'password': '123',  # Too weak
            'name': 'Test User 2',
            'skill_level': 'beginner'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(weak_password_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'password' in data['errors']


class TestLearningAPI:
    """Test learning module API endpoints."""
    
    @pytest.fixture
    def authenticated_client(self, client):
        """Get authenticated client with token."""
        # Register and login
        user_data = {
            'email': 'learner@example.com',
            'password': 'securepassword123',
            'name': 'Learning User',
            'skill_level': 'intermediate'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'email': user_data['email'],
                                       'password': user_data['password']
                                   }),
                                   content_type='application/json')
        
        token = json.loads(login_response.data)['access_token']
        return client, token
    
    def test_start_swara_exercise(self, authenticated_client):
        """Test starting swara recognition exercise."""
        client, token = authenticated_client
        
        exercise_data = {
            'exercise_type': 'swara_recognition',
            'difficulty': 'intermediate',
            'shruti_count': 12
        }
        
        response = client.post('/api/learning/exercises/swara/start',
                             data=json.dumps(exercise_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'exercise_config' in data
    
    def test_submit_exercise_result(self, authenticated_client):
        """Test submitting exercise results."""
        client, token = authenticated_client
        
        # Start exercise first
        start_response = self.test_start_swara_exercise(authenticated_client)
        session_id = json.loads(client.response.data)['session_id']
        
        result_data = {
            'session_id': session_id,
            'detected_swaras': ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Dha', 'Ni'],
            'accuracy_scores': [0.95, 0.87, 0.92, 0.89, 0.94, 0.88, 0.91],
            'total_time': 120,
            'completion_status': 'completed'
        }
        
        response = client.post('/api/learning/exercises/swara/submit',
                             data=json.dumps(result_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'overall_score' in data
        assert 'progress_update' in data
    
    def test_get_user_progress(self, authenticated_client):
        """Test retrieving user progress."""
        client, token = authenticated_client
        
        response = client.get('/api/learning/progress',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'module_progress' in data
        assert 'achievements' in data
        assert 'practice_stats' in data
    
    def test_get_recommendations(self, authenticated_client):
        """Test getting personalized recommendations."""
        client, token = authenticated_client
        
        response = client.get('/api/learning/recommendations',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommended_exercises' in data
        assert 'difficulty_adjustments' in data


class TestAudioAPI:
    """Test audio processing API endpoints."""
    
    def test_analyze_pitch_endpoint(self, client):
        """Test pitch analysis endpoint."""
        # Mock audio data
        audio_data = {
            'audio_samples': [0.1, 0.2, -0.1, -0.2] * 1000,  # Mock audio samples
            'sample_rate': 44100
        }
        
        response = client.post('/api/audio/analyze/pitch',
                             data=json.dumps(audio_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'detected_frequency' in data
        assert 'confidence' in data
    
    def test_analyze_shruti_endpoint(self, client):
        """Test shruti analysis endpoint."""
        shruti_data = {
            'frequency': 261.63,  # Sa (C4)
            'base_sa': 261.63
        }
        
        response = client.post('/api/audio/analyze/shruti',
                             data=json.dumps(shruti_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'shruti_name' in data
        assert 'shruti_number' in data
        assert 'deviation_cents' in data
        assert 'accuracy_score' in data
    
    def test_generate_tanpura_endpoint(self, client):
        """Test tanpura generation endpoint."""
        tanpura_config = {
            'base_frequency': 261.63,
            'raga': 'Bilaval',
            'duration': 10
        }
        
        response = client.post('/api/audio/generate/tanpura',
                             data=json.dumps(tanpura_config),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'audio/wav'
    
    def test_invalid_audio_data(self, client):
        """Test handling of invalid audio data."""
        invalid_data = {
            'audio_samples': [],  # Empty samples
            'sample_rate': 0  # Invalid sample rate
        }
        
        response = client.post('/api/audio/analyze/pitch',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestSocialAPI:
    """Test social features API endpoints."""
    
    def test_get_practice_groups(self, client):
        """Test getting practice groups."""
        response = client.get('/api/social/groups')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'groups' in data
    
    def test_create_practice_session(self, client):
        """Test creating collaborative practice session."""
        session_data = {
            'title': 'Evening Raga Practice',
            'description': 'Practice Yaman raga together',
            'raga': 'Yaman',
            'max_participants': 5,
            'start_time': '2024-01-01T18:00:00Z'
        }
        
        response = client.post('/api/social/sessions',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'session_id' in data


class TestWebSocketIntegration:
    """Test WebSocket real-time functionality."""
    
    @pytest.fixture
    def socketio_client(self, flask_app):
        """Create SocketIO test client."""
        return SocketIOTestClient(flask_app, socketio)
    
    def test_websocket_connection(self, socketio_client):
        """Test WebSocket connection."""
        received = socketio_client.get_received()
        assert len(received) > 0
        assert received[0]['name'] == 'connected'
        assert 'Connected to Carnatic Learning Server' in received[0]['args'][0]['message']
    
    def test_start_detection_event(self, socketio_client):
        """Test start detection WebSocket event."""
        socketio_client.emit('start_detection', {'mode': 'swara_recognition'})
        received = socketio_client.get_received()
        
        assert len(received) > 0
        assert received[0]['name'] == 'detection_started'
    
    def test_pitch_detection_stream(self, socketio_client):
        """Test real-time pitch detection streaming."""
        # Simulate starting detection
        socketio_client.emit('start_detection', {'mode': 'pitch_tracking'})
        
        # Simulate audio data streaming
        audio_chunk = {
            'audio_data': [0.1, 0.2, -0.1] * 100,
            'timestamp': 1234567890
        }
        
        socketio_client.emit('audio_chunk', audio_chunk)
        received = socketio_client.get_received()
        
        # Should receive pitch detection result
        pitch_result = next(
            (msg for msg in received if msg['name'] == 'pitch_detected'), 
            None
        )
        assert pitch_result is not None
        assert 'frequency' in pitch_result['args'][0]
    
    def test_exercise_feedback_event(self, socketio_client):
        """Test exercise feedback WebSocket event."""
        feedback_data = {
            'exercise_id': 'swara_001',
            'accuracy': 0.87,
            'detected_swara': 'Ga',
            'target_swara': 'Ga',
            'feedback_message': 'Good pitch accuracy!'
        }
        
        socketio_client.emit('exercise_feedback', feedback_data)
        received = socketio_client.get_received()
        
        feedback_update = next(
            (msg for msg in received if msg['name'] == 'feedback_update'),
            None
        )
        assert feedback_update is not None
    
    def test_milestone_achievement(self, socketio_client):
        """Test milestone achievement broadcast."""
        milestone_data = {
            'user_id': 'test_user_123',
            'milestone': 'swara_mastery_level_1',
            'achievement_date': '2024-01-01T12:00:00Z'
        }
        
        socketio_client.emit('milestone_achieved', milestone_data)
        received = socketio_client.get_received()
        
        milestone_notification = next(
            (msg for msg in received if msg['name'] == 'milestone_notification'),
            None
        )
        assert milestone_notification is not None
    
    def test_progress_update_event(self, socketio_client):
        """Test progress update WebSocket event."""
        progress_data = {
            'user_id': 'test_user_123',
            'module': 'swara_recognition',
            'progress_percentage': 75,
            'new_level': 'intermediate_plus'
        }
        
        socketio_client.emit('progress_update', progress_data)
        received = socketio_client.get_received()
        
        progress_updated = next(
            (msg for msg in received if msg['name'] == 'progress_updated'),
            None
        )
        assert progress_updated is not None
    
    def test_collaborative_session_events(self, socketio_client):
        """Test collaborative practice session events."""
        # Join session
        socketio_client.emit('join_session', {'session_id': 'practice_001'})
        
        # Simulate participant audio
        participant_audio = {
            'session_id': 'practice_001',
            'user_id': 'participant_1',
            'detected_pitch': 440.0,
            'accuracy': 0.92
        }
        
        socketio_client.emit('participant_audio', participant_audio)
        received = socketio_client.get_received()
        
        # Should receive session update
        session_update = next(
            (msg for msg in received if msg['name'] == 'session_update'),
            None
        )
        # Note: This would be implemented in actual collaborative features


class TestErrorHandlingAPI:
    """Test API error handling and edge cases."""
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get('/api/learning/progress')
        assert response.status_code == 401
        
        response = client.post('/api/learning/exercises/swara/start')
        assert response.status_code == 401
    
    def test_invalid_json_data(self, client):
        """Test handling of invalid JSON data."""
        response = client.post('/api/auth/register',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_data = {
            'email': 'test@example.com'
            # Missing password, name, skill_level
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data
    
    def test_rate_limiting(self, client):
        """Test API rate limiting."""
        # Make multiple rapid requests
        for _ in range(100):
            response = client.get('/api/audio/analyze/pitch',
                                data=json.dumps({'audio_samples': [], 'sample_rate': 44100}),
                                content_type='application/json')
            
            # Check if rate limiting kicks in
            if response.status_code == 429:
                assert 'rate limit' in response.data.decode().lower()
                break
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        # Create large audio data
        large_audio_data = {
            'audio_samples': [0.1] * 1000000,  # Very large audio sample
            'sample_rate': 44100
        }
        
        response = client.post('/api/audio/analyze/pitch',
                             data=json.dumps(large_audio_data),
                             content_type='application/json')
        
        # Should either process successfully or return appropriate error
        assert response.status_code in [200, 413, 400]  # Success, Payload too large, or Bad request


@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API performance characteristics."""
    
    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import time
        
        def make_request():
            start_time = time.time()
            response = client.get('/api/audio/analyze/pitch',
                                data=json.dumps({'audio_samples': [0.1] * 1000, 'sample_rate': 44100}),
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
        
        assert all(status in [200, 400] for status in status_codes)
        assert all(time < 1.0 for time in response_times)  # Under 1 second
    
    async def test_memory_efficiency(self, client):
        """Test memory efficiency during processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple audio requests
        for _ in range(50):
            client.post('/api/audio/analyze/pitch',
                       data=json.dumps({'audio_samples': [0.1] * 4410, 'sample_rate': 44100}),
                       content_type='application/json')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024