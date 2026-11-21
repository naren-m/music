"""
End-to-End Performance Validation Tests
Validates real-world performance improvements with Playwright
"""

import asyncio
import json
import statistics
import time

import numpy as np
import pytest
from playwright.async_api import BrowserContext, Page, async_playwright


class TestPerformanceValidation:
    """E2E tests to validate performance improvements"""

    @pytest.fixture
    async def browser_context(self):
        """Create browser context for performance testing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-web-security",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--enable-automation",
                ],
            )

            context = await browser.new_context(
                permissions=["microphone"], viewport={"width": 1280, "height": 720}
            )

            yield context
            await browser.close()

    @pytest.fixture
    async def app_page(self, browser_context):
        """Create page with Carnatic app loaded"""
        page = await browser_context.new_page()

        # Navigate to the application
        await page.goto("http://localhost:5001/carnatic")

        # Wait for app to load
        await page.wait_for_selector('[data-testid="audio-controls"]', timeout=10000)

        yield page
        await page.close()

    async def test_websocket_connection_performance(self, app_page: Page):
        """Test WebSocket connection establishment performance"""
        print("\n🔌 Testing WebSocket connection performance...")

        # Track connection metrics
        connection_times = []
        message_latencies = []

        for i in range(5):  # Test 5 connections
            start_time = time.time()

            # Start detection to trigger WebSocket connection
            await app_page.click('[data-testid="start-detection-btn"]')

            # Wait for connection confirmation
            await app_page.wait_for_selector(
                '[data-testid="connection-status"][data-status="connected"]',
                timeout=5000,
            )

            connection_time = (time.time() - start_time) * 1000  # ms
            connection_times.append(connection_time)

            # Test ping-pong latency
            ping_start = time.time()
            await app_page.evaluate(
                """
                window.socket.emit('ping');
            """
            )

            # Wait for pong response
            await app_page.wait_for_function(
                """
                window.lastPongTime && (Date.now() - window.lastPongTime) < 1000
            """,
                timeout=2000,
            )

            latency = (time.time() - ping_start) * 1000
            message_latencies.append(latency)

            # Stop detection
            await app_page.click('[data-testid="stop-detection-btn"]')
            await asyncio.sleep(0.5)  # Brief pause between tests

        # Analyze results
        avg_connection_time = statistics.mean(connection_times)
        avg_latency = statistics.mean(message_latencies)
        max_connection_time = max(connection_times)
        max_latency = max(message_latencies)

        print(f"📊 Connection Performance:")
        print(f"   Average connection time: {avg_connection_time:.1f}ms")
        print(f"   Maximum connection time: {max_connection_time:.1f}ms")
        print(f"   Average message latency: {avg_latency:.1f}ms")
        print(f"   Maximum message latency: {max_latency:.1f}ms")

        # Performance assertions
        assert (
            avg_connection_time < 500
        ), f"Average connection time {avg_connection_time:.1f}ms exceeds 500ms"
        assert (
            max_connection_time < 1000
        ), f"Max connection time {max_connection_time:.1f}ms exceeds 1000ms"
        assert avg_latency < 100, f"Average latency {avg_latency:.1f}ms exceeds 100ms"
        assert max_latency < 200, f"Max latency {max_latency:.1f}ms exceeds 200ms"

    async def test_audio_processing_real_time_performance(self, app_page: Page):
        """Test real-time audio processing performance with simulated audio"""
        print("\n🎵 Testing real-time audio processing performance...")

        # Start audio detection
        await app_page.click('[data-testid="start-detection-btn"]')
        await app_page.wait_for_selector(
            '[data-testid="detection-status"][data-status="active"]'
        )

        # Simulate audio chunks being sent
        processing_times = []
        chunk_count = 50

        for i in range(chunk_count):
            start_time = time.time()

            # Send simulated audio chunk (Sa frequency = 261.63 Hz)
            await app_page.evaluate(
                """
                const sampleRate = 44100;
                const frequency = 261.63;
                const duration = 0.023; // 23ms chunk
                const samples = Math.floor(sampleRate * duration);
                const audioData = new Float32Array(samples);

                for (let i = 0; i < samples; i++) {
                    audioData[i] = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 0.5;
                }

                window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
            """
            )

            # Wait for processing response
            try:
                await app_page.wait_for_function(
                    """
                    window.lastShruti_detected && 
                    (Date.now() - window.lastShruti_detected.timestamp * 1000) < 100
                """,
                    timeout=100,
                )  # 100ms timeout

                processing_time = (time.time() - start_time) * 1000
                processing_times.append(processing_time)

            except:
                # Timeout - record as slow processing
                processing_times.append(100)  # Max timeout value

        # Stop detection
        await app_page.click('[data-testid="stop-detection-btn"]')

        # Analyze processing performance
        successful_chunks = len([t for t in processing_times if t < 50])  # Under 50ms
        avg_processing_time = statistics.mean(processing_times)
        p95_processing_time = np.percentile(processing_times, 95)
        success_rate = successful_chunks / chunk_count

        print(f"📊 Audio Processing Performance:")
        print(f"   Processed chunks: {chunk_count}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Average processing time: {avg_processing_time:.1f}ms")
        print(f"   95th percentile: {p95_processing_time:.1f}ms")

        # Performance assertions
        assert (
            success_rate > 0.90
        ), f"Success rate {success_rate:.1%} below 90% requirement"
        assert (
            avg_processing_time < 50
        ), f"Average processing {avg_processing_time:.1f}ms exceeds 50ms"
        assert (
            p95_processing_time < 75
        ), f"95th percentile {p95_processing_time:.1f}ms exceeds 75ms"

    async def test_concurrent_user_simulation(self, browser_context: BrowserContext):
        """Test concurrent user performance simulation"""
        print("\n👥 Testing concurrent user performance...")

        num_users = 10
        pages = []

        try:
            # Create multiple pages (users)
            for i in range(num_users):
                page = await browser_context.new_page()
                await page.goto("http://localhost:5001/carnatic")
                await page.wait_for_selector('[data-testid="audio-controls"]')
                pages.append(page)

            # Start detection on all pages simultaneously
            start_time = time.time()

            tasks = []
            for page in pages:
                task = asyncio.create_task(
                    page.click('[data-testid="start-detection-btn"]')
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            setup_time = (time.time() - start_time) * 1000

            # Verify all connections are active
            active_connections = 0
            for page in pages:
                try:
                    await page.wait_for_selector(
                        '[data-testid="connection-status"][data-status="connected"]',
                        timeout=5000,
                    )
                    active_connections += 1
                except:
                    pass

            # Send audio data from all users
            processing_start = time.time()

            audio_tasks = []
            for page in pages:
                task = asyncio.create_task(
                    page.evaluate(
                        """
                    const audioData = new Float32Array(1024).fill(0.5);
                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
                """
                    )
                )
                audio_tasks.append(task)

            await asyncio.gather(*audio_tasks, return_exceptions=True)

            processing_time = (time.time() - processing_start) * 1000

            print(f"📊 Concurrent User Performance:")
            print(f"   Users simulated: {num_users}")
            print(f"   Active connections: {active_connections}")
            print(f"   Setup time: {setup_time:.1f}ms")
            print(f"   Processing time: {processing_time:.1f}ms")

            # Performance assertions
            connection_rate = active_connections / num_users
            assert (
                connection_rate > 0.8
            ), f"Connection rate {connection_rate:.1%} below 80%"
            assert setup_time < 2000, f"Setup time {setup_time:.1f}ms exceeds 2000ms"
            assert (
                processing_time < 500
            ), f"Processing time {processing_time:.1f}ms exceeds 500ms"

        finally:
            # Cleanup
            for page in pages:
                try:
                    await page.close()
                except:
                    pass

    async def test_memory_usage_stability(self, app_page: Page):
        """Test memory usage stability during extended use"""
        print("\n🧠 Testing memory usage stability...")

        # Start detection
        await app_page.click('[data-testid="start-detection-btn"]')

        # Monitor performance metrics
        initial_metrics = await app_page.evaluate("performance.memory")

        # Simulate extended usage (send many audio chunks)
        for cycle in range(5):  # 5 cycles of 20 chunks each
            for i in range(20):
                await app_page.evaluate(
                    """
                    const audioData = new Float32Array(1024);
                    for (let j = 0; j < 1024; j++) {
                        audioData[j] = Math.sin(2 * Math.PI * 261.63 * j / 44100) * 0.5;
                    }
                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
                """
                )

                await asyncio.sleep(0.01)  # 10ms delay

            # Check memory after each cycle
            current_metrics = await app_page.evaluate("performance.memory")
            memory_increase = (
                (current_metrics["usedJSHeapSize"] - initial_metrics["usedJSHeapSize"])
                / 1024
                / 1024
            )  # MB

            print(f"   Cycle {cycle + 1}: Memory increase = {memory_increase:.1f}MB")

            # Memory should not increase excessively
            assert (
                memory_increase < 50
            ), f"Memory increase {memory_increase:.1f}MB exceeds 50MB limit"

        # Stop detection
        await app_page.click('[data-testid="stop-detection-btn"]')

        # Final memory check
        final_metrics = await app_page.evaluate("performance.memory")
        total_memory_increase = (
            (final_metrics["usedJSHeapSize"] - initial_metrics["usedJSHeapSize"])
            / 1024
            / 1024
        )

        print(f"📊 Memory Stability:")
        print(f"   Total memory increase: {total_memory_increase:.1f}MB")
        print(
            f"   Final heap size: {final_metrics['usedJSHeapSize'] / 1024 / 1024:.1f}MB"
        )

        assert (
            total_memory_increase < 100
        ), f"Total memory increase {total_memory_increase:.1f}MB exceeds 100MB"

    async def test_ui_responsiveness_under_load(self, app_page: Page):
        """Test UI responsiveness during heavy audio processing"""
        print("\n🖱️ Testing UI responsiveness under load...")

        # Start detection
        await app_page.click('[data-testid="start-detection-btn"]')

        # Create high-frequency audio processing load
        load_task = asyncio.create_task(self._create_audio_load(app_page))

        # Test UI responsiveness during load
        ui_response_times = []

        for i in range(10):
            start_time = time.time()

            # Click base frequency button
            await app_page.click('[data-testid="freq-261-btn"]')

            # Wait for UI update
            await app_page.wait_for_function(
                """
                document.querySelector('[data-testid="base-frequency-display"]').textContent.includes('261.63')
            """
            )

            response_time = (time.time() - start_time) * 1000
            ui_response_times.append(response_time)

            await asyncio.sleep(0.1)  # Brief pause

        # Stop load and detection
        load_task.cancel()
        await app_page.click('[data-testid="stop-detection-btn"]')

        # Analyze UI responsiveness
        avg_response_time = statistics.mean(ui_response_times)
        max_response_time = max(ui_response_times)

        print(f"📊 UI Responsiveness Under Load:")
        print(f"   Average response time: {avg_response_time:.1f}ms")
        print(f"   Maximum response time: {max_response_time:.1f}ms")

        # UI should remain responsive
        assert (
            avg_response_time < 200
        ), f"Average UI response {avg_response_time:.1f}ms exceeds 200ms"
        assert (
            max_response_time < 500
        ), f"Max UI response {max_response_time:.1f}ms exceeds 500ms"

    async def _create_audio_load(self, page: Page):
        """Create continuous audio processing load"""
        try:
            while True:
                await page.evaluate(
                    """
                    const audioData = new Float32Array(1024);
                    for (let i = 0; i < 1024; i++) {
                        audioData[i] = Math.random() * 0.5;
                    }
                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
                """
                )
                await asyncio.sleep(0.02)  # 50 FPS
        except asyncio.CancelledError:
            pass

    async def test_performance_regression_detection(self, app_page: Page):
        """Test for performance regressions against baseline metrics"""
        print("\n📈 Testing for performance regressions...")

        # Baseline performance expectations (optimized values)
        baseline_metrics = {
            "connection_time_ms": 300,
            "audio_processing_ms": 25,
            "ui_response_ms": 100,
            "memory_usage_mb": 30,
        }

        # Test connection performance
        connection_start = time.time()
        await app_page.click('[data-testid="start-detection-btn"]')
        await app_page.wait_for_selector(
            '[data-testid="connection-status"][data-status="connected"]'
        )
        connection_time = (time.time() - connection_start) * 1000

        # Test audio processing
        processing_start = time.time()
        await app_page.evaluate(
            """
            const audioData = new Float32Array(1024).fill(0.5);
            window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
        """
        )
        await app_page.wait_for_function("window.lastShruti_detected", timeout=100)
        processing_time = (time.time() - processing_start) * 1000

        # Test UI response
        ui_start = time.time()
        await app_page.click('[data-testid="freq-293-btn"]')
        await app_page.wait_for_function(
            'document.querySelector("[data-testid=base-frequency-display]").textContent.includes("293")'
        )
        ui_response_time = (time.time() - ui_start) * 1000

        # Check memory usage
        memory_metrics = await app_page.evaluate("performance.memory")
        memory_usage = memory_metrics["usedJSHeapSize"] / 1024 / 1024

        # Stop detection
        await app_page.click('[data-testid="stop-detection-btn"]')

        # Calculate performance ratios vs baseline
        actual_metrics = {
            "connection_time_ms": connection_time,
            "audio_processing_ms": processing_time,
            "ui_response_ms": ui_response_time,
            "memory_usage_mb": memory_usage,
        }

        print(f"📊 Performance Regression Analysis:")

        regression_detected = False
        for metric, baseline in baseline_metrics.items():
            actual = actual_metrics[metric]
            ratio = actual / baseline
            status = "✅" if ratio <= 1.2 else "⚠️" if ratio <= 1.5 else "❌"

            print(
                f"   {metric}: {actual:.1f} vs {baseline:.1f} (ratio: {ratio:.2f}) {status}"
            )

            if ratio > 1.5:  # 50% regression threshold
                regression_detected = True

        assert (
            not regression_detected
        ), "Performance regression detected - metrics exceed 150% of baseline"

        print("✅ No significant performance regressions detected")


if __name__ == "__main__":
    # Run E2E performance validation
    pytest.main([__file__, "-v", "--tb=short"])
