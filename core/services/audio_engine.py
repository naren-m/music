"""
Enhanced Audio Processing Engine for Carnatic Learning
Implements advanced pitch detection, synthesis, and real-time analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import threading
import time
from collections import deque
import json

from ..models.shruti import ShrutiSystem, Shruti


@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int = 44100
    buffer_size: int = 2048
    fft_size: int = 8192
    overlap_ratio: float = 0.5
    smoothing_factor: float = 0.3
    confidence_threshold: float = 0.6
    frequency_range: Tuple[float, float] = (80.0, 2000.0)
    noise_gate_threshold: float = -60.0  # dB


@dataclass
class PitchDetectionResult:
    """Result of pitch detection analysis"""
    fundamental_frequency: float
    confidence: float
    magnitude: float
    harmonics: List[Tuple[float, float]]  # (frequency, magnitude) pairs
    spectral_centroid: float
    zero_crossing_rate: float
    timestamp: float
    
    
@dataclass
class ShrutiDetectionResult:
    """Result of Carnatic shruti detection"""
    shruti: Optional[Shruti]
    detected_frequency: float
    target_frequency: float
    cent_deviation: float
    confidence: float
    magnitude: float
    timestamp: float
    raga_context: Optional[str] = None


class AdvancedPitchDetector:
    """Advanced pitch detection using multiple algorithms"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self._autocorr_threshold = 0.3
        self._harmonic_threshold = 0.1
        
    def detect_pitch(self, audio_data: np.ndarray) -> Optional[PitchDetectionResult]:
        """Detect pitch using hybrid approach"""
        if len(audio_data) < self.config.buffer_size:
            return None
            
        # Apply window function
        windowed = audio_data * np.hanning(len(audio_data))
        
        # Multiple pitch detection methods
        freq_autocorr = self._autocorrelation_pitch(windowed)
        freq_harmonic = self._harmonic_product_spectrum(windowed)
        freq_cepstrum = self._cepstrum_pitch(windowed)
        
        # Combine results with confidence weighting
        fundamental = self._combine_pitch_estimates([
            freq_autocorr, freq_harmonic, freq_cepstrum
        ])
        
        if fundamental is None:
            return None
            
        # Calculate additional features
        magnitude = np.sqrt(np.mean(audio_data ** 2))
        harmonics = self._extract_harmonics(windowed, fundamental)
        spectral_centroid = self._spectral_centroid(windowed)
        zcr = self._zero_crossing_rate(audio_data)
        confidence = self._calculate_confidence(windowed, fundamental, magnitude)
        
        return PitchDetectionResult(
            fundamental_frequency=fundamental,
            confidence=confidence,
            magnitude=magnitude,
            harmonics=harmonics,
            spectral_centroid=spectral_centroid,
            zero_crossing_rate=zcr,
            timestamp=time.time()
        )
    
    def _autocorrelation_pitch(self, signal: np.ndarray) -> Optional[float]:
        """Pitch detection using autocorrelation"""
        autocorr = np.correlate(signal, signal, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        # Find peaks in autocorrelation
        min_period = int(self.config.sample_rate / self.config.frequency_range[1])
        max_period = int(self.config.sample_rate / self.config.frequency_range[0])
        
        if max_period >= len(autocorr):
            return None
            
        autocorr_segment = autocorr[min_period:max_period]
        if len(autocorr_segment) == 0:
            return None
            
        peak_idx = np.argmax(autocorr_segment)
        if autocorr_segment[peak_idx] < self._autocorr_threshold * autocorr[0]:
            return None
            
        period = min_period + peak_idx
        return self.config.sample_rate / period
    
    def _harmonic_product_spectrum(self, signal: np.ndarray) -> Optional[float]:
        """Pitch detection using harmonic product spectrum"""
        fft_data = np.fft.rfft(signal, n=self.config.fft_size)
        magnitude_spectrum = np.abs(fft_data)
        
        # Downsample for harmonic products
        products = magnitude_spectrum.copy()
        for harmonic in range(2, 6):  # Up to 5th harmonic
            downsampled = magnitude_spectrum[::harmonic]
            min_len = min(len(products), len(downsampled))
            products[:min_len] *= downsampled[:min_len]
        
        # Find peak in product spectrum
        freq_resolution = self.config.sample_rate / self.config.fft_size
        min_bin = int(self.config.frequency_range[0] / freq_resolution)
        max_bin = int(self.config.frequency_range[1] / freq_resolution)
        
        if max_bin >= len(products):
            max_bin = len(products) - 1
            
        if min_bin >= max_bin:
            return None
            
        search_region = products[min_bin:max_bin]
        if len(search_region) == 0:
            return None
            
        peak_idx = np.argmax(search_region)
        return (min_bin + peak_idx) * freq_resolution
    
    def _cepstrum_pitch(self, signal: np.ndarray) -> Optional[float]:
        """Pitch detection using cepstral analysis"""
        fft_data = np.fft.rfft(signal, n=self.config.fft_size)
        log_spectrum = np.log(np.abs(fft_data) + 1e-10)
        cepstrum = np.fft.irfft(log_spectrum)
        
        # Find peak in cepstrum (quefrency domain)
        min_quefrency = int(self.config.sample_rate / self.config.frequency_range[1])
        max_quefrency = int(self.config.sample_rate / self.config.frequency_range[0])
        
        if max_quefrency >= len(cepstrum):
            return None
            
        cep_segment = cepstrum[min_quefrency:max_quefrency]
        if len(cep_segment) == 0:
            return None
            
        peak_idx = np.argmax(cep_segment)
        quefrency = min_quefrency + peak_idx
        return self.config.sample_rate / quefrency
    
    def _combine_pitch_estimates(self, estimates: List[Optional[float]]) -> Optional[float]:
        """Combine multiple pitch estimates with confidence weighting"""
        valid_estimates = [f for f in estimates if f is not None]
        
        if not valid_estimates:
            return None
            
        if len(valid_estimates) == 1:
            return valid_estimates[0]
        
        # Use median for robustness
        return float(np.median(valid_estimates))
    
    def _extract_harmonics(self, signal: np.ndarray, fundamental: float) -> List[Tuple[float, float]]:
        """Extract harmonic frequencies and their magnitudes"""
        fft_data = np.fft.rfft(signal, n=self.config.fft_size)
        magnitude_spectrum = np.abs(fft_data)
        freq_resolution = self.config.sample_rate / self.config.fft_size
        
        harmonics = []
        for harmonic_num in range(1, 8):  # Up to 7th harmonic
            harmonic_freq = fundamental * harmonic_num
            if harmonic_freq > self.config.sample_rate / 2:
                break
                
            # Find bin closest to harmonic frequency
            bin_idx = int(harmonic_freq / freq_resolution)
            if bin_idx < len(magnitude_spectrum):
                magnitude = magnitude_spectrum[bin_idx]
                if magnitude > self._harmonic_threshold * magnitude_spectrum.max():
                    harmonics.append((harmonic_freq, float(magnitude)))
        
        return harmonics
    
    def _spectral_centroid(self, signal: np.ndarray) -> float:
        """Calculate spectral centroid (brightness measure)"""
        fft_data = np.fft.rfft(signal, n=self.config.fft_size)
        magnitude_spectrum = np.abs(fft_data)
        freqs = np.fft.rfftfreq(self.config.fft_size, 1/self.config.sample_rate)
        
        if magnitude_spectrum.sum() == 0:
            return 0.0
            
        return float(np.sum(freqs * magnitude_spectrum) / np.sum(magnitude_spectrum))
    
    def _zero_crossing_rate(self, signal: np.ndarray) -> float:
        """Calculate zero crossing rate"""
        return float(np.sum(np.diff(np.signbit(signal))) / len(signal))
    
    def _calculate_confidence(self, signal: np.ndarray, fundamental: float, magnitude: float) -> float:
        """Calculate confidence score for pitch detection"""
        # Based on signal strength, harmonic content, and spectral clarity
        if magnitude < 1e-6:
            return 0.0
            
        # Harmonic strength
        harmonics = self._extract_harmonics(signal, fundamental)
        harmonic_strength = len(harmonics) / 7.0  # Normalized by max harmonics
        
        # Spectral clarity (inverse of spectral spread)
        fft_data = np.fft.rfft(signal, n=self.config.fft_size)
        magnitude_spectrum = np.abs(fft_data)
        spectral_spread = np.std(magnitude_spectrum) / (np.mean(magnitude_spectrum) + 1e-10)
        clarity = 1.0 / (1.0 + spectral_spread)
        
        # Combine factors
        confidence = (harmonic_strength * 0.4 + clarity * 0.3 + min(magnitude * 10, 1.0) * 0.3)
        return float(np.clip(confidence, 0.0, 1.0))


class CarnaticAudioEngine:
    """Complete audio engine for Carnatic music learning"""
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.shruti_system = ShrutiSystem()
        self.pitch_detector = AdvancedPitchDetector(self.config)
        
        # State management
        self.base_sa_frequency = 261.63  # C4
        self.detection_history = deque(maxlen=50)
        self.current_raga_context = None
        self._lock = threading.Lock()
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'shruti_detected': [],
            'raga_changed': [],
            'session_started': [],
            'session_ended': []
        }
    
    def set_base_sa_frequency(self, frequency: float) -> None:
        """Set the base Sa frequency for shruti calculations"""
        if 100 <= frequency <= 500:  # Reasonable range
            with self._lock:
                self.base_sa_frequency = frequency
    
    def detect_shruti(self, audio_data: np.ndarray) -> Optional[ShrutiDetectionResult]:
        """Detect Carnatic shruti from audio data"""
        pitch_result = self.pitch_detector.detect_pitch(audio_data)
        
        if not pitch_result or pitch_result.confidence < self.config.confidence_threshold:
            return None
        
        with self._lock:
            # Find closest shruti
            closest_shruti = self.shruti_system.find_closest_shruti(
                pitch_result.fundamental_frequency, 
                self.base_sa_frequency,
                tolerance_cents=30
            )
            
            if not closest_shruti:
                return None
            
            # Calculate target frequency and deviation
            target_freq = closest_shruti.calculate_frequency(self.base_sa_frequency)
            cent_deviation = closest_shruti.cent_deviation(
                pitch_result.fundamental_frequency, 
                self.base_sa_frequency
            )
            
            # Create result
            result = ShrutiDetectionResult(
                shruti=closest_shruti,
                detected_frequency=pitch_result.fundamental_frequency,
                target_frequency=target_freq,
                cent_deviation=cent_deviation,
                confidence=pitch_result.confidence,
                magnitude=pitch_result.magnitude,
                timestamp=pitch_result.timestamp,
                raga_context=self.current_raga_context
            )
            
            # Update detection history
            self.detection_history.append(result)
            
            # Analyze raga context
            self._update_raga_context()
            
            # Trigger callbacks
            self._trigger_callbacks('shruti_detected', result)
            
            return result
    
    def _update_raga_context(self) -> None:
        """Update raga context based on recent detections"""
        if len(self.detection_history) < 5:
            return
        
        # Get recent shruti names
        recent_shrutis = [
            detection.shruti.western_equiv 
            for detection in list(self.detection_history)[-10:]
            if detection.shruti
        ]
        
        # Simple raga pattern matching
        from ..models.shruti import RagaAnalyzer
        raga_analyzer = RagaAnalyzer(self.shruti_system)
        raga_scores = raga_analyzer.analyze_note_sequence(recent_shrutis)
        
        if raga_scores:
            best_raga = max(raga_scores, key=raga_scores.get)
            if raga_scores[best_raga] >= 0.6:  # Minimum confidence
                if self.current_raga_context != best_raga:
                    old_raga = self.current_raga_context
                    self.current_raga_context = best_raga
                    self._trigger_callbacks('raga_changed', {
                        'old_raga': old_raga,
                        'new_raga': best_raga,
                        'confidence': raga_scores[best_raga]
                    })
    
    def get_detection_statistics(self) -> Dict[str, float]:
        """Get statistics from recent detections"""
        if not self.detection_history:
            return {}
        
        recent_detections = list(self.detection_history)[-20:]
        
        avg_confidence = np.mean([d.confidence for d in recent_detections])
        avg_magnitude = np.mean([d.magnitude for d in recent_detections])
        avg_deviation = np.mean([abs(d.cent_deviation) for d in recent_detections])
        
        # Most common shruti
        shruti_counts = {}
        for detection in recent_detections:
            if detection.shruti:
                name = detection.shruti.name
                shruti_counts[name] = shruti_counts.get(name, 0) + 1
        
        most_common_shruti = max(shruti_counts, key=shruti_counts.get) if shruti_counts else None
        
        return {
            'average_confidence': float(avg_confidence),
            'average_magnitude': float(avg_magnitude),
            'average_cent_deviation': float(avg_deviation),
            'most_common_shruti': most_common_shruti,
            'total_detections': len(recent_detections),
            'unique_shrutis': len(shruti_counts),
            'current_raga': self.current_raga_context
        }
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for audio events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable) -> None:
        """Remove callback for audio events"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
    
    def _trigger_callbacks(self, event: str, data: any) -> None:
        """Trigger all callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Callback error for {event}: {e}")
    
    def export_session_data(self) -> Dict[str, any]:
        """Export current session data for analysis"""
        return {
            'base_sa_frequency': self.base_sa_frequency,
            'current_raga_context': self.current_raga_context,
            'detection_history': [
                {
                    'shruti': d.shruti.name if d.shruti else None,
                    'detected_frequency': d.detected_frequency,
                    'target_frequency': d.target_frequency,
                    'cent_deviation': d.cent_deviation,
                    'confidence': d.confidence,
                    'magnitude': d.magnitude,
                    'timestamp': d.timestamp
                }
                for d in self.detection_history
            ],
            'statistics': self.get_detection_statistics()
        }


class AudioSynthesizer:
    """Audio synthesis for backing tracks and reference tones"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._cache = {}  # Cache for generated sounds
    
    def generate_tanpura_drone(self, sa_frequency: float, duration: float = 4.0) -> np.ndarray:
        """Generate tanpura drone sound"""
        cache_key = f"tanpura_{sa_frequency}_{duration}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate Sa and Pa drone
        sa_freq = sa_frequency
        pa_freq = sa_frequency * 1.5  # Perfect fifth
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Create complex harmonics for realistic tanpura sound
        sa_wave = self._generate_tanpura_string(t, sa_freq, 0.7)
        pa_wave = self._generate_tanpura_string(t, pa_freq, 0.3)
        
        # Combine and apply envelope
        drone = sa_wave + pa_wave
        drone = self._apply_envelope(drone, attack=0.1, decay=0.2, sustain=0.8, release=0.1)
        
        # Cache and return
        self._cache[cache_key] = drone
        return drone
    
    def _generate_tanpura_string(self, t: np.ndarray, fundamental: float, amplitude: float) -> np.ndarray:
        """Generate realistic tanpura string sound with harmonics"""
        wave = np.zeros_like(t)
        
        # Add harmonics with decreasing amplitude
        for harmonic in range(1, 8):
            freq = fundamental * harmonic
            harm_amp = amplitude / harmonic  # Decreasing harmonics
            wave += harm_amp * np.sin(2 * np.pi * freq * t)
        
        # Add slight frequency modulation for realism
        vibrato = 0.002 * np.sin(2 * np.pi * 4 * t)  # 4Hz vibrato
        modulated_wave = wave * (1 + vibrato)
        
        return modulated_wave
    
    def _apply_envelope(self, signal: np.ndarray, attack: float, decay: float, 
                       sustain: float, release: float) -> np.ndarray:
        """Apply ADSR envelope to signal"""
        total_samples = len(signal)
        
        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        release_samples = int(release * self.sample_rate)
        sustain_samples = total_samples - attack_samples - decay_samples - release_samples
        
        envelope = np.ones(total_samples)
        
        # Attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay
        if decay_samples > 0:
            start_idx = attack_samples
            end_idx = start_idx + decay_samples
            envelope[start_idx:end_idx] = np.linspace(1, sustain, decay_samples)
        
        # Sustain (already set to sustain level)
        sustain_start = attack_samples + decay_samples
        envelope[sustain_start:sustain_start + sustain_samples] = sustain
        
        # Release
        if release_samples > 0:
            start_idx = total_samples - release_samples
            envelope[start_idx:] = np.linspace(sustain, 0, release_samples)
        
        return signal * envelope
    
    def generate_metronome_beat(self, tempo: int, accent_beat: int = 4) -> np.ndarray:
        """Generate metronome beat pattern"""
        beat_duration = 60.0 / tempo  # seconds per beat
        beat_samples = int(self.sample_rate * beat_duration)
        
        # Generate different sounds for accented and regular beats
        accent_freq = 1000  # Hz
        regular_freq = 800  # Hz
        
        t_beat = np.linspace(0, 0.1, int(self.sample_rate * 0.1))  # 100ms click
        
        accent_click = np.sin(2 * np.pi * accent_freq * t_beat) * np.exp(-t_beat * 30)
        regular_click = np.sin(2 * np.pi * regular_freq * t_beat) * np.exp(-t_beat * 30)
        
        # Create beat pattern (4 beats)
        pattern = np.zeros(beat_samples * accent_beat)
        for beat in range(accent_beat):
            start_sample = beat * beat_samples
            if beat == 0:  # Accent on first beat
                pattern[start_sample:start_sample + len(accent_click)] = accent_click
            else:
                pattern[start_sample:start_sample + len(regular_click)] = regular_click
        
        return pattern