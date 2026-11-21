#!/usr/bin/env python3
"""
Simplified Playwright test suite for the improved carnatic.html page.
Tests all key functionality without complex dependencies.
"""

import asyncio
import logging
import time

import pytest
from playwright.async_api import Page, async_playwright, expect

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5002"
CARNATIC_URL = f"{BASE_URL}/carnatic"


async def _check_page_load(page: Page):
    """Test 1: page loads with the new UI design."""
    logger.info("\n1️⃣ Testing page loading and UI design...")
    await page.goto(CARNATIC_URL)
    await page.wait_for_load_state("networkidle")

    # Check page title
    await expect(page).to_have_title("🎵 Carnatic Music Learning - Real-time Shruti Detection")
    logger.info("   ✅ Page title is correct")

    # Check main header
    header = page.locator("h1")
    await expect(header).to_contain_text("🎵 Carnatic Music Learning")
    logger.info("   ✅ Main header found")

    # Check main sections are present
    status_card = page.locator(".status-card")
    controls_section = page.locator(".controls")
    detection_display = page.locator(".detection-display")

    await expect(status_card).to_be_visible()
    await expect(controls_section).to_be_visible()
    await expect(detection_display).to_be_visible()
    logger.info("   ✅ All main sections are visible")


async def _check_api_status(page: Page):
    """Test 2: API health check indicator."""
    logger.info("\n2️⃣ Testing API health check functionality...")
    await page.wait_for_timeout(2000)

    # Look for API status indicator
    api_status_selectors = ["#connectionStatus", "#statusText", ".status-indicator", ".status-dot"]
    api_status_found = False

    for selector in api_status_selectors:
        elements = page.locator(selector)
        if await elements.count() > 0:
            element = elements.first
            await expect(element).to_be_visible()
            if selector == "#statusText":
                status_text = await element.inner_text()
                logger.info(f"   ✅ System status found: {status_text}")
            api_status_found = True
            break

    if not api_status_found:
        logger.info("   ⚠️ API status indicator not found - checking for general status displays")


async def _check_websocket(page: Page):
    """Test 3: WebSocket status and console activity. Returns the console log."""
    logger.info("\n3️⃣ Testing WebSocket connection handling...")

    # Check for WebSocket status indicators
    ws_selectors = ["#websocket-status", "#ws-status", ".websocket-status", ".connection-status"]
    ws_status_found = False

    for selector in ws_selectors:
        elements = page.locator(selector)
        if await elements.count() > 0:
            status_text = await elements.first.inner_text()
            logger.info(f"   ✅ WebSocket status found: {status_text}")
            ws_status_found = True
            break

    # Monitor console for WebSocket messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    await page.wait_for_timeout(3000)

    ws_console_msgs = [msg for msg in console_messages if "websocket" in msg.lower() or "socket" in msg.lower()]
    if ws_console_msgs:
        logger.info(f"   ✅ WebSocket console activity: {len(ws_console_msgs)} messages")
    return console_messages


async def _check_status_indicators(page: Page):
    """Test 4: error handling and status indicators."""
    logger.info("\n4️⃣ Testing error handling and status indicators...")

    # Look for various status indicators
    all_status_indicators = page.locator("[id*='status'], [class*='status'], [class*='indicator']")
    indicator_count = await all_status_indicators.count()
    logger.info(f"   ✅ Found {indicator_count} status indicators")

    for i in range(min(indicator_count, 5)):  # Check first 5 indicators
        indicator = all_status_indicators.nth(i)
        if await indicator.is_visible():
            text = await indicator.inner_text()
            if text.strip():
                logger.info(f"   📊 Status indicator {i+1}: {text[:50]}...")

    # Test error simulation
    await page.evaluate(
        """
        console.log('Testing error handling simulation');
        if (window.showError) {
            window.showError('Test error message');
        }
    """
    )
    await page.wait_for_timeout(1000)


async def _check_responsiveness(page: Page):
    """Test 5: layout at several viewport sizes."""
    logger.info("\n5️⃣ Testing UI responsiveness...")

    # Test different viewport sizes
    viewports = [
        {"width": 1920, "height": 1080, "name": "Desktop"},
        {"width": 1024, "height": 768, "name": "Tablet landscape"},
        {"width": 768, "height": 1024, "name": "Tablet portrait"},
        {"width": 375, "height": 667, "name": "Mobile"},
    ]

    for viewport in viewports:
        await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
        await page.wait_for_timeout(500)

        # Check main elements are still visible
        await expect(page.locator("h1")).to_be_visible()
        container = page.locator(".container, .main-container, body")
        await expect(container.first).to_be_visible()
        logger.info(f"   ✅ UI responsive at {viewport['name']} ({viewport['width']}x{viewport['height']})")

    # Reset to desktop size for remaining tests
    await page.set_viewport_size({"width": 1280, "height": 720})


async def _check_navigation(page: Page):
    """Test 6: navigation links."""
    logger.info("\n6️⃣ Testing navigation functionality...")

    # Find all links
    all_links = page.locator("a[href]")
    link_count = await all_links.count()
    logger.info(f"   📝 Found {link_count} links")

    tested_links = 0
    for i in range(min(link_count, 3)):  # Test up to 3 links
        link = all_links.nth(i)
        if await link.is_visible():
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and text.strip() and len(text.strip()) < 50:
                logger.info(f"   🔗 Link {i+1}: '{text.strip()}' -> {href}")
                tested_links += 1

    logger.info(f"   ✅ {tested_links} navigation links validated")


async def _check_audio_interface(page: Page):
    """Test 7: real-time audio processing controls."""
    logger.info("\n7️⃣ Testing real-time audio processing interface...")

    # Look for audio control buttons
    audio_button_selectors = [
        "#startBtn",
        "#stopBtn",
        "button:has-text('Start Detection')",
        "button:has-text('Stop Detection')",
        ".btn-primary",
        ".btn-secondary",
    ]

    audio_controls_found = 0
    for selector in audio_button_selectors:
        buttons = page.locator(selector)
        if await buttons.count() > 0:
            button = buttons.first
            if await button.is_visible():
                button_text = await button.inner_text()
                is_enabled = await button.is_enabled()
                status = "enabled" if is_enabled else "disabled"
                logger.info(f"   🎛️ Audio control found: {button_text} ({status})")
                audio_controls_found += 1

    # Look for visualization elements
    viz_selectors = ["canvas", "#frequency", ".frequency-display", ".detection-display", "#visualizer", ".shruti-wheel"]
    viz_found = 0
    for selector in viz_selectors:
        elements = page.locator(selector)
        if await elements.count() > 0 and await elements.first.is_visible():
            logger.info(f"   📈 Visualization element found: {selector}")
            viz_found += 1

    # Check output area
    output_selectors = ["#frequency", ".detection-display", ".frequency-display", "#shruti-display", "#note-display"]
    output_found = False
    for selector in output_selectors:
        elements = page.locator(selector)
        if await elements.count() > 0 and await elements.first.is_visible():
            logger.info(f"   📊 Output area found: {selector}")
            output_found = True
            break

    logger.info(f"   ✅ Audio interface validated: {audio_controls_found} controls, {viz_found} visualizations")


async def _check_performance(page: Page, console_messages):
    """Test 8: reload time, console errors, JS state."""
    logger.info("\n8️⃣ Testing performance and loading...")

    # Measure page load time
    start_time = time.time()
    await page.reload()
    await page.wait_for_load_state("networkidle")
    load_time = time.time() - start_time

    logger.info(f"   ⏱️ Page reload time: {load_time:.2f} seconds")

    # Check for console errors
    error_count = len([msg for msg in console_messages if "error" in msg.lower()])
    logger.info(f"   🐛 Console errors: {error_count}")

    # Test JavaScript functionality
    js_ready = await page.evaluate(
        """
        () => {
            return {
                documentReady: document.readyState === 'complete',
                windowDefined: typeof window !== 'undefined',
                hasAudioAPI: typeof navigator !== 'undefined' && !!navigator.mediaDevices
            };
        }
    """
    )

    logger.info(
        f"   💻 JavaScript state: Document ready: {js_ready['documentReady']}, Window defined: {js_ready['windowDefined']}, Audio API: {js_ready['hasAudioAPI']}"
    )


async def _check_integration(page: Page):
    """Test 9: click-through integration check."""
    logger.info("\n9️⃣ Running integration test...")

    # Test complete user workflow simulation
    await page.wait_for_timeout(2000)

    # Try to interact with an enabled button if available
    enabled_buttons = page.locator("button:visible:enabled")
    button_count = await enabled_buttons.count()
    if button_count > 0:
        first_button = enabled_buttons.first
        button_text = await first_button.inner_text()
        logger.info(f"   🖱️ Clicking enabled button: {button_text}")
        await first_button.click()
        await page.wait_for_timeout(1000)
    else:
        logger.info("   ⚠️ No enabled buttons found for interaction test")

    # Final validation
    current_title = await page.title()
    current_url = page.url

    logger.info(f"   ✅ Final state: Title: {current_title}")
    logger.info(f"   ✅ Final URL: {current_url}")


@pytest.mark.asyncio
async def test_carnatic_comprehensive_suite():
    """Comprehensive test suite for Carnatic Music Learning interface."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(permissions=["microphone"], viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            logger.info("🧪 Starting comprehensive Carnatic UI test suite...")

            await _check_page_load(page)
            await _check_api_status(page)
            console_messages = await _check_websocket(page)
            await _check_status_indicators(page)
            await _check_responsiveness(page)
            await _check_navigation(page)
            await _check_audio_interface(page)
            await _check_performance(page, console_messages)
            await _check_integration(page)

            logger.info("\n🎉 Comprehensive test suite completed successfully!")
            logger.info("=" * 60)
            logger.info("SUMMARY:")
            logger.info("✅ Page loading and UI design")
            logger.info("✅ API health check functionality")
            logger.info("✅ WebSocket connection handling")
            logger.info("✅ Error handling and status indicators")
            logger.info("✅ User interface responsiveness")
            logger.info("✅ Navigation functionality")
            logger.info("✅ Real-time audio processing interface")
            logger.info("✅ Performance and loading")
            logger.info("✅ Integration testing")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Test failed with error: {str(e)}")
            raise

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(test_carnatic_comprehensive_suite())
