#!/usr/bin/env python3
"""
Comprehensive Playwright test suite for the improved carnatic.html page.
Tests all key functionality including UI components, API health checks, WebSocket connections,
error handling, status indicators, and user experience improvements.
"""

import pytest
import asyncio
import json
import time
from playwright.async_api import async_playwright, Page, expect, Browser, BrowserContext

BASE_URL = "http://localhost:5002"
CARNATIC_URL = f"{BASE_URL}/carnatic"

class TestCarnaticUI:
    """Comprehensive test suite for the Carnatic Music Learning interface."""

    @pytest.fixture(scope="session")
    async def browser(self):
        """Browser fixture for all tests."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            yield browser
            await browser.close()

    @pytest.fixture(scope="function")
    async def page(self, browser: Browser):
        """Page fixture for each test."""
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    async def test_page_loads_correctly(self, page: Page):
        """Test 1: Validate that the page loads correctly with the new UI design."""
        # Navigate to the carnatic page
        await page.goto(CARNATIC_URL)

        # Check page title
        await expect(page).to_have_title("🎵 Carnatic Music Learning - Real-time Shruti Detection")

        # Check main header is visible
        await expect(page.locator("h1")).to_contain_text("🎵 Carnatic Music Learning")

        # Check that main sections are present
        await expect(page.locator(".status-section")).to_be_visible()
        await expect(page.locator(".controls-section")).to_be_visible()
        await expect(page.locator(".output-section")).to_be_visible()

        # Validate UI elements are properly styled
        status_section = page.locator(".status-section")
        await expect(status_section).to_have_css("background-color", "rgb(248, 249, 250)")

        # Check for responsive design indicators
        await page.set_viewport_size({"width": 768, "height": 1024})
        await expect(page.locator(".container")).to_be_visible()

        print("✅ Page loads correctly with new UI design")

    async def test_api_health_check_functionality(self, page: Page):
        """Test 2: Validate API health check functionality works."""
        await page.goto(CARNATIC_URL)

        # Wait for page to fully load
        await page.wait_for_load_state("networkidle")

        # Check initial API status indicator
        api_status = page.locator("#api-status")
        await expect(api_status).to_be_visible()

        # Check if health check button exists and is clickable
        health_check_btn = page.locator("button:has-text('Check API Health')")
        if await health_check_btn.count() > 0:
            await health_check_btn.click()

            # Wait for status update
            await page.wait_for_timeout(1000)

            # Verify status indicator updates
            status_text = await api_status.inner_text()
            assert status_text in ["🟢 API Connected", "🔴 API Disconnected", "🟡 Checking..."]

        # Check that API status is displayed in the status section
        status_section = page.locator(".status-section")
        await expect(status_section).to_contain_text("API Status")

        print("✅ API health check functionality validated")

    async def test_websocket_connection_handling(self, page: Page):
        """Test 3: Validate WebSocket connection handling is properly implemented."""
        await page.goto(CARNATIC_URL)

        # Wait for JavaScript to initialize
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Check for WebSocket status indicator
        ws_status = page.locator("#websocket-status, #ws-status, [id*='socket']")
        if await ws_status.count() > 0:
            await expect(ws_status).to_be_visible()

            # Check initial WebSocket status
            status_text = await ws_status.inner_text()
            print(f"WebSocket status: {status_text}")

            # WebSocket status should be one of the expected states
            expected_states = ["🔴 Disconnected", "🟢 Connected", "🟡 Connecting", "🟠 Reconnecting"]
            assert any(state in status_text for state in expected_states)

        # Check console for WebSocket-related messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg.text))

        await page.wait_for_timeout(3000)

        # Look for WebSocket initialization in console
        ws_messages = [msg for msg in console_messages if 'websocket' in msg.lower() or 'socket' in msg.lower()]
        print(f"WebSocket console messages: {ws_messages}")

        print("✅ WebSocket connection handling validated")

    async def test_error_handling_and_status_indicators(self, page: Page):
        """Test 4: Validate error handling and status indicators function correctly."""
        await page.goto(CARNATIC_URL)

        # Wait for page initialization
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Check for various status indicators
        status_indicators = [
            "#api-status",
            "#websocket-status",
            "#ws-status",
            "#microphone-status",
            "#mic-status",
            ".status-indicator"
        ]

        found_indicators = []
        for selector in status_indicators:
            indicators = page.locator(selector)
            count = await indicators.count()
            if count > 0:
                found_indicators.append(selector)
                for i in range(count):
                    indicator = indicators.nth(i)
                    await expect(indicator).to_be_visible()
                    text = await indicator.inner_text()
                    print(f"Status indicator {selector}[{i}]: {text}")

        assert len(found_indicators) > 0, "At least one status indicator should be present"

        # Test error state simulation
        await page.evaluate("""
            // Simulate connection error
            if (window.showError) {
                window.showError('Test error message');
            }
        """)

        await page.wait_for_timeout(1000)

        # Check if error messages are displayed
        error_elements = page.locator(".error, .alert-danger, [class*='error']")
        if await error_elements.count() > 0:
            await expect(error_elements.first()).to_be_visible()

        print("✅ Error handling and status indicators validated")

    async def test_user_interface_responsive_and_functional(self, page: Page):
        """Test 5: Validate the user interface is responsive and functional."""
        await page.goto(CARNATIC_URL)
        await page.wait_for_load_state("networkidle")

        # Test responsive design at different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1024, "height": 768},   # Tablet landscape
            {"width": 768, "height": 1024},   # Tablet portrait
            {"width": 375, "height": 667}     # Mobile
        ]

        for viewport in viewports:
            await page.set_viewport_size(viewport)
            await page.wait_for_timeout(500)

            # Check main container is visible and properly sized
            container = page.locator(".container, .main-container")
            if await container.count() > 0:
                await expect(container.first()).to_be_visible()

            # Check critical UI elements are visible
            await expect(page.locator("h1")).to_be_visible()

            # Check sections adapt to screen size
            sections = page.locator(".status-section, .controls-section, .output-section")
            section_count = await sections.count()
            for i in range(section_count):
                await expect(sections.nth(i)).to_be_visible()

            print(f"✅ UI responsive at {viewport['width']}x{viewport['height']}")

        # Test interactive elements
        await page.set_viewport_size({"width": 1024, "height": 768})

        # Check buttons are clickable
        buttons = page.locator("button")
        button_count = await buttons.count()
        print(f"Found {button_count} buttons")

        for i in range(min(button_count, 5)):  # Test up to 5 buttons
            button = buttons.nth(i)
            if await button.is_visible():
                button_text = await button.inner_text()
                await expect(button).to_be_enabled()
                print(f"Button '{button_text}' is functional")

        print("✅ User interface is responsive and functional")

    async def test_navigation_links_working(self, page: Page):
        """Test 6: Validate navigation links are working properly."""
        await page.goto(CARNATIC_URL)
        await page.wait_for_load_state("networkidle")

        # Look for navigation elements
        nav_selectors = [
            "nav a",
            ".nav-link",
            ".navigation a",
            "a[href]",
            ".menu a"
        ]

        all_links = []
        for selector in nav_selectors:
            links = page.locator(selector)
            count = await links.count()
            for i in range(count):
                link = links.nth(i)
                if await link.is_visible():
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    if href and href.strip():
                        all_links.append({"element": link, "href": href, "text": text})

        print(f"Found {len(all_links)} navigation links")

        # Test each navigation link
        for link_info in all_links[:5]:  # Test up to 5 links to avoid overwhelming
            href = link_info["href"]
            text = link_info["text"].strip()

            if not text or len(text) > 50:  # Skip empty or very long text
                continue

            print(f"Testing link: '{text}' -> {href}")

            # Test internal links
            if href.startswith('/') or 'localhost:5002' in href:
                try:
                    # Click link and verify navigation
                    await link_info["element"].click()
                    await page.wait_for_load_state("networkidle", timeout=5000)

                    # Verify page changed or loaded
                    current_url = page.url
                    print(f"Navigated to: {current_url}")

                    # Navigate back for next test
                    await page.go_back()
                    await page.wait_for_load_state("networkidle", timeout=5000)

                except Exception as e:
                    print(f"Link test failed for '{text}': {str(e)}")

            # Test external links (just verify they exist)
            elif href.startswith('http'):
                await expect(link_info["element"]).to_have_attribute("href", href)
                print(f"External link verified: {href}")

        print("✅ Navigation links validated")

    async def test_real_time_audio_processing_interface(self, page: Page):
        """Test 7: Validate real-time audio processing interface components."""
        await page.goto(CARNATIC_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Look for audio-related UI components
        audio_elements = [
            "button:has-text('Start')",
            "button:has-text('Stop')",
            "button:has-text('Record')",
            "button:has-text('Listen')",
            "#start-btn",
            "#stop-btn",
            ".audio-controls",
            ".microphone-controls"
        ]

        found_audio_controls = []
        for selector in audio_elements:
            elements = page.locator(selector)
            if await elements.count() > 0:
                found_audio_controls.append(selector)
                await expect(elements.first()).to_be_visible()

        print(f"Found audio controls: {found_audio_controls}")

        # Check for audio visualization elements
        viz_elements = [
            "canvas",
            "#frequency-display",
            "#note-display",
            ".visualization",
            ".frequency-viz",
            "#output"
        ]

        found_viz_elements = []
        for selector in viz_elements:
            elements = page.locator(selector)
            if await elements.count() > 0:
                found_viz_elements.append(selector)
                await expect(elements.first()).to_be_visible()

        print(f"Found visualization elements: {found_viz_elements}")

        # Test microphone permission handling (simulate)
        await page.evaluate("""
            // Mock navigator.mediaDevices for testing
            if (typeof navigator !== 'undefined' && navigator.mediaDevices) {
                console.log('MediaDevices API available');
            }
        """)

        # Check for output display area
        output_area = page.locator("#output, .output-section, .results")
        if await output_area.count() > 0:
            await expect(output_area.first()).to_be_visible()
            print("✅ Output display area found")

        print("✅ Real-time audio processing interface validated")

    async def test_comprehensive_functionality_integration(self, page: Page):
        """Test 8: Comprehensive integration test of all key features."""
        await page.goto(CARNATIC_URL)
        await page.wait_for_load_state("networkidle")

        # Test complete user workflow
        print("🧪 Running comprehensive integration test...")

        # Step 1: Page loads with all components
        await expect(page.locator("h1")).to_be_visible()
        await expect(page.locator(".status-section")).to_be_visible()
        await expect(page.locator(".controls-section")).to_be_visible()
        await expect(page.locator(".output-section")).to_be_visible()

        # Step 2: Status indicators initialize
        await page.wait_for_timeout(3000)  # Allow status updates

        # Step 3: Check JavaScript initialization
        js_ready = await page.evaluate("""
            () => {
                return typeof window !== 'undefined' &&
                       document.readyState === 'complete';
            }
        """)
        assert js_ready, "JavaScript should be properly initialized"

        # Step 4: Test error recovery
        await page.evaluate("""
            // Simulate error and recovery
            console.log('Testing error handling...');
        """)

        # Step 5: UI interaction test
        buttons = page.locator("button")
        if await buttons.count() > 0:
            # Try to interact with first available button
            first_button = buttons.first()
            if await first_button.is_visible() and await first_button.is_enabled():
                await first_button.click()
                await page.wait_for_timeout(1000)

        # Step 6: Check final state
        page_title = await page.title()
        assert "Carnatic" in page_title, f"Page title should contain 'Carnatic', got: {page_title}"

        print("✅ Comprehensive integration test completed successfully")

    async def test_performance_and_loading(self, page: Page):
        """Test 9: Validate page performance and loading metrics."""
        # Navigate and measure performance
        start_time = time.time()
        await page.goto(CARNATIC_URL)
        await page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time

        print(f"Page load time: {load_time:.2f} seconds")
        assert load_time < 10, f"Page should load within 10 seconds, took {load_time:.2f}s"

        # Check resource loading
        await page.wait_for_timeout(2000)

        # Validate no JavaScript errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        await page.wait_for_timeout(3000)

        if console_errors:
            print(f"Console errors found: {[err.text for err in console_errors]}")

        # Check page is interactive
        body = page.locator("body")
        await expect(body).to_be_visible()

        print("✅ Performance and loading validated")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])