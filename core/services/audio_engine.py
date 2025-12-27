"""
Carnatic Audio Engine Service
Core service for audio processing, pitch detection, and shruti analysis.
"""

import logging
import numpy as np
from typing import Dict, Optional, Tuple, List, Union
from dataclasses import dataclass
import time
from concurrent.futures import ThreadPoolExecutor

from core.models.shruti import (
    ShrutiSystem, 
    Shruti, 
    find_closest_shruti, 
    analyze_pitch_deviation
)

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Configuration for audio processing"""
    sample_rate: int = 44100
    buffer_size: int = 2048
    hop_length: int = 512
    confidence_threshold: float = 0.6
    min_frequency: float = 60.0  # ~B1
    max_frequency: float = 1200.0  # ~D6
    enable_parallel_processing: bool = False
    max_worker_threads: int = 2

@dataclass
class PitchDetectionResult:
    """Result of a pitch detection operation"""
    timestamp: float
    detected_frequency: float
    confidence: float
    shruti: Optional[Shruti] = None
    cent_deviation: float = 0.0
    note_name: str = ""
    is_voiced: bool = False

class CarnaticAudioEngine:
    """
    Main engine for processing audio and detecting Carnatic musical concepts.
    Handles pitch detection, noise reduction, and shruti mapping.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.shruti_system = ShrutiSystem()
        self.base_sa = 261.63  # Default C4, can be updated per session
        
        # Initialize processing buffers
        self._window = np.hanning(self.config.buffer_size)
        
        # Performance metrics
        self._last_process_time = 0
        self._avg_latency = 0
        
        logger.info(f"CarnaticAudioEngine initialized with sample_rate={self.config.sample_rate}")

    def set_base_frequency(self, frequency: float):
        """Update the base Sa frequency"""
        if 50 <= frequency <= 1000:
            self.base_sa = frequency
            logger.debug(f"Base frequency updated to {frequency}Hz")
        else:
            logger.warning(f"Invalid base frequency request: {frequency}")

    def detect_shruti(self, audio_data: np.ndarray) -> Optional[PitchDetectionResult]:
        """
        Process audio data and detect pitch/shruti.
        Expected input: normalized float32 numpy array of audio samples.
        """
        start_time = time.time()
        
        # Basic validation
        if len(audio_data) < self.config.buffer_size:
            # Pad if too short
            pad_len = self.config.buffer_size - len(audio_data)
            audio_data = np.pad(audio_data, (0, pad_len))
        elif len(audio_data) > self.config.buffer_size:
            # Truncate if too long
            audio_data = audio_data[:self.config.buffer_size]

        # 1. Calculate Signal Energy / RMS for voicing detection
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 0.01:  # Silence threshold
            return None

        # 2. Pitch Detection (Simplified Autocorrelation for now)
        # In a real implementation, this would use a more robust algorithm like YIN or CREPE
        frequency, confidence = self._detect_pitch_autocorr(audio_data)
        
        if confidence < self.config.confidence_threshold or frequency < self.config.min_frequency:
            return None

        # 3. Shruti Mapping
        match = find_closest_shruti(frequency, self.base_sa)
        
        result = PitchDetectionResult(
            timestamp=start_time,
            detected_frequency=frequency,
            confidence=confidence,
            shruti=self.shruti_system.get_shruti(match['shruti_name']) if match['shruti_name'] else None,
            cent_deviation=match['deviation_cents'],
            note_name=match['shruti_name'] or "Unknown",
            is_voiced=True
        )
        
        # Update metrics
        process_time = (time.time() - start_time) * 1000  # ms
        self._last_process_time = process_time
        
        return result

    def _detect_pitch_autocorr(self, audio_buffer: np.ndarray) -> Tuple[float, float]:
        """
        Basic time-domain pitch detection using autocorrelation.
        Returns (frequency, confidence)
        """
        # Apply window function
        windowed = audio_buffer * self._window
        
        # Calculate autocorrelation
        # Using FFT for faster correlation: corr(x,x) = ifft(fft(x) * conj(fft(x)))
        n = len(windowed)
        # Pad with zeros to avoid wrap-around error (circular correlation)
        n_fft = 2 ** int(np.ceil(np.log2(2*n)))
        
        spectrum = np.fft.rfft(windowed, n_fft)
        autocorr = np.fft.irfft(spectrum * np.conj(spectrum))
        
        # Normalize
        autocorr = autocorr[:n]
        if autocorr[0] == 0:
            return 0.0, 0.0
        autocorr = autocorr / autocorr[0]
        
        # Find peaks
        # We look for the first major peak after the zero lag
        # Skip the main lobe (lag 0)
        min_period = int(self.config.sample_rate / self.config.max_frequency)
        max_period = int(self.config.sample_rate / self.config.min_frequency)
        
        if max_period >= n:
            max_period = n - 1
            
        if min_period >= max_period:
            return 0.0, 0.0

        search_region = autocorr[min_period:max_period]
        
        if len(search_region) == 0:
            return 0.0, 0.0
            
        peak_idx = np.argmax(search_region) + min_period
        peak_val = autocorr[peak_idx]
        
        if peak_val < 0.1:  # Very low correlation
            return 0.0, 0.0
            
        # Parabolic interpolation for better precision
        if 0 < peak_idx < len(autocorr) - 1:
            alpha = autocorr[peak_idx - 1]
            beta = autocorr[peak_idx]
            gamma = autocorr[peak_idx + 1]
            offset = 0.5 * (alpha - gamma) / (alpha - 2*beta + gamma)
            true_idx = peak_idx + offset
        else:
            true_idx = peak_idx
            
        frequency = self.config.sample_rate / true_idx
        
        return frequency, float(peak_val)

