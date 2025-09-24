"""
Comprehensive Audio Engine Tests
Tests for pitch detection, shruti analysis, and audio processing
"""

import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch
from core.services.audio_engine import (
    AdvancedPitchDetector, 
    PitchDetectionResult,
    ShrutiAnalyzer,
    AudioSynthesizer,
    TanpuraGenerator,
    MetronomeGenerator
)
from core.models.shruti import SHRUTI_SYSTEM


class TestAdvancedPitchDetector:
    """Test pitch detection algorithms."""
    
    def test_pitch_detector_initialization(self, pitch_detector):
        """Test pitch detector initializes correctly."""
        assert pitch_detector.sample_rate == 44100
        assert pitch_detector.confidence_threshold == 0.7
        assert hasattr(pitch_detector, '_autocorrelation_pitch')
        assert hasattr(pitch_detector, '_harmonic_product_spectrum')
        assert hasattr(pitch_detector, '_cepstrum_pitch')
    
    def test_detect_pure_tone(self, pitch_detector):
        """Test detection of pure sine wave."""
        # Generate 440Hz sine wave (A4)
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440.0
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        result = pitch_detector.detect_pitch(audio_data)
        
        assert result is not None
        assert isinstance(result, PitchDetectionResult)
        assert abs(result.frequency - 440.0) < 5.0  # Within 5Hz tolerance
        assert result.confidence > 0.8
    
    def test_detect_complex_harmonic(self, pitch_detector):
        """Test detection of complex harmonic signal."""
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        fundamental = 261.63  # C4
        
        # Create complex signal with harmonics
        signal = (np.sin(2 * np.pi * fundamental * t) +
                 0.5 * np.sin(2 * np.pi * 2 * fundamental * t) +
                 0.25 * np.sin(2 * np.pi * 3 * fundamental * t))
        audio_data = signal.astype(np.float32)
        
        result = pitch_detector.detect_pitch(audio_data)
        
        assert result is not None
        assert abs(result.frequency - fundamental) < 10.0
        assert result.confidence > 0.6
    
    def test_noise_rejection(self, pitch_detector):
        """Test rejection of noise signals."""
        # Generate white noise
        audio_data = np.random.normal(0, 0.1, 44100).astype(np.float32)
        
        result = pitch_detector.detect_pitch(audio_data)
        
        # Should either return None or very low confidence
        if result is not None:
            assert result.confidence < 0.5
    
    def test_silence_detection(self, pitch_detector):
        """Test detection of silence."""
        # Generate silence
        audio_data = np.zeros(44100, dtype=np.float32)
        
        result = pitch_detector.detect_pitch(audio_data)
        
        assert result is None or result.confidence < 0.1
    
    def test_frequency_range_bounds(self, pitch_detector):
        """Test frequency detection within valid range."""
        test_frequencies = [80, 200, 440, 1000, 4000]
        
        for freq in test_frequencies:
            t = np.linspace(0, 1.0, 44100)
            audio_data = np.sin(2 * np.pi * freq * t).astype(np.float32)
            
            result = pitch_detector.detect_pitch(audio_data)
            
            if 80 <= freq <= 2000:  # Within detection range
                assert result is not None
                assert abs(result.frequency - freq) < freq * 0.02  # 2% tolerance
            else:  # Outside range
                assert result is None or result.confidence < 0.5


class TestShrutiAnalyzer:
    """Test shruti analysis and classification."""
    
    @pytest.fixture
    def shruti_analyzer(self):
        return ShrutiAnalyzer()
    
    def test_shruti_analyzer_initialization(self, shruti_analyzer):
        """Test shruti analyzer initializes correctly."""
        assert shruti_analyzer.base_sa == 261.63  # C4
        assert len(shruti_analyzer.shruti_frequencies) == 22
        assert hasattr(shruti_analyzer, 'analyze_shruti')
    
    def test_perfect_shruti_detection(self, shruti_analyzer):
        """Test detection of perfect shruti frequencies."""
        # Test Sa (1st shruti)
        sa_freq = 261.63
        result = shruti_analyzer.analyze_shruti(sa_freq)
        
        assert result['shruti_name'] == 'Shadja'
        assert result['shruti_number'] == 1
        assert result['deviation_cents'] < 5
        assert result['accuracy_score'] > 0.95
    
    def test_shruti_deviation_calculation(self, shruti_analyzer):
        """Test calculation of frequency deviations."""
        # Test slightly sharp Sa
        sharp_sa = 265.0  # About 22 cents sharp
        result = shruti_analyzer.analyze_shruti(sharp_sa)
        
        assert result['shruti_name'] == 'Shadja'
        assert 20 < result['deviation_cents'] < 30
        assert 0.7 < result['accuracy_score'] < 0.9
    
    def test_microtonal_detection(self, shruti_analyzer):
        """Test detection of microtonal intervals."""
        # Test Suddha Rishabha (5/4 ratio)
        ri_freq = shruti_analyzer.base_sa * (5/4)
        result = shruti_analyzer.analyze_shruti(ri_freq)
        
        assert 'Rishabha' in result['shruti_name']
        assert result['accuracy_score'] > 0.9
    
    def test_out_of_range_frequencies(self, shruti_analyzer):
        """Test handling of out-of-range frequencies."""
        # Test very low frequency
        low_freq = 50.0
        result = shruti_analyzer.analyze_shruti(low_freq)
        assert result['accuracy_score'] < 0.5
        
        # Test very high frequency
        high_freq = 5000.0
        result = shruti_analyzer.analyze_shruti(high_freq)
        assert result['accuracy_score'] < 0.5


class TestAudioSynthesizer:
    """Test audio synthesis capabilities."""
    
    @pytest.fixture
    def synthesizer(self):
        return AudioSynthesizer()
    
    def test_synthesizer_initialization(self, synthesizer):
        """Test synthesizer initializes correctly."""
        assert synthesizer.sample_rate == 44100
        assert hasattr(synthesizer, 'generate_sine_wave')
        assert hasattr(synthesizer, 'generate_complex_tone')
    
    def test_sine_wave_generation(self, synthesizer):
        """Test pure sine wave generation."""
        frequency = 440.0
        duration = 1.0
        
        audio_data = synthesizer.generate_sine_wave(frequency, duration)
        
        assert len(audio_data) == int(44100 * duration)
        assert audio_data.dtype == np.float32
        assert -1.0 <= np.max(audio_data) <= 1.0
        assert -1.0 <= np.min(audio_data) <= -1.0
    
    def test_complex_tone_generation(self, synthesizer):
        """Test complex harmonic tone generation."""
        frequency = 261.63  # C4
        duration = 0.5
        harmonics = [1.0, 0.5, 0.25, 0.125]  # Fundamental + 3 harmonics
        
        audio_data = synthesizer.generate_complex_tone(
            frequency, duration, harmonics
        )
        
        assert len(audio_data) == int(44100 * duration)
        assert audio_data.dtype == np.float32
        
        # Check that harmonics are present (FFT analysis)
        fft = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/44100)
        
        # Find peaks near expected harmonics
        for i, harmonic_amp in enumerate(harmonics):
            if harmonic_amp > 0.1:  # Only check significant harmonics
                expected_freq = frequency * (i + 1)
                freq_index = np.argmin(np.abs(freqs - expected_freq))
                assert np.abs(fft[freq_index]) > 0.1


class TestTanpuraGenerator:
    """Test tanpura drone generation."""
    
    @pytest.fixture
    def tanpura(self):
        return TanpuraGenerator()
    
    def test_tanpura_initialization(self, tanpura):
        """Test tanpura generator initializes correctly."""
        assert tanpura.base_frequency == 261.63  # C4 (Sa)
        assert len(tanpura.string_ratios) == 4  # 4 strings
        assert hasattr(tanpura, 'generate_drone')
    
    def test_drone_generation(self, tanpura):
        """Test basic drone generation."""
        duration = 2.0
        drone_audio = tanpura.generate_drone(duration)
        
        assert len(drone_audio) == int(44100 * duration)
        assert drone_audio.dtype == np.float32
        
        # Check that all string frequencies are present
        fft = np.fft.fft(drone_audio)
        freqs = np.fft.fftfreq(len(drone_audio), 1/44100)
        
        for ratio in tanpura.string_ratios:
            expected_freq = tanpura.base_frequency * ratio
            freq_index = np.argmin(np.abs(freqs - expected_freq))
            assert np.abs(fft[freq_index]) > 0.05
    
    def test_raga_specific_tuning(self, tanpura):
        """Test raga-specific tanpura tuning."""
        # Test Kalyan raga tuning (with Tivra Ma)
        kalyan_tuning = tanpura.get_raga_tuning('Kalyan')
        
        assert len(kalyan_tuning) == 4
        assert kalyan_tuning['pa'] == 3/2  # Perfect fifth
        assert kalyan_tuning['ma'] == 45/32  # Tivra Ma


class TestMetronomeGenerator:
    """Test metronome functionality."""
    
    @pytest.fixture
    def metronome(self):
        return MetronomeGenerator()
    
    def test_metronome_initialization(self, metronome):
        """Test metronome initializes correctly."""
        assert metronome.bpm == 120  # Default tempo
        assert hasattr(metronome, 'generate_click')
        assert hasattr(metronome, 'generate_pattern')
    
    def test_click_generation(self, metronome):
        """Test individual click generation."""
        click_audio = metronome.generate_click()
        
        assert len(click_audio) > 0
        assert click_audio.dtype == np.float32
        assert np.max(click_audio) > 0.1  # Should have audible amplitude
    
    def test_pattern_generation(self, metronome):
        """Test metronome pattern generation."""
        # Test 4/4 time signature for 2 bars
        pattern_audio = metronome.generate_pattern(
            time_signature=(4, 4), 
            num_bars=2
        )
        
        expected_length = int(44100 * (2 * 4 * 60 / 120))  # 2 bars at 120 BPM
        assert abs(len(pattern_audio) - expected_length) < 1000  # Allow small tolerance
    
    def test_tempo_changes(self, metronome):
        """Test tempo changes."""
        # Test different tempos
        tempos = [60, 120, 180]
        
        for bpm in tempos:
            metronome.set_tempo(bpm)
            pattern = metronome.generate_pattern((4, 4), 1)
            
            expected_duration = 4 * 60 / bpm  # 4 beats at given BPM
            actual_duration = len(pattern) / 44100
            
            assert abs(actual_duration - expected_duration) < 0.1


@pytest.mark.asyncio
class TestAudioEngineIntegration:
    """Integration tests for complete audio processing pipeline."""
    
    async def test_real_time_pitch_detection_simulation(self, pitch_detector, shruti_analyzer):
        """Simulate real-time pitch detection and analysis."""
        # Simulate continuous audio input
        frequencies_to_test = [261.63, 293.66, 329.63, 349.23]  # Sa, Ri, Ga, Ma
        
        results = []
        for freq in frequencies_to_test:
            # Generate audio chunk
            t = np.linspace(0, 0.1, 4410)  # 100ms chunk
            audio_chunk = np.sin(2 * np.pi * freq * t).astype(np.float32)
            
            # Detect pitch
            pitch_result = pitch_detector.detect_pitch(audio_chunk)
            
            if pitch_result and pitch_result.confidence > 0.7:
                # Analyze shruti
                shruti_result = shruti_analyzer.analyze_shruti(pitch_result.frequency)
                results.append({
                    'detected_freq': pitch_result.frequency,
                    'target_freq': freq,
                    'shruti': shruti_result['shruti_name'],
                    'accuracy': shruti_result['accuracy_score']
                })
        
        # Verify results
        assert len(results) == 4
        for result in results:
            assert abs(result['detected_freq'] - result['target_freq']) < 5.0
            assert result['accuracy'] > 0.8
    
    async def test_audio_synthesis_and_analysis_roundtrip(self, synthesizer, pitch_detector):
        """Test generating audio and analyzing it back."""
        test_frequency = 440.0  # A4
        duration = 1.0
        
        # Generate audio
        synthesized_audio = synthesizer.generate_sine_wave(test_frequency, duration)
        
        # Analyze generated audio
        detected_result = pitch_detector.detect_pitch(synthesized_audio)
        
        assert detected_result is not None
        assert abs(detected_result.frequency - test_frequency) < 1.0
        assert detected_result.confidence > 0.9
    
    async def test_performance_benchmarks(self, pitch_detector):
        """Test performance of audio processing."""
        import time
        
        # Generate test audio
        audio_data = np.random.normal(0, 0.1, 44100).astype(np.float32)
        
        # Measure processing time
        start_time = time.time()
        for _ in range(10):
            pitch_detector.detect_pitch(audio_data)
        end_time = time.time()
        
        average_time = (end_time - start_time) / 10
        
        # Should process 1 second of audio in less than 100ms
        assert average_time < 0.1
    
    async def test_memory_usage(self, pitch_detector, synthesizer):
        """Test memory usage during audio processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple audio chunks
        for _ in range(100):
            audio_data = synthesizer.generate_sine_wave(440.0, 0.1)
            pitch_detector.detect_pitch(audio_data)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024