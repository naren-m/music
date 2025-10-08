"""
End-to-End Performance Validation Tests
Validates real-world performance improvements with Playwright
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, BrowserContext
import json
import statistics
import numpy as np


class TestPerformanceValidation:
    """E2E tests to validate performance improvements"""

    @pytest.fixture
    async def browser_context(self):
        """Create browser context for performance testing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--enable-automation'
                ]
            )

            context = await browser.new_context(
                permissions=['microphone'],
                viewport={'width': 1280, 'height': 720}
            )

            yield context
            await browser.close()

    @pytest.fixture
    async def app_page(self, browser_context):
        """Create page with Carnatic app loaded"""
        page = await browser_context.new_page()

        # Navigate to the application
        await page.goto('http://localhost:5001/carnatic')

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
            await app_page.wait_for_selector('[data-testid="connection-status"][data-status="connected"]', timeout=5000)

            connection_time = (time.time() - start_time) * 1000  # ms
            connection_times.append(connection_time)

            # Test ping-pong latency
            ping_start = time.time()
            await app_page.evaluate('''
                window.socket.emit('ping');
            ''')

            # Wait for pong response
            await app_page.wait_for_function('''
                window.lastPongTime && (Date.now() - window.lastPongTime) < 1000
            ''', timeout=2000)

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
        assert avg_connection_time < 500, f"Average connection time {avg_connection_time:.1f}ms exceeds 500ms"
        assert max_connection_time < 1000, f"Max connection time {max_connection_time:.1f}ms exceeds 1000ms"
        assert avg_latency < 100, f"Average latency {avg_latency:.1f}ms exceeds 100ms"
        assert max_latency < 200, f"Max latency {max_latency:.1f}ms exceeds 200ms"

    async def test_audio_processing_real_time_performance(self, app_page: Page):
        """Test real-time audio processing performance with simulated audio"""
        print("\n🎵 Testing real-time audio processing performance...")

        # Start audio detection
        await app_page.click('[data-testid="start-detection-btn"]')
        await app_page.wait_for_selector('[data-testid="detection-status"][data-status="active"]')

        # Simulate audio chunks being sent
        processing_times = []
        chunk_count = 50

        for i in range(chunk_count):
            start_time = time.time()

            # Send simulated audio chunk (Sa frequency = 261.63 Hz)
            await app_page.evaluate('''
                const sampleRate = 44100;
                const frequency = 261.63;
                const duration = 0.023; // 23ms chunk
                const samples = Math.floor(sampleRate * duration);
                const audioData = new Float32Array(samples);

                for (let i = 0; i < samples; i++) {
                    audioData[i] = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 0.5;
                }

                window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });
            ''')\n            \n            # Wait for processing response\n            try:\n                await app_page.wait_for_function('''\n                    window.lastShruti_detected && \n                    (Date.now() - window.lastShruti_detected.timestamp * 1000) < 100\n                ''', timeout=100)  # 100ms timeout\n                \n                processing_time = (time.time() - start_time) * 1000\n                processing_times.append(processing_time)\n                \n            except:\n                # Timeout - record as slow processing\n                processing_times.append(100)  # Max timeout value\n        \n        # Stop detection\n        await app_page.click('[data-testid=\"stop-detection-btn\"]')\n        \n        # Analyze processing performance\n        successful_chunks = len([t for t in processing_times if t < 50])  # Under 50ms\n        avg_processing_time = statistics.mean(processing_times)\n        p95_processing_time = np.percentile(processing_times, 95)\n        success_rate = successful_chunks / chunk_count\n        \n        print(f\"📊 Audio Processing Performance:\")\n        print(f\"   Processed chunks: {chunk_count}\")\n        print(f\"   Success rate: {success_rate:.1%}\")\n        print(f\"   Average processing time: {avg_processing_time:.1f}ms\")\n        print(f\"   95th percentile: {p95_processing_time:.1f}ms\")\n        \n        # Performance assertions\n        assert success_rate > 0.90, f\"Success rate {success_rate:.1%} below 90% requirement\"\n        assert avg_processing_time < 50, f\"Average processing {avg_processing_time:.1f}ms exceeds 50ms\"\n        assert p95_processing_time < 75, f\"95th percentile {p95_processing_time:.1f}ms exceeds 75ms\"\n\n    async def test_concurrent_user_simulation(self, browser_context: BrowserContext):\n        \"\"\"Test concurrent user performance simulation\"\"\"\n        print(\"\\n👥 Testing concurrent user performance...\")\n        \n        num_users = 10\n        pages = []\n        \n        try:\n            # Create multiple pages (users)\n            for i in range(num_users):\n                page = await browser_context.new_page()\n                await page.goto('http://localhost:5001/carnatic')\n                await page.wait_for_selector('[data-testid=\"audio-controls\"]')\n                pages.append(page)\n            \n            # Start detection on all pages simultaneously\n            start_time = time.time()\n            \n            tasks = []\n            for page in pages:\n                task = asyncio.create_task(page.click('[data-testid=\"start-detection-btn\"]'))\n                tasks.append(task)\n            \n            await asyncio.gather(*tasks, return_exceptions=True)\n            \n            setup_time = (time.time() - start_time) * 1000\n            \n            # Verify all connections are active\n            active_connections = 0\n            for page in pages:\n                try:\n                    await page.wait_for_selector('[data-testid=\"connection-status\"][data-status=\"connected\"]', timeout=5000)\n                    active_connections += 1\n                except:\n                    pass\n            \n            # Send audio data from all users\n            processing_start = time.time()\n            \n            audio_tasks = []\n            for page in pages:\n                task = asyncio.create_task(page.evaluate('''\n                    const audioData = new Float32Array(1024).fill(0.5);\n                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });\n                '''))\n                audio_tasks.append(task)\n            \n            await asyncio.gather(*audio_tasks, return_exceptions=True)\n            \n            processing_time = (time.time() - processing_start) * 1000\n            \n            print(f\"📊 Concurrent User Performance:\")\n            print(f\"   Users simulated: {num_users}\")\n            print(f\"   Active connections: {active_connections}\")\n            print(f\"   Setup time: {setup_time:.1f}ms\")\n            print(f\"   Processing time: {processing_time:.1f}ms\")\n            \n            # Performance assertions\n            connection_rate = active_connections / num_users\n            assert connection_rate > 0.8, f\"Connection rate {connection_rate:.1%} below 80%\"\n            assert setup_time < 2000, f\"Setup time {setup_time:.1f}ms exceeds 2000ms\"\n            assert processing_time < 500, f\"Processing time {processing_time:.1f}ms exceeds 500ms\"\n            \n        finally:\n            # Cleanup\n            for page in pages:\n                try:\n                    await page.close()\n                except:\n                    pass\n\n    async def test_memory_usage_stability(self, app_page: Page):\n        \"\"\"Test memory usage stability during extended use\"\"\"\n        print(\"\\n🧠 Testing memory usage stability...\")\n        \n        # Start detection\n        await app_page.click('[data-testid=\"start-detection-btn\"]')\n        \n        # Monitor performance metrics\n        initial_metrics = await app_page.evaluate('performance.memory')\n        \n        # Simulate extended usage (send many audio chunks)\n        for cycle in range(5):  # 5 cycles of 20 chunks each\n            for i in range(20):\n                await app_page.evaluate('''\n                    const audioData = new Float32Array(1024);\n                    for (let j = 0; j < 1024; j++) {\n                        audioData[j] = Math.sin(2 * Math.PI * 261.63 * j / 44100) * 0.5;\n                    }\n                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });\n                ''')\n                \n                await asyncio.sleep(0.01)  # 10ms delay\n            \n            # Check memory after each cycle\n            current_metrics = await app_page.evaluate('performance.memory')\n            memory_increase = (current_metrics['usedJSHeapSize'] - initial_metrics['usedJSHeapSize']) / 1024 / 1024  # MB\n            \n            print(f\"   Cycle {cycle + 1}: Memory increase = {memory_increase:.1f}MB\")\n            \n            # Memory should not increase excessively\n            assert memory_increase < 50, f\"Memory increase {memory_increase:.1f}MB exceeds 50MB limit\"\n        \n        # Stop detection\n        await app_page.click('[data-testid=\"stop-detection-btn\"]')\n        \n        # Final memory check\n        final_metrics = await app_page.evaluate('performance.memory')\n        total_memory_increase = (final_metrics['usedJSHeapSize'] - initial_metrics['usedJSHeapSize']) / 1024 / 1024\n        \n        print(f\"📊 Memory Stability:\")\n        print(f\"   Total memory increase: {total_memory_increase:.1f}MB\")\n        print(f\"   Final heap size: {final_metrics['usedJSHeapSize'] / 1024 / 1024:.1f}MB\")\n        \n        assert total_memory_increase < 100, f\"Total memory increase {total_memory_increase:.1f}MB exceeds 100MB\"\n\n    async def test_ui_responsiveness_under_load(self, app_page: Page):\n        \"\"\"Test UI responsiveness during heavy audio processing\"\"\"\n        print(\"\\n🖱️ Testing UI responsiveness under load...\")\n        \n        # Start detection\n        await app_page.click('[data-testid=\"start-detection-btn\"]')\n        \n        # Create high-frequency audio processing load\n        load_task = asyncio.create_task(self._create_audio_load(app_page))\n        \n        # Test UI responsiveness during load\n        ui_response_times = []\n        \n        for i in range(10):\n            start_time = time.time()\n            \n            # Click base frequency button\n            await app_page.click('[data-testid=\"freq-261-btn\"]')\n            \n            # Wait for UI update\n            await app_page.wait_for_function('''\n                document.querySelector('[data-testid=\"base-frequency-display\"]').textContent.includes('261.63')\n            ''')\n            \n            response_time = (time.time() - start_time) * 1000\n            ui_response_times.append(response_time)\n            \n            await asyncio.sleep(0.1)  # Brief pause\n        \n        # Stop load and detection\n        load_task.cancel()\n        await app_page.click('[data-testid=\"stop-detection-btn\"]')\n        \n        # Analyze UI responsiveness\n        avg_response_time = statistics.mean(ui_response_times)\n        max_response_time = max(ui_response_times)\n        \n        print(f\"📊 UI Responsiveness Under Load:\")\n        print(f\"   Average response time: {avg_response_time:.1f}ms\")\n        print(f\"   Maximum response time: {max_response_time:.1f}ms\")\n        \n        # UI should remain responsive\n        assert avg_response_time < 200, f\"Average UI response {avg_response_time:.1f}ms exceeds 200ms\"\n        assert max_response_time < 500, f\"Max UI response {max_response_time:.1f}ms exceeds 500ms\"\n\n    async def _create_audio_load(self, page: Page):\n        \"\"\"Create continuous audio processing load\"\"\"\n        try:\n            while True:\n                await page.evaluate('''\n                    const audioData = new Float32Array(1024);\n                    for (let i = 0; i < 1024; i++) {\n                        audioData[i] = Math.random() * 0.5;\n                    }\n                    window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });\n                ''')\n                await asyncio.sleep(0.02)  # 50 FPS\n        except asyncio.CancelledError:\n            pass\n\n    async def test_performance_regression_detection(self, app_page: Page):\n        \"\"\"Test for performance regressions against baseline metrics\"\"\"\n        print(\"\\n📈 Testing for performance regressions...\")\n        \n        # Baseline performance expectations (optimized values)\n        baseline_metrics = {\n            'connection_time_ms': 300,\n            'audio_processing_ms': 25,\n            'ui_response_ms': 100,\n            'memory_usage_mb': 30\n        }\n        \n        # Test connection performance\n        connection_start = time.time()\n        await app_page.click('[data-testid=\"start-detection-btn\"]')\n        await app_page.wait_for_selector('[data-testid=\"connection-status\"][data-status=\"connected\"]')\n        connection_time = (time.time() - connection_start) * 1000\n        \n        # Test audio processing\n        processing_start = time.time()\n        await app_page.evaluate('''\n            const audioData = new Float32Array(1024).fill(0.5);\n            window.socket.emit('audio_chunk', { audio_data: Array.from(audioData) });\n        ''')\n        await app_page.wait_for_function('window.lastShruti_detected', timeout=100)\n        processing_time = (time.time() - processing_start) * 1000\n        \n        # Test UI response\n        ui_start = time.time()\n        await app_page.click('[data-testid=\"freq-293-btn\"]')\n        await app_page.wait_for_function('document.querySelector(\"[data-testid=base-frequency-display]\").textContent.includes(\"293\")')\n        ui_response_time = (time.time() - ui_start) * 1000\n        \n        # Check memory usage\n        memory_metrics = await app_page.evaluate('performance.memory')\n        memory_usage = memory_metrics['usedJSHeapSize'] / 1024 / 1024\n        \n        # Stop detection\n        await app_page.click('[data-testid=\"stop-detection-btn\"]')\n        \n        # Calculate performance ratios vs baseline\n        actual_metrics = {\n            'connection_time_ms': connection_time,\n            'audio_processing_ms': processing_time, \n            'ui_response_ms': ui_response_time,\n            'memory_usage_mb': memory_usage\n        }\n        \n        print(f\"📊 Performance Regression Analysis:\")\n        \n        regression_detected = False\n        for metric, baseline in baseline_metrics.items():\n            actual = actual_metrics[metric]\n            ratio = actual / baseline\n            status = \"✅\" if ratio <= 1.2 else \"⚠️\" if ratio <= 1.5 else \"❌\"\n            \n            print(f\"   {metric}: {actual:.1f} vs {baseline:.1f} (ratio: {ratio:.2f}) {status}\")\n            \n            if ratio > 1.5:  # 50% regression threshold\n                regression_detected = True\n        \n        assert not regression_detected, \"Performance regression detected - metrics exceed 150% of baseline\"\n        \n        print(\"✅ No significant performance regressions detected\")\n\n\nif __name__ == \"__main__\":\n    # Run E2E performance validation\n    pytest.main([__file__, \"-v\", \"--tb=short\"])"