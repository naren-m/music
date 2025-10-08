"""
Advanced Audio Recording and Playback System
Carnatic Music Learning Platform
"""

import os
import io
import uuid
import wave
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from core.services.audio_engine import AudioEngine, AudioConfig
from config.database import get_db_session, Recording, User, Exercise

# Configure Blueprint
recording_bp = Blueprint('recording', __name__, url_prefix='/api/v1/recording')

@dataclass
class RecordingConfig:
    """Configuration for audio recording and processing"""

    # File format settings
    sample_rate: int = 44100
    channels: int = 1
    bit_depth: int = 16
    format: str = 'wav'

    # Quality settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_duration: int = 300  # 5 minutes
    min_duration: float = 0.5  # 500ms

    # Processing settings
    normalize: bool = True
    noise_reduction: bool = True
    apply_filtering: bool = True

    # Storage settings
    upload_directory: str = 'recordings'
    temp_directory: str = 'temp_recordings'

    # Analysis settings
    pitch_analysis: bool = True
    spectral_analysis: bool = True
    onset_detection: bool = True
    tempo_detection: bool = True

class AudioRecordingProcessor:
    """Advanced audio recording processor with analysis capabilities"""

    def __init__(self, config: RecordingConfig = None):
        self.config = config or RecordingConfig()
        self.audio_engine = AudioEngine()

        # Create directories
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = [
            self.config.upload_directory,
            self.config.temp_directory,
            f"{self.config.upload_directory}/processed",
            f"{self.config.upload_directory}/compressed"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def validate_audio_data(self, audio_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded audio data"""
        try:
            # Check file size
            file_size = len(audio_data)
            if file_size > self.config.max_file_size:
                return {
                    'valid': False,
                    'error': f'File size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({self.config.max_file_size / 1024 / 1024}MB)'
                }

            # Check file extension
            allowed_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
            file_ext = Path(filename).suffix.lower()
            if file_ext not in allowed_extensions:
                return {
                    'valid': False,
                    'error': f'Unsupported file format: {file_ext}'
                }

            # Validate audio content
            try:
                audio_buffer = io.BytesIO(audio_data)
                audio, sr = librosa.load(audio_buffer, sr=None)

                duration = len(audio) / sr
                if duration < self.config.min_duration:
                    return {
                        'valid': False,
                        'error': f'Recording too short: {duration:.1f}s (minimum: {self.config.min_duration}s)'
                    }

                if duration > self.config.max_duration:
                    return {
                        'valid': False,
                        'error': f'Recording too long: {duration:.1f}s (maximum: {self.config.max_duration}s)'
                    }

                return {
                    'valid': True,
                    'duration': duration,
                    'sample_rate': sr,
                    'channels': audio.ndim,
                    'file_size': file_size
                }

            except Exception as e:
                return {
                    'valid': False,
                    'error': f'Invalid audio file: {str(e)}'
                }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }

    def process_recording(self, audio_data: bytes, filename: str,
                         user_id: int, exercise_id: Optional[int] = None) -> Dict[str, Any]:
        """Process and analyze uploaded recording"""
        try:
            # Generate unique filename
            recording_id = str(uuid.uuid4())
            secure_name = secure_filename(filename)
            base_name = Path(secure_name).stem

            # Process audio
            audio_buffer = io.BytesIO(audio_data)
            audio, original_sr = librosa.load(audio_buffer, sr=None)

            # Resample to standard rate if needed
            if original_sr != self.config.sample_rate:
                audio = librosa.resample(audio, orig_sr=original_sr, target_sr=self.config.sample_rate)

            # Apply audio processing
            processed_audio = self._apply_audio_processing(audio)

            # Generate file paths
            wav_filename = f"{recording_id}_{base_name}.wav"
            compressed_filename = f"{recording_id}_{base_name}_compressed.flac"

            wav_path = Path(self.config.upload_directory) / wav_filename
            compressed_path = Path(self.config.upload_directory) / "compressed" / compressed_filename

            # Save processed audio
            sf.write(wav_path, processed_audio, self.config.sample_rate)
            sf.write(compressed_path, processed_audio, self.config.sample_rate, format='FLAC')

            # Analyze audio
            analysis_results = self._analyze_audio(processed_audio)

            # Create database record
            recording_data = {
                'user_id': user_id,
                'exercise_id': exercise_id,
                'filename': wav_filename,
                'file_path': str(wav_path),
                'file_size': os.path.getsize(wav_path),
                'duration': len(processed_audio) / self.config.sample_rate,
                'sample_rate': self.config.sample_rate,
                'channels': 1,
                'format': 'wav',
                'analysis_results': analysis_results,
                'overall_accuracy': analysis_results.get('overall_accuracy', 0.0),
                'feedback_data': self._generate_feedback(analysis_results),
                'recorded_at': datetime.now(timezone.utc),
                'is_processed': True,
                'processed_at': datetime.now(timezone.utc)
            }

            with get_db_session() as session:
                recording = Recording(**recording_data)
                session.add(recording)
                session.flush()

                return {
                    'success': True,
                    'recording_id': recording.id,
                    'filename': wav_filename,
                    'duration': recording.duration,
                    'file_size': recording.file_size,
                    'analysis_results': analysis_results,
                    'feedback': recording.feedback_data,
                    'compressed_url': f"/api/v1/recording/{recording.id}/download/compressed"
                }

        except Exception as e:
            current_app.logger.error(f"Recording processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _apply_audio_processing(self, audio: np.ndarray) -> np.ndarray:
        """Apply audio processing pipeline"""
        processed = audio.copy()

        # Normalize audio
        if self.config.normalize:
            processed = librosa.util.normalize(processed)

        # Apply noise reduction
        if self.config.noise_reduction:
            processed = self._reduce_noise(processed)

        # Apply filtering
        if self.config.apply_filtering:
            processed = self._apply_filters(processed)

        return processed

    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Apply noise reduction using spectral gating"""
        try:
            # Spectral gating noise reduction
            stft = librosa.stft(audio, hop_length=512, n_fft=2048)
            magnitude = np.abs(stft)
            phase = np.angle(stft)

            # Estimate noise floor
            noise_floor = np.percentile(magnitude, 10)

            # Apply spectral gating
            gate_threshold = noise_floor * 2.0
            magnitude_gated = np.where(magnitude > gate_threshold, magnitude, magnitude * 0.1)

            # Reconstruct audio
            stft_processed = magnitude_gated * np.exp(1j * phase)
            audio_processed = librosa.istft(stft_processed, hop_length=512)

            return audio_processed

        except Exception as e:
            current_app.logger.warning(f"Noise reduction failed: {e}")
            return audio

    def _apply_filters(self, audio: np.ndarray) -> np.ndarray:
        """Apply audio filters"""
        try:
            # High-pass filter to remove low-frequency noise
            sos = signal.butter(4, 80, 'hp', fs=self.config.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, audio)

            # Low-pass filter to prevent aliasing
            sos = signal.butter(4, 8000, 'lp', fs=self.config.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, filtered)

            return filtered

        except Exception as e:
            current_app.logger.warning(f"Filtering failed: {e}")
            return audio

    def _analyze_audio(self, audio: np.ndarray) -> Dict[str, Any]:
        """Comprehensive audio analysis"""
        analysis = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration': len(audio) / self.config.sample_rate,
            'sample_rate': self.config.sample_rate
        }

        try:
            # Basic audio statistics
            analysis['rms_energy'] = float(np.sqrt(np.mean(audio**2)))
            analysis['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(audio)))
            analysis['spectral_centroid'] = float(np.mean(librosa.feature.spectral_centroid(audio, sr=self.config.sample_rate)))

            # Pitch analysis
            if self.config.pitch_analysis:
                analysis['pitch_analysis'] = self._analyze_pitch(audio)

            # Spectral analysis
            if self.config.spectral_analysis:
                analysis['spectral_analysis'] = self._analyze_spectrum(audio)

            # Onset detection
            if self.config.onset_detection:
                analysis['onsets'] = self._detect_onsets(audio)

            # Tempo detection
            if self.config.tempo_detection:
                analysis['tempo_analysis'] = self._analyze_tempo(audio)

            # Overall quality metrics
            analysis['overall_accuracy'] = self._calculate_overall_accuracy(analysis)

        except Exception as e:
            current_app.logger.error(f"Audio analysis error: {e}")
            analysis['error'] = str(e)

        return analysis

    def _analyze_pitch(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detailed pitch analysis"""
        try:
            # Extract pitch using multiple methods
            f0_pyin, voiced_flag, voiced_probs = librosa.pyin(
                audio, fmin=80, fmax=800, sr=self.config.sample_rate,
                frame_length=2048, hop_length=512
            )

            # Remove unvoiced segments
            f0_clean = f0_pyin[voiced_flag]

            if len(f0_clean) > 0:
                return {
                    'fundamental_frequency': {
                        'mean': float(np.nanmean(f0_clean)),
                        'median': float(np.nanmedian(f0_clean)),
                        'std': float(np.nanstd(f0_clean)),
                        'min': float(np.nanmin(f0_clean)),
                        'max': float(np.nanmax(f0_clean))
                    },
                    'voiced_percentage': float(np.mean(voiced_flag)),
                    'pitch_confidence': float(np.mean(voiced_probs[voiced_flag])),
                    'pitch_stability': self._calculate_pitch_stability(f0_clean),
                    'shruti_detection': self._detect_shrutis(f0_clean)
                }
            else:
                return {
                    'error': 'No pitched content detected',
                    'voiced_percentage': 0.0
                }

        except Exception as e:
            return {'error': f'Pitch analysis failed: {e}'}

    def _analyze_spectrum(self, audio: np.ndarray) -> Dict[str, Any]:
        """Spectral analysis"""
        try:
            # Compute spectral features
            spectral_centroids = librosa.feature.spectral_centroid(audio, sr=self.config.sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(audio, sr=self.config.sample_rate)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(audio, sr=self.config.sample_rate)

            return {
                'spectral_centroid': {
                    'mean': float(np.mean(spectral_centroids)),
                    'std': float(np.std(spectral_centroids))
                },
                'spectral_rolloff': {
                    'mean': float(np.mean(spectral_rolloff)),
                    'std': float(np.std(spectral_rolloff))
                },
                'spectral_bandwidth': {
                    'mean': float(np.mean(spectral_bandwidth)),
                    'std': float(np.std(spectral_bandwidth))
                }
            }

        except Exception as e:
            return {'error': f'Spectral analysis failed: {e}'}

    def _detect_onsets(self, audio: np.ndarray) -> Dict[str, Any]:
        """Onset detection"""
        try:
            onset_frames = librosa.onset.onset_detect(
                audio, sr=self.config.sample_rate,
                units='time', hop_length=512
            )

            return {
                'onset_times': onset_frames.tolist(),
                'onset_count': len(onset_frames),
                'average_onset_interval': float(np.mean(np.diff(onset_frames))) if len(onset_frames) > 1 else 0.0
            }

        except Exception as e:
            return {'error': f'Onset detection failed: {e}'}

    def _analyze_tempo(self, audio: np.ndarray) -> Dict[str, Any]:
        """Tempo analysis"""
        try:
            tempo, beats = librosa.beat.beat_track(
                audio, sr=self.config.sample_rate,
                hop_length=512
            )

            beat_times = librosa.beat.tempo(onset_envelope=librosa.onset.onset_strength(audio, sr=self.config.sample_rate))

            return {
                'tempo_bpm': float(tempo),
                'beat_count': len(beats),
                'beat_consistency': self._calculate_beat_consistency(beats) if len(beats) > 2 else 0.0
            }

        except Exception as e:
            return {'error': f'Tempo analysis failed: {e}'}

    def _calculate_pitch_stability(self, f0_values: np.ndarray) -> float:
        """Calculate pitch stability metric"""
        if len(f0_values) < 2:
            return 0.0

        # Calculate coefficient of variation
        return float(1.0 - (np.std(f0_values) / np.mean(f0_values)))

    def _detect_shrutis(self, f0_values: np.ndarray) -> Dict[str, Any]:
        """Detect shruti patterns in pitch data"""
        try:
            # Use audio engine for shruti detection
            shruti_results = []

            for f0 in f0_values:
                if not np.isnan(f0) and f0 > 0:
                    result = self.audio_engine.detect_shruti(f0)
                    if result:
                        shruti_results.append(result)

            if shruti_results:
                # Aggregate results
                detected_shrutis = [r['shruti_name'] for r in shruti_results if 'shruti_name' in r]

                return {
                    'detected_shrutis': detected_shrutis,
                    'most_common_shruti': max(set(detected_shrutis), key=detected_shrutis.count) if detected_shrutis else None,
                    'shruti_accuracy': float(np.mean([r.get('accuracy', 0) for r in shruti_results])),
                    'total_detections': len(shruti_results)
                }
            else:
                return {'error': 'No shruti detections'}

        except Exception as e:
            return {'error': f'Shruti detection failed: {e}'}

    def _calculate_beat_consistency(self, beats: np.ndarray) -> float:
        """Calculate beat timing consistency"""
        beat_intervals = np.diff(beats)
        if len(beat_intervals) < 2:
            return 0.0

        # Calculate consistency as inverse of coefficient of variation
        cv = np.std(beat_intervals) / np.mean(beat_intervals)
        return float(max(0, 1 - cv))

    def _calculate_overall_accuracy(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall recording accuracy score"""
        scores = []

        # Pitch accuracy
        if 'pitch_analysis' in analysis and 'pitch_stability' in analysis['pitch_analysis']:
            scores.append(analysis['pitch_analysis']['pitch_stability'])

        # Voice quality (based on voiced percentage)
        if 'pitch_analysis' in analysis and 'voiced_percentage' in analysis['pitch_analysis']:
            scores.append(analysis['pitch_analysis']['voiced_percentage'])

        # Beat consistency
        if 'tempo_analysis' in analysis and 'beat_consistency' in analysis['tempo_analysis']:
            scores.append(analysis['tempo_analysis']['beat_consistency'])

        return float(np.mean(scores)) if scores else 0.0

    def _generate_feedback(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user-friendly feedback based on analysis"""
        feedback = {
            'overall_score': analysis.get('overall_accuracy', 0.0),
            'strengths': [],
            'improvements': [],
            'suggestions': []
        }

        try:
            # Pitch feedback
            if 'pitch_analysis' in analysis:
                pitch = analysis['pitch_analysis']

                if pitch.get('pitch_stability', 0) > 0.8:
                    feedback['strengths'].append("Excellent pitch stability")
                elif pitch.get('pitch_stability', 0) < 0.6:
                    feedback['improvements'].append("Work on maintaining steady pitch")
                    feedback['suggestions'].append("Practice with a drone or tanpura")

                if pitch.get('voiced_percentage', 0) > 0.8:
                    feedback['strengths'].append("Clear vocal tone throughout")
                elif pitch.get('voiced_percentage', 0) < 0.6:
                    feedback['improvements'].append("Maintain consistent vocal tone")
                    feedback['suggestions'].append("Focus on breath support and vocal clarity")

            # Tempo feedback
            if 'tempo_analysis' in analysis:
                tempo = analysis['tempo_analysis']

                if tempo.get('beat_consistency', 0) > 0.8:
                    feedback['strengths'].append("Consistent rhythm")
                elif tempo.get('beat_consistency', 0) < 0.6:
                    feedback['improvements'].append("Work on rhythmic consistency")
                    feedback['suggestions'].append("Practice with a metronome")

            # Shruti feedback
            if 'pitch_analysis' in analysis and 'shruti_detection' in analysis['pitch_analysis']:
                shruti = analysis['pitch_analysis']['shruti_detection']

                if shruti.get('shruti_accuracy', 0) > 0.8:
                    feedback['strengths'].append("Accurate shruti intonation")
                elif shruti.get('shruti_accuracy', 0) < 0.6:
                    feedback['improvements'].append("Focus on precise shruti intonation")
                    feedback['suggestions'].append("Practice individual swaras with reference pitch")

        except Exception as e:
            current_app.logger.warning(f"Feedback generation error: {e}")

        return feedback

# Initialize processor
processor = AudioRecordingProcessor()

# API Routes

@recording_bp.route('/upload', methods=['POST'])
def upload_recording():
    """Upload and process audio recording"""
    try:
        # Validate request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        user_id = request.form.get('user_id', type=int)
        exercise_id = request.form.get('exercise_id', type=int)

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        # Read and validate audio data
        audio_data = audio_file.read()
        validation = processor.validate_audio_data(audio_data, audio_file.filename)

        if not validation['valid']:
            return jsonify({'error': validation['error']}), 400

        # Process recording
        result = processor.process_recording(
            audio_data, audio_file.filename, user_id, exercise_id
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        current_app.logger.error(f"Recording upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@recording_bp.route('/<int:recording_id>', methods=['GET'])
def get_recording(recording_id: int):
    """Get recording information"""
    try:
        with get_db_session() as session:
            recording = session.query(Recording).filter_by(id=recording_id).first()

            if not recording:
                return jsonify({'error': 'Recording not found'}), 404

            return jsonify({
                'id': recording.id,
                'filename': recording.filename,
                'duration': recording.duration,
                'sample_rate': recording.sample_rate,
                'channels': recording.channels,
                'file_size': recording.file_size,
                'recorded_at': recording.recorded_at.isoformat(),
                'analysis_results': recording.analysis_results,
                'feedback_data': recording.feedback_data,
                'overall_accuracy': recording.overall_accuracy,
                'download_url': f'/api/v1/recording/{recording.id}/download',
                'stream_url': f'/api/v1/recording/{recording.id}/stream'
            })

    except Exception as e:
        current_app.logger.error(f"Get recording error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@recording_bp.route('/<int:recording_id>/download', methods=['GET'])
@recording_bp.route('/<int:recording_id>/download/<format_type>', methods=['GET'])
def download_recording(recording_id: int, format_type: str = 'original'):
    """Download recording file"""
    try:
        with get_db_session() as session:
            recording = session.query(Recording).filter_by(id=recording_id).first()

            if not recording:
                return jsonify({'error': 'Recording not found'}), 404

            if format_type == 'compressed':
                # Try compressed version first
                compressed_path = Path(processor.config.upload_directory) / "compressed" / f"{Path(recording.filename).stem}_compressed.flac"
                if compressed_path.exists():
                    return send_file(compressed_path, as_attachment=True)

            # Original file
            file_path = Path(recording.file_path)
            if not file_path.exists():
                return jsonify({'error': 'Recording file not found'}), 404

            return send_file(file_path, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Download recording error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@recording_bp.route('/<int:recording_id>/stream', methods=['GET'])
def stream_recording(recording_id: int):
    """Stream recording for web playback"""
    try:
        with get_db_session() as session:
            recording = session.query(Recording).filter_by(id=recording_id).first()

            if not recording:
                return jsonify({'error': 'Recording not found'}), 404

            file_path = Path(recording.file_path)
            if not file_path.exists():
                return jsonify({'error': 'Recording file not found'}), 404

            return send_file(
                file_path,
                mimetype='audio/wav',
                as_attachment=False,
                conditional=True
            )

    except Exception as e:
        current_app.logger.error(f"Stream recording error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@recording_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_recordings(user_id: int):
    """Get all recordings for a user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        exercise_id = request.args.get('exercise_id', type=int)

        with get_db_session() as session:
            query = session.query(Recording).filter_by(user_id=user_id)

            if exercise_id:
                query = query.filter_by(exercise_id=exercise_id)

            query = query.order_by(Recording.recorded_at.desc())

            # Pagination
            offset = (page - 1) * per_page
            recordings = query.offset(offset).limit(per_page).all()
            total_count = query.count()

            recording_list = []
            for recording in recordings:
                recording_list.append({
                    'id': recording.id,
                    'filename': recording.filename,
                    'duration': recording.duration,
                    'file_size': recording.file_size,
                    'recorded_at': recording.recorded_at.isoformat(),
                    'overall_accuracy': recording.overall_accuracy,
                    'exercise_id': recording.exercise_id,
                    'stream_url': f'/api/v1/recording/{recording.id}/stream'
                })

            return jsonify({
                'recordings': recording_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            })

    except Exception as e:
        current_app.logger.error(f"Get user recordings error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@recording_bp.route('/<int:recording_id>/analysis', methods=['POST'])
def reanalyze_recording(recording_id: int):
    """Re-run analysis on existing recording"""
    try:
        with get_db_session() as session:
            recording = session.query(Recording).filter_by(id=recording_id).first()

            if not recording:
                return jsonify({'error': 'Recording not found'}), 404

            file_path = Path(recording.file_path)
            if not file_path.exists():
                return jsonify({'error': 'Recording file not found'}), 404

            # Load and re-analyze audio
            audio, sr = librosa.load(file_path, sr=processor.config.sample_rate)
            analysis_results = processor._analyze_audio(audio)

            # Update database
            recording.analysis_results = analysis_results
            recording.overall_accuracy = analysis_results.get('overall_accuracy', 0.0)
            recording.feedback_data = processor._generate_feedback(analysis_results)
            recording.processed_at = datetime.now(timezone.utc)

            session.commit()

            return jsonify({
                'success': True,
                'recording_id': recording.id,
                'analysis_results': analysis_results,
                'feedback': recording.feedback_data
            })

    except Exception as e:
        current_app.logger.error(f"Re-analyze recording error: {e}")
        return jsonify({'error': 'Internal server error'}), 500