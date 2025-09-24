"""
End-to-End Tests with Playwright
Comprehensive testing of user workflows and browser interactions
"""

import pytest
import asyncio
import json
from playwright.async_api import Page, expect
from conftest import wait_for_audio_permission, simulate_microphone_input, measure_page_load_time


@pytest.mark.asyncio
class TestUserAuthentication:
    """Test user authentication flows."""
    
    async def test_user_registration(self, page: Page, test_server_url: str):
        """Test user registration process."""
        await page.goto(f"{test_server_url}/register")
        
        # Fill registration form
        await page.fill('input[name="email"]', 'test@example.com')
        await page.fill('input[name="password"]', 'securepassword123')
        await page.fill('input[name="name"]', 'Test User')
        await page.select_option('select[name="skill_level"]', 'beginner')
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard
        await page.wait_for_url(f"{test_server_url}/dashboard")
        
        # Verify successful registration
        welcome_text = await page.locator('.welcome-message').text_content()
        assert 'Welcome, Test User' in welcome_text
    
    async def test_user_login(self, page: Page, test_server_url: str):
        """Test user login process."""
        await page.goto(f"{test_server_url}/login")
        
        # Fill login form
        await page.fill('input[name="email"]', 'test@example.com')
        await page.fill('input[name="password"]', 'securepassword123')
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for redirect
        await page.wait_for_url(f"{test_server_url}/dashboard")
        
        # Verify login success
        dashboard_heading = await page.locator('h1').text_content()
        assert 'Dashboard' in dashboard_heading
    
    async def test_logout(self, page: Page, test_server_url: str):
        """Test user logout process."""
        # Login first
        await self.test_user_login(page, test_server_url)
        
        # Logout
        await page.click('button[data-testid="logout-button"]')
        
        # Wait for redirect to home
        await page.wait_for_url(f"{test_server_url}/")
        
        # Verify logout
        assert await page.locator('.login-button').is_visible()


@pytest.mark.asyncio
class TestSwaraRecognitionWorkflow:
    """Test complete swara recognition learning workflow."""
    
    async def test_swara_exercise_initialization(self, page: Page, test_server_url: str):
        """Test swara exercise setup."""
        await page.goto(f"{test_server_url}/learning/swara")
        
        # Check page loads
        await page.wait_for_selector('[data-testid="swara-trainer"]')
        
        # Verify exercise options
        assert await page.locator('.exercise-type-selector').is_visible()
        assert await page.locator('.difficulty-selector').is_visible()
        assert await page.locator('.shruti-count-selector').is_visible()
    
    async def test_microphone_permission_flow(self, page: Page, test_server_url: str):
        """Test microphone permission handling."""
        await page.goto(f"{test_server_url}/learning/swara")
        
        # Grant microphone permission
        await wait_for_audio_permission(page)
        
        # Start exercise
        await page.click('[data-testid="start-exercise"]')
        
        # Verify microphone indicator
        await page.wait_for_selector('[data-testid="microphone-active"]')
        assert await page.locator('[data-testid="microphone-active"]').is_visible()
    
    async def test_real_time_pitch_detection(self, page: Page, test_server_url: str):
        """Test real-time pitch detection display."""
        await page.goto(f"{test_server_url}/learning/swara")
        await wait_for_audio_permission(page)
        
        # Simulate microphone input
        await simulate_microphone_input(page, 261.63)  # Sa (C4)
        
        # Start exercise
        await page.click('[data-testid="start-exercise"]')
        
        # Wait for pitch detection
        await page.wait_for_selector('[data-testid="detected-pitch"]', timeout=5000)
        
        # Verify pitch display
        pitch_display = await page.locator('[data-testid="detected-pitch"]').text_content()
        assert 'Sa' in pitch_display or '261' in pitch_display
    
    async def test_shruti_accuracy_feedback(self, page: Page, test_server_url: str):
        """Test shruti accuracy feedback system."""
        await page.goto(f"{test_server_url}/learning/swara")
        await wait_for_audio_permission(page)
        await simulate_microphone_input(page, 261.63)  # Perfect Sa
        
        await page.click('[data-testid="start-exercise"]')
        
        # Wait for accuracy feedback
        await page.wait_for_selector('[data-testid="accuracy-meter"]')
        
        # Verify high accuracy for perfect pitch
        accuracy_meter = page.locator('[data-testid="accuracy-meter"]')
        accuracy_value = await accuracy_meter.get_attribute('data-accuracy')
        assert float(accuracy_value) > 0.9
    
    async def test_exercise_completion_flow(self, page: Page, test_server_url: str):
        """Test complete exercise workflow."""
        await page.goto(f"{test_server_url}/learning/swara")
        await wait_for_audio_permission(page)
        
        # Start exercise
        await page.click('[data-testid="start-exercise"]')
        
        # Simulate singing all 7 swaras
        swaras = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]
        
        for freq in swaras:
            await simulate_microphone_input(page, freq)
            await asyncio.sleep(1)  # Wait for detection
        
        # Complete exercise
        await page.click('[data-testid="complete-exercise"]')
        
        # Verify completion
        await page.wait_for_selector('[data-testid="exercise-results"]')
        results = await page.locator('[data-testid="exercise-results"]').text_content()
        assert 'Exercise Complete' in results
    
    async def test_progress_tracking(self, page: Page, test_server_url: str):
        """Test progress tracking and analytics."""
        await page.goto(f"{test_server_url}/dashboard")
        
        # Check progress indicators
        await page.wait_for_selector('[data-testid="progress-overview"]')
        
        # Verify progress elements
        assert await page.locator('[data-testid="swara-accuracy-chart"]').is_visible()
        assert await page.locator('[data-testid="practice-streak"]').is_visible()
        assert await page.locator('[data-testid="total-practice-time"]').is_visible()


@pytest.mark.asyncio
class TestRagaLearningWorkflow:
    """Test raga learning and recognition features."""
    
    async def test_raga_library_navigation(self, page: Page, test_server_url: str):
        """Test raga library browsing."""
        await page.goto(f"{test_server_url}/learning/ragas")
        
        # Wait for raga list
        await page.wait_for_selector('[data-testid="raga-list"]')
        
        # Verify popular ragas are listed
        raga_names = await page.locator('.raga-card h3').all_text_contents()
        assert 'Bilaval' in raga_names
        assert 'Kalyan' in raga_names
        assert 'Bhairav' in raga_names
    
    async def test_raga_detail_view(self, page: Page, test_server_url: str):
        """Test individual raga detail page."""
        await page.goto(f"{test_server_url}/learning/ragas")
        
        # Click on first raga
        await page.click('.raga-card:first-child')
        
        # Wait for detail view
        await page.wait_for_selector('[data-testid="raga-details"]')
        
        # Verify detail components
        assert await page.locator('[data-testid="raga-scale"]').is_visible()
        assert await page.locator('[data-testid="raga-characteristics"]').is_visible()
        assert await page.locator('[data-testid="play-raga-sample"]').is_visible()
    
    async def test_raga_practice_mode(self, page: Page, test_server_url: str):
        """Test raga practice mode."""
        await page.goto(f"{test_server_url}/learning/ragas/bilaval")
        await wait_for_audio_permission(page)
        
        # Start raga practice
        await page.click('[data-testid="start-raga-practice"]')
        
        # Verify practice interface
        await page.wait_for_selector('[data-testid="raga-practice-interface"]')
        assert await page.locator('[data-testid="tanpura-controls"]').is_visible()
        assert await page.locator('[data-testid="metronome-controls"]').is_visible()


@pytest.mark.asyncio
class TestAudioControls:
    """Test audio control interfaces."""
    
    async def test_tanpura_controls(self, page: Page, test_server_url: str):
        """Test tanpura drone controls."""
        await page.goto(f"{test_server_url}/learning")
        
        # Open tanpura controls
        await page.click('[data-testid="tanpura-toggle"]')
        
        # Test play/pause
        await page.click('[data-testid="tanpura-play"]')
        await page.wait_for_selector('[data-testid="tanpura-playing"]')
        
        # Test volume control
        volume_slider = page.locator('[data-testid="tanpura-volume"]')
        await volume_slider.fill('50')
        
        # Test tuning adjustment
        tuning_selector = page.locator('[data-testid="tanpura-tuning"]')
        await tuning_selector.select_option('kalyan')
    
    async def test_metronome_controls(self, page: Page, test_server_url: str):
        """Test metronome functionality."""
        await page.goto(f"{test_server_url}/learning")
        
        # Open metronome
        await page.click('[data-testid="metronome-toggle"]')
        
        # Test tempo adjustment
        tempo_input = page.locator('[data-testid="metronome-tempo"]')
        await tempo_input.fill('120')
        
        # Test time signature
        time_sig_selector = page.locator('[data-testid="time-signature"]')
        await time_sig_selector.select_option('4/4')
        
        # Start metronome
        await page.click('[data-testid="metronome-start"]')
        await page.wait_for_selector('[data-testid="metronome-active"]')


@pytest.mark.asyncio
class TestResponsiveDesign:
    """Test responsive design and mobile compatibility."""
    
    async def test_mobile_layout(self, page: Page, test_server_url: str):
        """Test mobile responsive layout."""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto(f"{test_server_url}/")
        
        # Check mobile navigation
        hamburger_menu = page.locator('[data-testid="mobile-menu-toggle"]')
        if await hamburger_menu.is_visible():
            await hamburger_menu.click()
            assert await page.locator('[data-testid="mobile-nav"]').is_visible()
    
    async def test_tablet_layout(self, page: Page, test_server_url: str):
        """Test tablet responsive layout."""
        # Set tablet viewport
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.goto(f"{test_server_url}/learning")
        
        # Verify layout adapts properly
        sidebar = page.locator('[data-testid="learning-sidebar"]')
        assert await sidebar.is_visible()
    
    async def test_desktop_layout(self, page: Page, test_server_url: str):
        """Test desktop layout."""
        # Set desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(f"{test_server_url}/dashboard")
        
        # Verify full desktop layout
        assert await page.locator('[data-testid="dashboard-grid"]').is_visible()
        assert await page.locator('[data-testid="sidebar-navigation"]').is_visible()


@pytest.mark.asyncio
class TestPerformanceTesting:
    """Test performance characteristics."""
    
    async def test_page_load_performance(self, page: Page, test_server_url: str):
        """Test page load times."""
        # Test main pages
        pages_to_test = [
            "/",
            "/learning",
            "/learning/swara",
            "/learning/ragas",
            "/dashboard"
        ]
        
        for page_path in pages_to_test:
            load_time = await measure_page_load_time(page, f"{test_server_url}{page_path}")
            assert load_time < 3.0, f"Page {page_path} took {load_time:.2f}s to load"
    
    async def test_audio_latency(self, page: Page, test_server_url: str):
        """Test audio processing latency."""
        await page.goto(f"{test_server_url}/learning/swara")
        await wait_for_audio_permission(page)
        await simulate_microphone_input(page, 440.0)
        
        # Measure time from audio input to display update
        start_time = await page.evaluate("performance.now()")
        await page.click('[data-testid="start-exercise"]')
        await page.wait_for_selector('[data-testid="detected-pitch"]')
        end_time = await page.evaluate("performance.now()")
        
        latency = end_time - start_time
        assert latency < 200, f"Audio latency too high: {latency:.2f}ms"
    
    async def test_memory_usage(self, page: Page, test_server_url: str):
        """Test browser memory usage during extended use."""
        await page.goto(f"{test_server_url}/learning/swara")
        
        # Get initial memory
        initial_memory = await page.evaluate("""
            performance.memory ? performance.memory.usedJSHeapSize : 0
        """)
        
        # Simulate extended usage
        for _ in range(10):
            await page.click('[data-testid="start-exercise"]')
            await asyncio.sleep(1)
            await page.click('[data-testid="stop-exercise"]')
        
        # Check memory after usage
        final_memory = await page.evaluate("""
            performance.memory ? performance.memory.usedJSHeapSize : 0
        """)
        
        if initial_memory > 0 and final_memory > 0:
            memory_increase = final_memory - initial_memory
            # Memory increase should be reasonable (less than 10MB)
            assert memory_increase < 10 * 1024 * 1024


@pytest.mark.asyncio
class TestAccessibility:
    """Test accessibility compliance."""
    
    async def test_keyboard_navigation(self, page: Page, test_server_url: str):
        """Test keyboard navigation accessibility."""
        await page.goto(f"{test_server_url}/learning")
        
        # Test tab navigation
        await page.keyboard.press('Tab')
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element in ['BUTTON', 'A', 'INPUT']
        
        # Test skip links
        await page.keyboard.press('Tab')
        skip_link = page.locator('[data-testid="skip-link"]')
        if await skip_link.is_visible():
            await page.keyboard.press('Enter')
    
    async def test_screen_reader_compatibility(self, page: Page, test_server_url: str):
        """Test screen reader compatibility."""
        await page.goto(f"{test_server_url}/learning/swara")
        
        # Check for ARIA labels
        exercise_button = page.locator('[data-testid="start-exercise"]')
        aria_label = await exercise_button.get_attribute('aria-label')
        assert aria_label is not None and len(aria_label) > 0
        
        # Check for proper heading structure
        headings = await page.locator('h1, h2, h3, h4, h5, h6').all()
        assert len(headings) > 0
    
    async def test_color_contrast(self, page: Page, test_server_url: str):
        """Test color contrast accessibility."""
        await page.goto(f"{test_server_url}/")
        
        # Test high contrast mode simulation
        await page.emulate_media(color_scheme='dark')
        await page.reload()
        
        # Verify page still functions in dark mode
        assert await page.locator('body').is_visible()


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_network_error_handling(self, page: Page, test_server_url: str):
        """Test handling of network errors."""
        await page.goto(f"{test_server_url}/learning")
        
        # Simulate network failure
        await page.route('**/api/**', lambda route: route.abort())
        
        # Try to start exercise
        await page.click('[data-testid="start-exercise"]')
        
        # Verify error message appears
        await page.wait_for_selector('[data-testid="error-message"]')
        error_text = await page.locator('[data-testid="error-message"]').text_content()
        assert 'network' in error_text.lower() or 'connection' in error_text.lower()
    
    async def test_microphone_permission_denied(self, page: Page, test_server_url: str):
        """Test handling when microphone permission is denied."""
        await page.goto(f"{test_server_url}/learning/swara")
        
        # Deny microphone permission
        await page.context.grant_permissions([], origin=test_server_url)
        
        # Try to start exercise
        await page.click('[data-testid="start-exercise"]')
        
        # Verify permission error handling
        await page.wait_for_selector('[data-testid="permission-error"]')
        error_text = await page.locator('[data-testid="permission-error"]').text_content()
        assert 'microphone' in error_text.lower()
    
    async def test_browser_compatibility(self, page: Page, test_server_url: str):
        """Test browser feature detection and fallbacks."""
        await page.goto(f"{test_server_url}/learning")
        
        # Check for feature detection
        web_audio_support = await page.evaluate("""
            !!(window.AudioContext || window.webkitAudioContext)
        """)
        
        if not web_audio_support:
            # Verify fallback message
            await page.wait_for_selector('[data-testid="browser-compatibility-warning"]')
            warning_text = await page.locator('[data-testid="browser-compatibility-warning"]').text_content()
            assert 'browser' in warning_text.lower()