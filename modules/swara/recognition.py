"""
Advanced Swara Recognition Engine
Phase 2: Carnatic Music Learning Platform
"""

import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import tensorflow as tf
from scipy import signal
from sklearn.preprocessing import StandardScaler
import joblib

from core.models.shruti import ShrutiSystem, SwaraName

@dataclass
class SwaraRecognitionConfig:
    """Configuration for swara recognition system"""

    # Model settings
    model_path: str = "models/swara_classifier.h5"
    scaler_path: str = "models/feature_scaler.pkl"
    confidence_threshold: float = 0.7

    # Audio analysis
    sample_rate: int = 44100
    frame_size: int = 2048
    hop_length: int = 512
    n_mels: int = 128
    n_mfcc: int = 13

    # Temporal analysis
    context_frames: int = 5  # Number of frames for context
    smoothing_window: int = 3
    stability_threshold: float = 0.8

    # Training data
    training_samples_per_swara: int = 1000
    validation_split: float = 0.2

class SwaraFeatureExtractor:
    """Extract features for swara classification"""

    def __init__(self, config: SwaraRecognitionConfig):
        self.config = config
        self.shruti_system = ShrutiSystem()

    def extract_features(self, audio: np.ndarray, sr: int = None) -> np.ndarray:
        """Extract comprehensive features for swara recognition"""
        if sr is None:
            sr = self.config.sample_rate

        # Ensure mono audio
        if audio.ndim > 1:
            audio = np.mean(audio, axis=0)

        features = []

        try:
            # 1. Pitch-based features
            pitch_features = self._extract_pitch_features(audio, sr)
            features.extend(pitch_features)

            # 2. Spectral features
            spectral_features = self._extract_spectral_features(audio, sr)
            features.extend(spectral_features)

            # 3. MFCC features
            mfcc_features = self._extract_mfcc_features(audio, sr)
            features.extend(mfcc_features)

            # 4. Harmonic features
            harmonic_features = self._extract_harmonic_features(audio, sr)
            features.extend(harmonic_features)

            # 5. Temporal features
            temporal_features = self._extract_temporal_features(audio, sr)
            features.extend(temporal_features)

            # 6. Carnatic-specific features
            carnatic_features = self._extract_carnatic_features(audio, sr)
            features.extend(carnatic_features)

        except Exception as e:
            # Return zeros if feature extraction fails
            return np.zeros(self._get_feature_dimension())

        return np.array(features, dtype=np.float32)

    def _extract_pitch_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract pitch-related features"""
        features = []

        try:
            # Fundamental frequency
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio, fmin=80, fmax=800, sr=sr,
                frame_length=self.config.frame_size,
                hop_length=self.config.hop_length
            )

            # Remove unvoiced segments
            f0_voiced = f0[voiced_flag]

            if len(f0_voiced) > 0:
                features.extend([
                    np.nanmean(f0_voiced),              # Mean F0
                    np.nanstd(f0_voiced),               # F0 stability
                    np.nanmedian(f0_voiced),            # Median F0
                    np.nanpercentile(f0_voiced, 25),    # Q1 F0
                    np.nanpercentile(f0_voiced, 75),    # Q3 F0
                    np.mean(voiced_flag),               # Voicing probability
                    np.mean(voiced_probs[voiced_flag])  # Confidence
                ])
            else:
                features.extend([0.0] * 7)

            # Pitch contour features
            if len(f0_voiced) > 1:
                pitch_diff = np.diff(f0_voiced)
                features.extend([
                    np.mean(np.abs(pitch_diff)),        # Average pitch change
                    np.std(pitch_diff),                 # Pitch variation
                    np.sum(pitch_diff > 0) / len(pitch_diff),  # Ascending ratio
                ])
            else:
                features.extend([0.0] * 3)

        except Exception:
            features.extend([0.0] * 10)

        return features

    def _extract_spectral_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract spectral features"""
        features = []

        try:
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
            features.extend([
                np.mean(spectral_centroids),
                np.std(spectral_centroids)
            ])

            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            features.extend([
                np.mean(spectral_rolloff),
                np.std(spectral_rolloff)
            ])

            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
            features.extend([
                np.mean(spectral_bandwidth),
                np.std(spectral_bandwidth)
            ])

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio)
            features.extend([
                np.mean(zcr),
                np.std(zcr)
            ])

        except Exception:
            features.extend([0.0] * 8)

        return features

    def _extract_mfcc_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract MFCC features"""
        features = []

        try:
            # MFCC coefficients
            mfccs = librosa.feature.mfcc(
                y=audio, sr=sr,
                n_mfcc=self.config.n_mfcc,
                n_fft=self.config.frame_size,
                hop_length=self.config.hop_length
            )

            # Statistical measures of MFCCs
            for i in range(self.config.n_mfcc):
                features.extend([
                    np.mean(mfccs[i]),
                    np.std(mfccs[i])
                ])

            # Delta and delta-delta MFCCs
            mfcc_delta = librosa.feature.delta(mfccs)
            mfcc_delta2 = librosa.feature.delta(mfccs, order=2)

            features.extend([
                np.mean(np.mean(mfcc_delta, axis=1)),
                np.mean(np.std(mfcc_delta, axis=1)),
                np.mean(np.mean(mfcc_delta2, axis=1)),
                np.mean(np.std(mfcc_delta2, axis=1))
            ])

        except Exception:
            features.extend([0.0] * (self.config.n_mfcc * 2 + 4))

        return features

    def _extract_harmonic_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract harmonic content features"""
        features = []

        try:
            # Harmonic-percussive separation
            harmonic, percussive = librosa.effects.hpss(audio)

            # Harmonic ratio
            harmonic_energy = np.sum(harmonic ** 2)
            total_energy = np.sum(audio ** 2)
            harmonic_ratio = harmonic_energy / (total_energy + 1e-8)
            features.append(harmonic_ratio)

            # Spectral features of harmonic component
            if np.sum(np.abs(harmonic)) > 0:
                harm_centroid = librosa.feature.spectral_centroid(y=harmonic, sr=sr)
                harm_bandwidth = librosa.feature.spectral_bandwidth(y=harmonic, sr=sr)
                features.extend([
                    np.mean(harm_centroid),
                    np.mean(harm_bandwidth)
                ])
            else:
                features.extend([0.0, 0.0])

            # Chroma features (pitch class profile)
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            features.extend([
                np.mean(chroma, axis=1).tolist()
            ][0])

        except Exception:
            features.extend([0.0] * 15)  # 1 + 2 + 12 chroma features

        return features

    def _extract_temporal_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract temporal features"""
        features = []

        try:
            # RMS energy
            rms = librosa.feature.rms(y=audio, frame_length=self.config.frame_size)
            features.extend([
                np.mean(rms),
                np.std(rms)
            ])

            # Onset detection
            onset_frames = librosa.onset.onset_detect(
                y=audio, sr=sr,
                hop_length=self.config.hop_length
            )

            if len(onset_frames) > 1:
                onset_times = librosa.frames_to_time(onset_frames, sr=sr)
                onset_intervals = np.diff(onset_times)
                features.extend([
                    len(onset_frames) / (len(audio) / sr),  # Onset rate
                    np.mean(onset_intervals),               # Average interval
                    np.std(onset_intervals)                 # Interval variation
                ])
            else:
                features.extend([0.0, 0.0, 0.0])

            # Tempo estimation
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
            features.append(tempo)

        except Exception:
            features.extend([0.0] * 6)

        return features

    def _extract_carnatic_features(self, audio: np.ndarray, sr: int) -> List[float]:
        """Extract Carnatic music specific features"""
        features = []

        try:
            # Gamaka detection (pitch oscillations)
            f0, _, _ = librosa.pyin(
                audio, fmin=80, fmax=800, sr=sr,
                frame_length=self.config.frame_size,
                hop_length=self.config.hop_length
            )

            # Remove NaN values
            f0_clean = f0[~np.isnan(f0)]

            if len(f0_clean) > 3:
                # Pitch oscillation features
                pitch_diff = np.diff(f0_clean)
                oscillation_magnitude = np.std(pitch_diff)
                oscillation_frequency = len(signal.find_peaks(pitch_diff)[0]) / (len(f0_clean) / sr * self.config.hop_length)

                features.extend([
                    oscillation_magnitude,
                    oscillation_frequency,
                    np.mean(np.abs(pitch_diff))
                ])

                # Microtonal deviation from Western semitones
                if len(f0_clean) > 0:
                    avg_f0 = np.mean(f0_clean)
                    # Convert to MIDI note number
                    midi_note = 12 * np.log2(avg_f0 / 440) + 69
                    # Distance from nearest semitone
                    semitone_deviation = abs(midi_note - round(midi_note))
                    features.append(semitone_deviation)
                else:
                    features.append(0.0)
            else:
                features.extend([0.0] * 4)

            # Shruti-specific features
            if len(f0_clean) > 0:
                avg_freq = np.mean(f0_clean)
                shruti_info = self.shruti_system.detect_shruti(avg_freq)

                if shruti_info:
                    features.extend([
                        shruti_info.get('cent_deviation', 0),
                        shruti_info.get('confidence', 0),
                        float(shruti_info.get('shruti_index', 0))
                    ])
                else:
                    features.extend([0.0] * 3)
            else:
                features.extend([0.0] * 3)

        except Exception:
            features.extend([0.0] * 7)

        return features

    def _get_feature_dimension(self) -> int:
        """Get total feature dimension"""
        return 10 + 8 + 26 + 4 + 15 + 6 + 7  # Sum of all feature groups

class SwaraClassifier:
    """Deep learning model for swara classification"""

    def __init__(self, config: SwaraRecognitionConfig):
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_extractor = SwaraFeatureExtractor(config)
        self.is_trained = False

    def build_model(self, input_dim: int, num_classes: int = 7) -> tf.keras.Model:
        """Build neural network model for swara classification"""
        model = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(input_dim,)),

            # Feature normalization
            tf.keras.layers.BatchNormalization(),

            # Dense layers with dropout
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.BatchNormalization(),

            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.BatchNormalization(),

            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),

            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),

            # Output layer
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        return model

    def train_model(self, training_data: Dict[str, List[np.ndarray]]) -> Dict[str, Any]:
        """Train the swara classification model"""
        try:
            # Prepare training data
            X_train = []
            y_train = []

            swara_to_index = {swara.name: i for i, swara in enumerate(SwaraName)}

            for swara_name, audio_samples in training_data.items():
                if swara_name in swara_to_index:
                    label = swara_to_index[swara_name]

                    for audio in audio_samples:
                        features = self.feature_extractor.extract_features(audio)
                        X_train.append(features)
                        y_train.append(label)

            X_train = np.array(X_train)
            y_train = np.array(y_train)

            # Split data
            from sklearn.model_selection import train_test_split
            X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
                X_train, y_train, test_size=self.config.validation_split, stratify=y_train
            )

            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train_split)
            X_val_scaled = self.scaler.transform(X_val_split)

            # Build and train model
            self.model = self.build_model(X_train_scaled.shape[1], len(swara_to_index))

            # Training callbacks
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_accuracy',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5
                )
            ]

            # Train model
            history = self.model.fit(
                X_train_scaled, y_train_split,
                validation_data=(X_val_scaled, y_val_split),
                epochs=100,
                batch_size=32,
                callbacks=callbacks,
                verbose=1
            )

            # Save model and scaler
            self.model.save(self.config.model_path)
            joblib.dump(self.scaler, self.config.scaler_path)

            self.is_trained = True

            return {
                'success': True,
                'final_accuracy': max(history.history['val_accuracy']),
                'final_loss': min(history.history['val_loss']),
                'training_samples': len(X_train),
                'feature_dimension': X_train_scaled.shape[1]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def load_model(self) -> bool:
        """Load trained model and scaler"""
        try:
            if tf.io.gfile.exists(self.config.model_path):
                self.model = tf.keras.models.load_model(self.config.model_path)

            if tf.io.gfile.exists(self.config.scaler_path):
                self.scaler = joblib.load(self.config.scaler_path)

            self.is_trained = self.model is not None and self.scaler is not None
            return self.is_trained

        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def predict_swara(self, audio: np.ndarray, sr: int = None) -> Dict[str, Any]:
        """Predict swara from audio"""
        if not self.is_trained:
            if not self.load_model():
                return {
                    'success': False,
                    'error': 'Model not trained or loaded'
                }

        try:
            # Extract features
            features = self.feature_extractor.extract_features(audio, sr)

            if self.scaler is None:
                return {
                    'success': False,
                    'error': 'Feature scaler not available'
                }

            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # Predict
            predictions = self.model.predict(features_scaled, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = predictions[0][predicted_class]

            # Convert to swara name
            index_to_swara = {i: swara.name for i, swara in enumerate(SwaraName)}
            predicted_swara = index_to_swara.get(predicted_class, 'Unknown')

            # Get top predictions
            top_indices = np.argsort(predictions[0])[::-1][:3]
            top_predictions = []

            for idx in top_indices:
                swara_name = index_to_swara.get(idx, 'Unknown')
                prob = predictions[0][idx]
                top_predictions.append({
                    'swara': swara_name,
                    'confidence': float(prob)
                })

            return {
                'success': True,
                'predicted_swara': predicted_swara,
                'confidence': float(confidence),
                'meets_threshold': confidence >= self.config.confidence_threshold,
                'top_predictions': top_predictions,
                'features': features.tolist()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class SwaraRecognitionEngine:
    """Complete swara recognition system with temporal stability"""

    def __init__(self, config: SwaraRecognitionConfig = None):
        self.config = config or SwaraRecognitionConfig()
        self.classifier = SwaraClassifier(self.config)


        # Temporal tracking
        self.recent_predictions = []
        self.stability_buffer = []

    def analyze_swara(self, ml_result: Dict[str, Any], pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze swara with temporal stability"""
        try:
            # Combine results
            result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

            # Add pitch information
            if pitch_data:
                result.update({
                    'fundamental_frequency': pitch_data.get('frequency'),
                    'pitch_confidence': pitch_data.get('confidence'),
                    'voiced_probability': pitch_data.get('voiced_probability', 0)
                })

            # Add ML classification results
            if ml_result['success']:
                result.update({
                    'predicted_swara': ml_result['predicted_swara'],
                    'classification_confidence': ml_result['confidence'],
                    'meets_threshold': ml_result['meets_threshold'],
                    'top_predictions': ml_result['top_predictions']
                })

                # Temporal stability analysis
                stability_info = self._analyze_temporal_stability(ml_result)
                result.update(stability_info)

            else:
                result.update({
                    'predicted_swara': None,
                    'classification_confidence': 0.0,
                    'meets_threshold': False,
                    'error': ml_result.get('error')
                })

            # Overall assessment
            result['overall_confidence'] = self._calculate_overall_confidence(result)
            result['recommendation'] = self._generate_recommendation(result)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _analyze_temporal_stability(self, ml_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal stability of predictions"""
        predicted_swara = ml_result['predicted_swara']
        confidence = ml_result['confidence']

        # Add to recent predictions
        self.recent_predictions.append({
            'swara': predicted_swara,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc)
        })

        # Keep only recent predictions
        cutoff_time = datetime.now(timezone.utc).timestamp() - 5  # 5 seconds
        self.recent_predictions = [
            p for p in self.recent_predictions
            if p['timestamp'].timestamp() > cutoff_time
        ]

        if len(self.recent_predictions) < 2:
            return {
                'temporal_stability': 0.0,
                'consistent_swara': None,
                'stability_confidence': 0.0
            }

        # Analyze consistency
        recent_swaras = [p['swara'] for p in self.recent_predictions[-self.config.context_frames:]]
        most_common_swara = max(set(recent_swaras), key=recent_swaras.count)
        consistency_ratio = recent_swaras.count(most_common_swara) / len(recent_swaras)

        # Calculate average confidence for the consistent swara
        consistent_confidences = [
            p['confidence'] for p in self.recent_predictions[-self.config.context_frames:]
            if p['swara'] == most_common_swara
        ]
        avg_confidence = np.mean(consistent_confidences) if consistent_confidences else 0.0

        stability_score = consistency_ratio * avg_confidence

        return {
            'temporal_stability': stability_score,
            'consistent_swara': most_common_swara if stability_score > self.config.stability_threshold else None,
            'stability_confidence': avg_confidence,
            'consistency_ratio': consistency_ratio,
            'recent_predictions_count': len(recent_swaras)
        }

    def _calculate_overall_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate overall confidence combining multiple factors"""
        factors = []

        # Classification confidence
        if 'classification_confidence' in result:
            factors.append(result['classification_confidence'])

        # Pitch confidence
        if 'pitch_confidence' in result:
            factors.append(result['pitch_confidence'])

        # Temporal stability
        if 'temporal_stability' in result:
            factors.append(result['temporal_stability'])

        # Voiced probability
        if 'voiced_probability' in result:
            factors.append(result['voiced_probability'])

        return float(np.mean(factors)) if factors else 0.0

    def _generate_recommendation(self, result: Dict[str, Any]) -> str:
        """Generate user-friendly recommendation"""
        overall_confidence = result.get('overall_confidence', 0)
        predicted_swara = result.get('predicted_swara')
        temporal_stability = result.get('temporal_stability', 0)

        if not predicted_swara:
            return "Could not detect swara. Ensure clear vocal tone."

        if overall_confidence > 0.8:
            return f"Excellent {predicted_swara}! Very accurate intonation."
        elif overall_confidence > 0.6:
            return f"Good {predicted_swara}. Try to maintain steady pitch."
        elif overall_confidence > 0.4:
            if temporal_stability < 0.5:
                return f"Detected {predicted_swara} but pitch is unstable. Focus on steady tone."
            else:
                return f"Uncertain {predicted_swara} detection. Check your intonation."
        else:
            return "Unclear swara. Practice with reference pitch and try again."
