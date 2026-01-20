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
    """Configuration for audio processing (optimized for keyboard/instruments)"""
    sample_rate: int = 44100
    buffer_size: int = 2048
    hop_length: int = 512
    confidence_threshold: float = 0.50  # Higher for clean instrument signals
    silence_threshold: float = 0.008  # Threshold for ambient noise
    min_frequency: float = 60.0  # ~B1 - supports lower octaves on keyboard
    max_frequency: float = 2000.0  # ~B6 - supports upper octaves on keyboard
    autocorr_peak_threshold: float = 0.10  # Higher for cleaner instrument signals
    cent_tolerance: float = 25.0  # Tighter tolerance for precise keyboard pitch
    max_deviation_cents: float = 50.0  # Stricter for keyboard (was 100 for voice)
    spectral_flatness_threshold: float = 0.3  # Lower threshold - instruments are more tonal
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

    def _normalize_to_octave(self, frequency: float) -> float:
        """
        Normalize a frequency to the base octave (starting at base_sa).

        The 22-shruti system covers ratios from 1.0 to ~2.0 (one octave).
        This method applies octave equivalence so notes in higher/lower octaves
        are correctly mapped to their corresponding shruti.

        Examples (base_sa = 261.63 Hz):
            - 523.26 Hz (Upper Sa) → 261.63 Hz (Shadja)
            - 130.81 Hz (Lower Sa) → 261.63 Hz (Shadja)
            - 392.44 Hz (Pa) → 392.44 Hz (unchanged, already in base octave)
        """
        normalized = frequency
        # Bring down from higher octaves
        while normalized >= self.base_sa * 2:
            normalized = normalized / 2
        # Bring up from lower octaves
        while normalized < self.base_sa:
            normalized = normalized * 2
        return normalized

    def _calculate_spectral_flatness(self, audio_data: np.ndarray) -> float:
        """
        Calculate spectral flatness (Wiener entropy).

        Spectral flatness is the ratio of geometric mean to arithmetic mean of the spectrum.
        - Value close to 0: Tonal/harmonic content (peaked spectrum)
        - Value close to 1: Noise-like content (flat spectrum)

        Returns:
            float: Spectral flatness between 0 and 1
        """
        # Compute magnitude spectrum
        spectrum = np.abs(np.fft.rfft(audio_data * self._window))

        # Avoid log(0) by adding small epsilon
        spectrum = spectrum + 1e-10

        # Geometric mean (use log for numerical stability)
        log_spectrum = np.log(spectrum)
        geometric_mean = np.exp(np.mean(log_spectrum))

        # Arithmetic mean
        arithmetic_mean = np.mean(spectrum)

        # Spectral flatness
        if arithmetic_mean > 0:
            flatness = geometric_mean / arithmetic_mean
        else:
            flatness = 1.0  # Treat as noise if no energy

        return float(flatness)

    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Pre-process audio signal to improve pitch detection.
        - Remove DC offset
        - Apply simple high-pass filter to reduce low-frequency noise
        - Normalize signal
        """
        # Remove DC offset
        audio_data = audio_data - np.mean(audio_data)

        # Simple high-pass filter (remove frequencies below ~30Hz)
        # Using first-order difference as a simple high-pass
        if len(audio_data) > 1:
            # Coefficient for ~30Hz cutoff at 44100 sample rate
            alpha = 0.995
            filtered = np.zeros_like(audio_data)
            filtered[0] = audio_data[0]
            for i in range(1, len(audio_data)):
                filtered[i] = alpha * (filtered[i-1] + audio_data[i] - audio_data[i-1])
            audio_data = filtered

        # Normalize to [-1, 1] range while preserving relative amplitude
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val

        return audio_data

    def detect_shruti(self, audio_data: np.ndarray) -> Optional[PitchDetectionResult]:
        """
        Process audio data and detect pitch/shruti.
        Expected input: normalized float32 numpy array of audio samples.
        """
        start_time = time.time()

        # Debug: Log audio data statistics
        if len(audio_data) > 0:
            logger.debug(f"Audio data stats: len={len(audio_data)}, min={np.min(audio_data):.4f}, "
                        f"max={np.max(audio_data):.4f}, mean={np.mean(audio_data):.4f}, "
                        f"std={np.std(audio_data):.4f}")

        # Basic validation
        if len(audio_data) < self.config.buffer_size:
            # Pad if too short
            pad_len = self.config.buffer_size - len(audio_data)
            audio_data = np.pad(audio_data, (0, pad_len))
        elif len(audio_data) > self.config.buffer_size:
            # Truncate if too long
            audio_data = audio_data[:self.config.buffer_size]

        # Pre-process audio for better pitch detection
        audio_data = self._preprocess_audio(audio_data)

        # 1. Calculate Signal Energy / RMS for voicing detection
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < self.config.silence_threshold:  # Configurable silence threshold
            logger.debug(f"Below silence threshold: rms={rms:.4f} < {self.config.silence_threshold}")
            return None

        # 2. Spectral flatness check - noise has flat spectrum, music has peaks
        spectral_flatness = self._calculate_spectral_flatness(audio_data)
        if spectral_flatness > self.config.spectral_flatness_threshold:
            logger.debug(f"Rejected as noise: spectral_flatness={spectral_flatness:.3f} > {self.config.spectral_flatness_threshold}")
            return None

        # 3. Pitch Detection (Simplified Autocorrelation for now)
        # In a real implementation, this would use a more robust algorithm like YIN or CREPE
        frequency, confidence = self._detect_pitch_autocorr(audio_data)
        
        if confidence < self.config.confidence_threshold or frequency < self.config.min_frequency:
            logger.debug(f"Rejected: confidence={confidence:.2f} or freq={frequency:.1f}Hz below thresholds")
            return None

        # 4. Shruti Mapping with octave equivalence
        # Normalize frequency to the base octave for accurate shruti matching
        # (22-shruti system covers ratios 1.0 to ~2.0, so we need octave equivalence)
        normalized_freq = self._normalize_to_octave(frequency)
        match = find_closest_shruti(normalized_freq, self.base_sa)

        # 5. Maximum deviation filter - reject wild detections that don't match any shruti well
        if abs(match['deviation_cents']) > self.config.max_deviation_cents:
            logger.debug(f"Rejected: deviation={match['deviation_cents']:.1f}¢ > max {self.config.max_deviation_cents}¢ "
                        f"(freq={frequency:.1f}Hz matched={match['shruti_name']})")
            return None

        # Debug logging for pitch detection - use INFO level for visibility
        logger.info(f"Pitch Detection: freq={frequency:.1f}Hz, base_sa={self.base_sa}Hz, "
                    f"matched={match['shruti_name']}, deviation={match['deviation_cents']:.1f}¢, "
                    f"target_freq={match['frequency']:.1f}Hz, confidence={confidence:.2f}")

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
        Time-domain pitch detection using autocorrelation with fundamental frequency detection.
        Uses a modified approach to find the fundamental pitch rather than harmonics.
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

        # Define search range for fundamental frequency
        # For vocal pitch detection, focus on typical vocal range (80-800 Hz)
        min_period = int(self.config.sample_rate / 800)   # ~55 samples for 800Hz
        max_period = int(self.config.sample_rate / 80)    # ~551 samples for 80Hz

        if max_period >= n:
            max_period = n - 1

        if min_period >= max_period:
            return 0.0, 0.0

        # Find the fundamental frequency peak using subharmonic validation
        # The key insight: if we detect a harmonic, there should be a peak at 2x the period (fundamental)
        search_region = autocorr[min_period:max_period]

        if len(search_region) == 0:
            return 0.0, 0.0

        # Find all local maxima (peaks) in the search region
        # A peak is where the value is greater than its neighbors
        peaks = []
        for i in range(1, len(search_region) - 1):
            if search_region[i] > search_region[i-1] and search_region[i] > search_region[i+1]:
                if search_region[i] >= self.config.autocorr_peak_threshold:
                    peaks.append((i + min_period, search_region[i]))

        if not peaks:
            # Fallback to global max if no local peaks found
            peak_idx = np.argmax(search_region) + min_period
            peak_val = autocorr[peak_idx]
            if peak_val < self.config.autocorr_peak_threshold:
                return 0.0, 0.0
        else:
            # Sort peaks by autocorrelation value (strongest first)
            peaks.sort(key=lambda x: x[1], reverse=True)

            # Find the best fundamental frequency
            # Strategy: The fundamental frequency produces the FIRST strong peak in autocorrelation
            # (after the initial lag-0 peak). Longer periods (subharmonics) will also have peaks
            # but they should be weaker than the fundamental.
            #
            # Key insight: peaks are sorted by strength. The strongest peak that's not
            # obviously a subharmonic artifact should be the fundamental.
            best_peak = None

            for period, value in peaks:
                # Skip very low frequencies (likely room resonance/noise)
                freq = self.config.sample_rate / period
                if freq < 100:  # Below typical vocal range
                    continue

                # Check if this might be a SUBHARMONIC (octave below the real fundamental)
                # If there's a strong peak at period/2 (octave up), prefer that
                is_subharmonic = False
                half_period = int(period / 2)
                if half_period >= min_period and half_period < len(autocorr):
                    half_val = autocorr[half_period]
                    # If the octave-up has a STRONGER peak, this is likely a subharmonic
                    # Use strict threshold: must be actually stronger
                    if half_val > value * 0.95:
                        is_subharmonic = True
                        logger.debug(f"Period {period} ({freq:.1f}Hz) is subharmonic - "
                                   f"stronger peak at {half_period} ({self.config.sample_rate/half_period:.1f}Hz)")

                if not is_subharmonic:
                    best_peak = (period, value)
                    logger.debug(f"Selected fundamental at period {period} ({freq:.1f}Hz)")
                    break
                elif best_peak is None:
                    # Fallback: use strongest peak even if it might be subharmonic
                    best_peak = (period, value)

            if best_peak is None:
                return 0.0, 0.0

            peak_idx, peak_val = best_peak

            logger.debug(f"Selected period {peak_idx} -> {self.config.sample_rate/peak_idx:.1f}Hz "
                        f"(confidence: {peak_val:.2f})")

        # Parabolic interpolation for better precision
        if 0 < peak_idx < len(autocorr) - 1:
            alpha = autocorr[peak_idx - 1]
            beta = autocorr[peak_idx]
            gamma = autocorr[peak_idx + 1]
            denom = alpha - 2*beta + gamma
            if abs(denom) > 1e-10:  # Avoid division by zero
                offset = 0.5 * (alpha - gamma) / denom
                true_idx = peak_idx + offset
            else:
                true_idx = peak_idx
        else:
            true_idx = peak_idx

        frequency = self.config.sample_rate / true_idx

        return frequency, float(peak_val)

