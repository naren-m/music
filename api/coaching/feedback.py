"""
Real-time Coaching and Feedback System

Provides intelligent, adaptive coaching for Carnatic music learning
with personalized feedback and improvement recommendations.
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import websockets
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..models import User, Exercise, Progress, Recording

class FeedbackType(Enum):
    PITCH = "pitch"
    RHYTHM = "rhythm"
    TONE = "tone"
    TECHNIQUE = "technique"
    EXPRESSION = "expression"

class SeverityLevel(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

@dataclass
class CoachingFeedback:
    type: FeedbackType
    severity: SeverityLevel
    message: str
    suggestion: str
    confidence: float
    timestamp: datetime
    swara_context: Optional[str] = None
    technical_details: Optional[Dict[str, Any]] = None

@dataclass
class RealTimeFeedback:
    current_pitch: float
    target_pitch: float
    cent_deviation: float
    confidence: float
    stability: float
    tone_quality: float
    feedback: List[CoachingFeedback]

class RealTimeCoach:
    """
    Advanced real-time coaching system that provides instant feedback
    during practice sessions with adaptive learning algorithms.
    """

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Analysis parameters
        self.hop_length = 512
        self.n_fft = 2048

        # Coaching parameters
        self.pitch_tolerance = 20  # cents
        self.stability_window = 10  # frames
        self.confidence_threshold = 0.7

        # Feedback history for adaptive coaching
        self.feedback_history: List[CoachingFeedback] = []
        self.user_progress_cache: Dict[int, Dict] = {}

        # Swara frequency mapping (Carnatic tuning)
        self.swara_frequencies = {
            'Sa': 261.63,   # C4
            'Ri': 293.66,   # D4 (Shuddha Ri)
            'Ga': 329.63,   # E4 (Shuddha Ga)
            'Ma': 349.23,   # F4 (Shuddha Ma)
            'Pa': 392.00,   # G4
            'Da': 440.00,   # A4 (Shuddha Da)
            'Ni': 493.88    # B4 (Shuddha Ni)
        }

        # Initialize ML models for tone quality assessment
        self._load_tone_models()

    def _load_tone_models(self):
        """Load pre-trained models for tone quality analysis"""
        # In production, load actual ML models
        # For now, use heuristic approaches
        pass

    async def process_audio_stream(
        self,
        audio_data: np.ndarray,
        user_id: int,
        target_swara: str,
        exercise_context: Optional[Dict] = None
    ) -> RealTimeFeedback:
        """
        Process real-time audio stream and provide instant coaching feedback
        """
        try:
            # Extract audio features
            features = self._extract_audio_features(audio_data)

            # Analyze pitch and stability
            pitch_analysis = self._analyze_pitch(features, target_swara)

            # Assess tone quality
            tone_analysis = self._analyze_tone_quality(features)

            # Generate contextual feedback
            feedback_messages = await self._generate_feedback(
                pitch_analysis,
                tone_analysis,
                user_id,
                target_swara,
                exercise_context
            )

            # Create real-time feedback response
            feedback = RealTimeFeedback(
                current_pitch=pitch_analysis['frequency'],
                target_pitch=self.swara_frequencies[target_swara],
                cent_deviation=pitch_analysis['cent_deviation'],
                confidence=pitch_analysis['confidence'],
                stability=pitch_analysis['stability'],
                tone_quality=tone_analysis['quality_score'],
                feedback=feedback_messages
            )

            # Store feedback for adaptive learning
            await self._store_feedback_session(user_id, feedback, exercise_context)

            return feedback

        except Exception as e:
            print(f"Error processing audio stream: {e}")
            return self._create_error_feedback()

    def _extract_audio_features(self, audio_data: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract comprehensive audio features for analysis"""

        # Fundamental frequency detection
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_data,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sample_rate,
            hop_length=self.hop_length
        )

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio_data, sr=self.sample_rate, hop_length=self.hop_length
        )[0]

        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=audio_data, sr=self.sample_rate, hop_length=self.hop_length
        )[0]

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio_data, sr=self.sample_rate, hop_length=self.hop_length
        )[0]

        # Zero crossing rate (indicates breathiness)
        zcr = librosa.feature.zero_crossing_rate(
            audio_data, hop_length=self.hop_length
        )[0]

        # MFCC features
        mfcc = librosa.feature.mfcc(
            y=audio_data, sr=self.sample_rate, n_mfcc=13, hop_length=self.hop_length
        )

        # Chroma features (for swara identification)
        chroma = librosa.feature.chroma_cqt(
            y=audio_data, sr=self.sample_rate, hop_length=self.hop_length
        )

        # RMS energy
        rms = librosa.feature.rms(
            y=audio_data, hop_length=self.hop_length
        )[0]

        return {
            'f0': f0,
            'voiced_flag': voiced_flag,
            'voiced_probs': voiced_probs,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'zcr': zcr,
            'mfcc': mfcc,
            'chroma': chroma,
            'rms': rms
        }

    def _analyze_pitch(self, features: Dict, target_swara: str) -> Dict[str, float]:
        """Analyze pitch accuracy and stability"""

        f0 = features['f0']
        voiced_probs = features['voiced_probs']

        # Filter out unvoiced segments
        voiced_f0 = f0[voiced_probs > self.confidence_threshold]

        if len(voiced_f0) == 0:
            return {
                'frequency': 0.0,
                'cent_deviation': 0.0,
                'confidence': 0.0,
                'stability': 0.0
            }

        # Calculate average pitch
        avg_pitch = np.nanmean(voiced_f0)

        # Calculate cent deviation from target
        target_freq = self.swara_frequencies[target_swara]
        cent_deviation = 1200 * np.log2(avg_pitch / target_freq) if avg_pitch > 0 else 0

        # Calculate pitch stability (standard deviation in cents)
        pitch_stability = 0.0
        if len(voiced_f0) > 1:
            pitch_cents = 1200 * np.log2(voiced_f0 / target_freq)
            pitch_stability = 1.0 - min(np.std(pitch_cents) / 50.0, 1.0)  # Normalize

        # Overall confidence based on voiced probability and stability
        confidence = np.mean(voiced_probs) * pitch_stability

        return {
            'frequency': avg_pitch,
            'cent_deviation': cent_deviation,
            'confidence': confidence,
            'stability': pitch_stability
        }

    def _analyze_tone_quality(self, features: Dict) -> Dict[str, float]:
        """Analyze tone quality using spectral features"""

        spectral_centroid = features['spectral_centroid']
        spectral_bandwidth = features['spectral_bandwidth']
        zcr = features['zcr']
        rms = features['rms']

        # Calculate tone quality metrics

        # Breathiness indicator (high ZCR suggests breathy tone)
        breathiness = np.mean(zcr)
        breathiness_score = max(0, 1.0 - breathiness * 10)  # Lower is better

        # Spectral clarity (consistent spectral centroid)
        spectral_stability = 1.0 - min(np.std(spectral_centroid) / np.mean(spectral_centroid), 1.0)

        # Energy consistency (stable RMS)
        energy_stability = 1.0 - min(np.std(rms) / np.mean(rms), 1.0) if np.mean(rms) > 0 else 0

        # Overall tone quality score
        quality_score = (breathiness_score + spectral_stability + energy_stability) / 3

        return {
            'quality_score': quality_score,
            'breathiness': breathiness_score,
            'spectral_stability': spectral_stability,
            'energy_stability': energy_stability
        }

    async def _generate_feedback(
        self,
        pitch_analysis: Dict,
        tone_analysis: Dict,
        user_id: int,
        target_swara: str,
        exercise_context: Optional[Dict]
    ) -> List[CoachingFeedback]:
        """Generate contextual coaching feedback"""

        feedback_messages = []
        timestamp = datetime.now()

        # Get user's progress history for personalized feedback
        user_progress = await self._get_user_progress(user_id)

        # Pitch feedback
        cent_deviation = pitch_analysis['cent_deviation']
        if abs(cent_deviation) > self.pitch_tolerance:
            severity = self._determine_pitch_severity(cent_deviation)

            if cent_deviation > 0:
                message = f"You're singing {abs(cent_deviation):.1f} cents sharp"
                suggestion = "Relax your throat and sing slightly lower"
            else:
                message = f"You're singing {abs(cent_deviation):.1f} cents flat"
                suggestion = "Provide more breath support and lift the pitch"

            feedback_messages.append(CoachingFeedback(
                type=FeedbackType.PITCH,
                severity=severity,
                message=message,
                suggestion=suggestion,
                confidence=pitch_analysis['confidence'],
                timestamp=timestamp,
                swara_context=target_swara,
                technical_details={'cent_deviation': cent_deviation}
            ))

        # Stability feedback
        stability = pitch_analysis['stability']
        if stability < 0.7:
            feedback_messages.append(CoachingFeedback(
                type=FeedbackType.TECHNIQUE,
                severity=SeverityLevel.MODERATE,
                message=f"Pitch stability is {stability:.1%}. Work on steadiness",
                suggestion="Focus on breath control and maintain consistent airflow",
                confidence=stability,
                timestamp=timestamp,
                swara_context=target_swara
            ))

        # Tone quality feedback
        tone_quality = tone_analysis['quality_score']
        if tone_quality < 0.6:
            feedback_messages.append(CoachingFeedback(
                type=FeedbackType.TONE,
                severity=SeverityLevel.MODERATE,
                message="Tone quality needs improvement",
                suggestion="Focus on breath support and vocal placement",
                confidence=tone_quality,
                timestamp=timestamp,
                technical_details=tone_analysis
            ))

        # Personalized feedback based on user history
        personalized_feedback = self._generate_personalized_feedback(
            user_progress, pitch_analysis, tone_analysis, target_swara
        )
        feedback_messages.extend(personalized_feedback)

        return feedback_messages

    def _determine_pitch_severity(self, cent_deviation: float) -> SeverityLevel:
        """Determine feedback severity based on pitch deviation"""
        abs_deviation = abs(cent_deviation)

        if abs_deviation < 10:
            return SeverityLevel.MINOR
        elif abs_deviation < 25:
            return SeverityLevel.MODERATE
        elif abs_deviation < 50:
            return SeverityLevel.MAJOR
        else:
            return SeverityLevel.CRITICAL

    def _generate_personalized_feedback(
        self,
        user_progress: Dict,
        pitch_analysis: Dict,
        tone_analysis: Dict,
        target_swara: str
    ) -> List[CoachingFeedback]:
        """Generate personalized feedback based on user's learning history"""

        feedback_messages = []
        timestamp = datetime.now()

        # Check for recurring issues
        if target_swara in user_progress.get('problem_swaras', []):
            feedback_messages.append(CoachingFeedback(
                type=FeedbackType.TECHNIQUE,
                severity=SeverityLevel.MODERATE,
                message=f"Remember, {target_swara} has been challenging for you",
                suggestion=f"Practice {target_swara} with slow, sustained notes first",
                confidence=0.8,
                timestamp=timestamp,
                swara_context=target_swara
            ))

        # Progress encouragement
        if user_progress.get('improvement_trend', 0) > 0.1:
            feedback_messages.append(CoachingFeedback(
                type=FeedbackType.EXPRESSION,
                severity=SeverityLevel.MINOR,
                message="Great progress! Your accuracy has improved significantly",
                suggestion="Keep up the consistent practice",
                confidence=1.0,
                timestamp=timestamp
            ))

        return feedback_messages

    async def _get_user_progress(self, user_id: int) -> Dict:
        """Retrieve user's progress and learning patterns"""

        if user_id in self.user_progress_cache:
            cache_entry = self.user_progress_cache[user_id]
            if datetime.now() - cache_entry['timestamp'] < timedelta(minutes=5):
                return cache_entry['data']

        # Fetch from database
        try:
            with get_db_session() as db:
                recent_progress = db.query(Progress).filter(
                    Progress.user_id == user_id,
                    Progress.created_at >= datetime.now() - timedelta(days=30)
                ).all()

                # Analyze patterns
                progress_data = {
                    'problem_swaras': self._identify_problem_swaras(recent_progress),
                    'improvement_trend': self._calculate_improvement_trend(recent_progress),
                    'practice_consistency': self._calculate_practice_consistency(recent_progress)
                }

                # Cache results
                self.user_progress_cache[user_id] = {
                    'data': progress_data,
                    'timestamp': datetime.now()
                }

                return progress_data

        except Exception as e:
            print(f"Error fetching user progress: {e}")
            return {}

    def _identify_problem_swaras(self, progress_records: List[Progress]) -> List[str]:
        """Identify swaras that consistently cause problems for the user"""
        swara_accuracy = {}

        for record in progress_records:
            if record.exercise_data and 'target_swara' in record.exercise_data:
                swara = record.exercise_data['target_swara']
                accuracy = record.accuracy_score

                if swara not in swara_accuracy:
                    swara_accuracy[swara] = []
                swara_accuracy[swara].append(accuracy)

        # Identify swaras with consistently low accuracy
        problem_swaras = []
        for swara, accuracies in swara_accuracy.items():
            avg_accuracy = np.mean(accuracies)
            if avg_accuracy < 0.7 and len(accuracies) >= 3:
                problem_swaras.append(swara)

        return problem_swaras

    def _calculate_improvement_trend(self, progress_records: List[Progress]) -> float:
        """Calculate user's improvement trend over recent sessions"""
        if len(progress_records) < 5:
            return 0.0

        # Sort by date
        sorted_records = sorted(progress_records, key=lambda x: x.created_at)

        # Calculate trend using linear regression
        accuracies = [record.accuracy_score for record in sorted_records[-10:]]
        x = np.arange(len(accuracies))

        if len(accuracies) > 1:
            slope = np.polyfit(x, accuracies, 1)[0]
            return slope

        return 0.0

    def _calculate_practice_consistency(self, progress_records: List[Progress]) -> float:
        """Calculate how consistently the user practices"""
        if not progress_records:
            return 0.0

        # Calculate days between practice sessions
        dates = [record.created_at.date() for record in progress_records]
        unique_dates = sorted(set(dates))

        if len(unique_dates) < 2:
            return 0.0

        # Calculate average days between sessions
        date_diffs = [(unique_dates[i+1] - unique_dates[i]).days
                      for i in range(len(unique_dates)-1)]
        avg_gap = np.mean(date_diffs)

        # Return consistency score (lower gap = higher consistency)
        return max(0, 1.0 - (avg_gap - 1) / 6)  # Normalize assuming ideal is daily practice

    async def _store_feedback_session(
        self,
        user_id: int,
        feedback: RealTimeFeedback,
        exercise_context: Optional[Dict]
    ):
        """Store feedback session for learning analytics"""
        try:
            session_data = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'pitch_data': {
                    'current_pitch': feedback.current_pitch,
                    'target_pitch': feedback.target_pitch,
                    'cent_deviation': feedback.cent_deviation,
                    'confidence': feedback.confidence,
                    'stability': feedback.stability
                },
                'tone_quality': feedback.tone_quality,
                'feedback_count': len(feedback.feedback),
                'exercise_context': exercise_context
            }

            # Store in database (simplified for demo)
            # In production, this would use proper database storage
            print(f"Storing feedback session: {json.dumps(session_data, indent=2)}")

        except Exception as e:
            print(f"Error storing feedback session: {e}")

    def _create_error_feedback(self) -> RealTimeFeedback:
        """Create error feedback when processing fails"""
        return RealTimeFeedback(
            current_pitch=0.0,
            target_pitch=0.0,
            cent_deviation=0.0,
            confidence=0.0,
            stability=0.0,
            tone_quality=0.0,
            feedback=[CoachingFeedback(
                type=FeedbackType.TECHNIQUE,
                severity=SeverityLevel.MINOR,
                message="Unable to analyze audio. Please check your microphone",
                suggestion="Ensure your microphone is working and try again",
                confidence=0.0,
                timestamp=datetime.now()
            )]
        )

class AdaptiveLearningEngine:
    """
    Machine learning engine that adapts coaching strategies based on
    individual learning patterns and progress.
    """

    def __init__(self):
        self.learning_models = {}
        self.user_profiles = {}

    async def update_user_model(self, user_id: int, session_data: Dict):
        """Update user's learning model with new session data"""
        # Implementation for adaptive learning model updates
        pass

    def recommend_exercises(self, user_id: int) -> List[Dict]:
        """Recommend personalized exercises based on learning patterns"""
        # Implementation for exercise recommendations
        return []

    def adjust_difficulty(self, user_id: int, current_level: int) -> int:
        """Dynamically adjust exercise difficulty"""
        # Implementation for adaptive difficulty adjustment
        return current_level

# WebSocket handler for real-time feedback
class RealtimeCoachingHandler:
    """WebSocket handler for real-time coaching sessions"""

    def __init__(self):
        self.coach = RealTimeCoach()
        self.active_sessions: Dict[str, Dict] = {}

    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection for coaching session"""
        session_id = f"session_{datetime.now().timestamp()}"

        try:
            await websocket.send(json.dumps({
                'type': 'connection_established',
                'session_id': session_id
            }))

            async for message in websocket:
                await self.process_message(websocket, session_id, message)

        except websockets.exceptions.ConnectionClosed:
            print(f"Session {session_id} disconnected")
        except Exception as e:
            print(f"Error in coaching session {session_id}: {e}")
        finally:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    async def process_message(self, websocket, session_id: str, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)

            if data['type'] == 'start_session':
                await self.start_coaching_session(websocket, session_id, data)
            elif data['type'] == 'audio_data':
                await self.process_audio_feedback(websocket, session_id, data)
            elif data['type'] == 'end_session':
                await self.end_coaching_session(websocket, session_id)

        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f"Error processing message: {e}"
            }))

    async def start_coaching_session(self, websocket, session_id: str, data: Dict):
        """Start a new coaching session"""
        self.active_sessions[session_id] = {
            'user_id': data.get('user_id'),
            'target_swara': data.get('target_swara'),
            'exercise_context': data.get('exercise_context'),
            'start_time': datetime.now()
        }

        await websocket.send(json.dumps({
            'type': 'session_started',
            'session_id': session_id
        }))

    async def process_audio_feedback(self, websocket, session_id: str, data: Dict):
        """Process audio data and send real-time feedback"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]

        # Convert audio data (base64 encoded) to numpy array
        import base64
        audio_bytes = base64.b64decode(data['audio_data'])
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)

        # Process audio and generate feedback
        feedback = await self.coach.process_audio_stream(
            audio_array,
            session['user_id'],
            session['target_swara'],
            session['exercise_context']
        )

        # Send feedback to client
        await websocket.send(json.dumps({
            'type': 'real_time_feedback',
            'feedback': asdict(feedback)
        }))

    async def end_coaching_session(self, websocket, session_id: str):
        """End coaching session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            duration = datetime.now() - session['start_time']

            await websocket.send(json.dumps({
                'type': 'session_ended',
                'duration_seconds': duration.total_seconds()
            }))

            del self.active_sessions[session_id]

# Initialize coaching system
coaching_handler = RealtimeCoachingHandler()