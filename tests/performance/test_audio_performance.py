"""
Enhanced Audio Performance Testing Suite
Comprehensive performance validation for optimized audio engine
"""

import pytest
import time
import numpy as np
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os
from unittest.mock import patch, MagicMock

from core.services.audio_engine import (
    CarnaticAudioEngine,
    AdvancedPitchDetector,
    AudioConfig,
    PitchDetectionResult
)
from core.models.shruti import ShrutiSystem


class TestAudioEnginePerformance:
    """Performance tests for optimized audio engine"""

    @pytest.fixture
    def optimized_config(self):
        """Optimized audio configuration for performance testing"""
        return AudioConfig(
            buffer_size=1024,  # Reduced for lower latency
            fft_size=4096,     # Optimized balance
            enable_parallel_processing=True,
            max_worker_threads=4,
            cache_size=128,
            use_optimized_fft=True
        )

    @pytest.fixture
    def audio_engine(self, optimized_config):
        """Carnatic audio engine with optimized configuration"""
        return CarnaticAudioEngine(optimized_config)

    @pytest.fixture
    def test_audio_samples(self):
        """Generate test audio samples for performance testing"""
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        samples = {}
        # Generate various test signals
        frequencies = [261.63, 293.66, 329.63, 349.23, 392.00]  # Sa, Ri, Ga, Ma, Pa

        for i, freq in enumerate(frequencies):
            # Pure tone
            pure_tone = np.sin(2 * np.pi * freq * t).astype(np.float32)

            # Complex harmonic tone
            complex_tone = (
                pure_tone +
                0.5 * np.sin(2 * np.pi * 2 * freq * t) +
                0.25 * np.sin(2 * np.pi * 3 * freq * t)
            ).astype(np.float32)

            samples[f'pure_{i}'] = pure_tone
            samples[f'complex_{i}'] = complex_tone

        return samples

    def test_pitch_detection_latency(self, audio_engine, test_audio_samples):
        """Test pitch detection latency meets real-time requirements (<25ms)"""
        latencies = []

        for sample_name, audio_data in test_audio_samples.items():
            # Test with smaller chunks for real-time simulation
            chunk_size = 1024  # 23ms at 44.1kHz
            num_chunks = len(audio_data) // chunk_size

            for i in range(0, min(num_chunks, 10)):  # Test 10 chunks
                chunk = audio_data[i * chunk_size:(i + 1) * chunk_size]

                start_time = time.time()
                result = audio_engine.detect_shruti(chunk)
                end_time = time.time()

                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)

        avg_latency = np.mean(latencies)
        max_latency = np.max(latencies)
        p95_latency = np.percentile(latencies, 95)

        print(f"Latency stats: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms, p95={p95_latency:.2f}ms")

        # Performance requirements
        assert avg_latency < 25.0, f"Average latency {avg_latency:.2f}ms exceeds 25ms requirement"
        assert p95_latency < 50.0, f"95th percentile latency {p95_latency:.2f}ms exceeds 50ms requirement"
        assert max_latency < 100.0, f"Maximum latency {max_latency:.2f}ms exceeds 100ms requirement"

    def test_concurrent_processing_performance(self, optimized_config, test_audio_samples):
        """Test concurrent audio processing performance"""
        num_concurrent_sessions = 10
        engines = [CarnaticAudioEngine(optimized_config) for _ in range(num_concurrent_sessions)]

        def process_session(engine, audio_samples):
            """Process audio samples in a single session"""
            results = []
            for sample_name, audio_data in audio_samples.items():
                chunk_size = 1024
                chunk = audio_data[:chunk_size]

                start_time = time.time()
                result = engine.detect_shruti(chunk)
                end_time = time.time()

                results.append({
                    'sample': sample_name,
                    'latency_ms': (end_time - start_time) * 1000,
                    'success': result is not None
                })
            return results

        # Run concurrent processing
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent_sessions) as executor:
            futures = [
                executor.submit(process_session, engines[i], test_audio_samples)
                for i in range(num_concurrent_sessions)
            ]

            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        end_time = time.time()
        total_duration = end_time - start_time

        # Analyze results
        latencies = [r['latency_ms'] for r in all_results]
        success_rate = sum(r['success'] for r in all_results) / len(all_results)

        avg_latency = np.mean(latencies)
        throughput = len(all_results) / total_duration

        print(f"Concurrent processing: {num_concurrent_sessions} sessions")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Throughput: {throughput:.1f} chunks/sec")

        # Performance requirements
        assert success_rate > 0.95, f"Success rate {success_rate:.2%} below 95% requirement"
        assert avg_latency < 50.0, f"Concurrent average latency {avg_latency:.2f}ms exceeds 50ms"
        assert throughput > 50.0, f"Throughput {throughput:.1f} chunks/sec below 50 requirement"

    def test_memory_efficiency(self, audio_engine, test_audio_samples):
        """Test memory usage efficiency during extended processing"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process audio continuously for 60 seconds simulation
        num_iterations = 100
        memory_samples = []

        for i in range(num_iterations):
            # Process all test samples
            for audio_data in test_audio_samples.values():
                chunk_size = 1024
                chunk = audio_data[:chunk_size]
                result = audio_engine.detect_shruti(chunk)

            # Sample memory usage every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples)

        print(f"Memory usage: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB, max={max_memory:.1f}MB")

        # Memory efficiency requirements
        assert memory_increase < 50.0, f"Memory increase {memory_increase:.1f}MB exceeds 50MB limit"
        assert max_memory < initial_memory + 100, f"Peak memory {max_memory:.1f}MB too high"

    def test_cache_effectiveness(self, audio_engine, test_audio_samples):
        """Test caching effectiveness for performance optimization"""
        # Get pitch detector to access cache
        detector = audio_engine.pitch_detector

        # First pass - populate cache
        sample_audio = list(test_audio_samples.values())[0][:1024]

        start_time = time.time()
        result1 = detector.detect_pitch(sample_audio)
        first_pass_time = time.time() - start_time

        # Second pass - should use cache
        start_time = time.time()
        result2 = detector.detect_pitch(sample_audio)
        second_pass_time = time.time() - start_time

        # Verify cache effectiveness
        speedup = first_pass_time / second_pass_time if second_pass_time > 0 else 1

        print(f"Cache test: first={first_pass_time*1000:.2f}ms, second={second_pass_time*1000:.2f}ms")
        print(f"Cache speedup: {speedup:.2f}x")

        # Cache should provide some speedup
        assert speedup > 1.0, f"Cache speedup {speedup:.2f}x insufficient"
        assert result1 is not None and result2 is not None, "Results should be consistent"

    def test_parallel_processing_benefit(self, test_audio_samples):
        """Test parallel processing performance benefit"""
        audio_sample = list(test_audio_samples.values())[0][:1024]

        # Test sequential processing
        sequential_config = AudioConfig(enable_parallel_processing=False)
        sequential_detector = AdvancedPitchDetector(sequential_config)

        start_time = time.time()
        for _ in range(20):
            sequential_detector.detect_pitch(audio_sample)
        sequential_time = time.time() - start_time

        # Test parallel processing
        parallel_config = AudioConfig(enable_parallel_processing=True, max_worker_threads=4)
        parallel_detector = AdvancedPitchDetector(parallel_config)

        start_time = time.time()
        for _ in range(20):
            parallel_detector.detect_pitch(audio_sample)
        parallel_time = time.time() - start_time

        speedup = sequential_time / parallel_time if parallel_time > 0 else 1

        print(f"Parallel processing: sequential={sequential_time:.3f}s, parallel={parallel_time:.3f}s")
        print(f"Parallel speedup: {speedup:.2f}x")

        # Parallel processing should provide speedup
        assert speedup > 1.2, f"Parallel speedup {speedup:.2f}x insufficient (expected >1.2x)"

    def test_real_time_audio_streaming_simulation(self, audio_engine):
        """Simulate real-time audio streaming with performance validation"""
        sample_rate = 44100
        chunk_size = 1024  # ~23ms chunks
        duration = 5.0  # 5 second simulation

        # Generate continuous audio stream
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 261.63  # Sa
        audio_stream = np.sin(2 * np.pi * frequency * t).astype(np.float32)

        # Process in real-time chunks
        processing_times = []
        chunk_intervals = []
        successful_detections = 0

        last_time = time.time()

        for i in range(0, len(audio_stream), chunk_size):
            current_time = time.time()
            chunk_intervals.append(current_time - last_time)

            chunk = audio_stream[i:i + chunk_size]
            if len(chunk) < chunk_size:
                break

            # Process chunk
            start_time = time.time()
            result = audio_engine.detect_shruti(chunk)
            processing_time = time.time() - start_time

            processing_times.append(processing_time * 1000)  # Convert to ms

            if result:
                successful_detections += 1

            last_time = current_time

            # Simulate real-time constraint
            expected_chunk_duration = chunk_size / sample_rate
            if processing_time > expected_chunk_duration:
                print(f"Real-time constraint violation: {processing_time*1000:.2f}ms > {expected_chunk_duration*1000:.2f}ms")

        # Analyze real-time performance
        avg_processing_time = np.mean(processing_times)
        max_processing_time = np.max(processing_times)
        real_time_violations = sum(1 for t in processing_times if t > 23.0)  # 23ms = chunk duration
        success_rate = successful_detections / len(processing_times)

        print(f"Real-time simulation: {len(processing_times)} chunks over {duration}s")
        print(f"Average processing: {avg_processing_time:.2f}ms")
        print(f"Max processing: {max_processing_time:.2f}ms")
        print(f"Real-time violations: {real_time_violations}")
        print(f"Detection success rate: {success_rate:.2%}")

        # Real-time requirements
        assert avg_processing_time < 23.0, f"Average processing {avg_processing_time:.2f}ms exceeds real-time limit"
        assert real_time_violations < len(processing_times) * 0.05, f"Too many real-time violations: {real_time_violations}"
        assert success_rate > 0.90, f"Detection success rate {success_rate:.2%} below 90%"


class TestWebSocketPerformance:
    """Performance tests for optimized WebSocket handling"""

    def test_websocket_connection_handling(self):
        """Test WebSocket connection management performance"""
        from api.audio.websocket import active_sessions, audio_engines

        # Simulate multiple connections
        num_connections = 50
        session_ids = [f"session_{i}" for i in range(num_connections)]

        start_time = time.time()

        # Simulate connection setup
        for session_id in session_ids:
            # Mock session setup
            active_sessions[session_id] = {
                'connected_at': time.time(),
                'audio_buffer': [],
                'performance_stats': {'processed_chunks': 0}
            }

        setup_time = time.time() - start_time

        # Test session cleanup
        start_time = time.time()
        for session_id in session_ids:
            if session_id in active_sessions:
                del active_sessions[session_id]
        cleanup_time = time.time() - start_time

        print(f"WebSocket performance: setup={setup_time:.3f}s, cleanup={cleanup_time:.3f}s")
        print(f"Connections per second: {num_connections/setup_time:.1f}")

        # Performance requirements
        assert setup_time < 1.0, f"Connection setup time {setup_time:.3f}s too slow"
        assert cleanup_time < 0.5, f"Cleanup time {cleanup_time:.3f}s too slow"
        assert num_connections/setup_time > 100, f"Connection rate {num_connections/setup_time:.1f}/s too low"

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self):
        """Test concurrent audio chunk processing performance"""
        from api.audio.websocket import executor

        # Generate test audio chunks
        chunk_size = 1024
        num_chunks = 20
        chunks = []

        for i in range(num_chunks):
            frequency = 261.63 + i * 10  # Varying frequencies
            t = np.linspace(0, chunk_size/44100, chunk_size)
            chunk = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            chunks.append(chunk)

        # Mock audio processing function
        def mock_process_chunk(chunk):
            time.sleep(0.01)  # Simulate processing time
            return {'frequency': 261.63, 'confidence': 0.9}

        # Test concurrent processing
        start_time = time.time()

        futures = []
        for chunk in chunks:
            future = executor.submit(mock_process_chunk, chunk)
            futures.append(future)

        # Wait for all to complete
        results = []
        for future in futures:
            result = future.result(timeout=1.0)
            results.append(result)

        processing_time = time.time() - start_time
        throughput = len(chunks) / processing_time

        print(f"Concurrent processing: {len(chunks)} chunks in {processing_time:.3f}s")
        print(f"Throughput: {throughput:.1f} chunks/sec")

        # Performance requirements
        assert len(results) == num_chunks, "All chunks should be processed"
        assert processing_time < 1.0, f"Processing time {processing_time:.3f}s too slow"
        assert throughput > 50.0, f"Throughput {throughput:.1f} chunks/sec too low"


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Benchmark tests for performance regression detection"""

    def test_pitch_detection_benchmark(self, benchmark):
        """Benchmark pitch detection performance"""
        config = AudioConfig(enable_parallel_processing=True)
        detector = AdvancedPitchDetector(config)

        # Generate test audio
        sample_rate = 44100
        duration = 0.1  # 100ms
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        # Benchmark the detection
        result = benchmark(detector.detect_pitch, audio_data)

        assert result is not None
        assert result.confidence > 0.8

    def test_shruti_analysis_benchmark(self, benchmark):
        """Benchmark shruti analysis performance"""
        config = AudioConfig()
        engine = CarnaticAudioEngine(config)

        # Generate test audio for Sa
        sample_rate = 44100
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 261.63 * t).astype(np.float32)

        # Benchmark shruti detection
        result = benchmark(engine.detect_shruti, audio_data)

        if result:
            assert result.shruti is not None
            assert abs(result.cent_deviation) < 50


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--benchmark-only"])