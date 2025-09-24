"""
Test configuration for Carnatic Learning Application
Pytest fixtures and test environment setup
"""

import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, patch
from flask import Flask
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from api import create_app
from core.models.user import UserProfile, SubscriptionTier
from core.models.shruti import SHRUTI_SYSTEM
from core.services.audio_engine import AdvancedPitchDetector


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def flask_app():
    """Create Flask application for testing."""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    return app


@pytest.fixture
def client(flask_app):
    """Create Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def app_context(flask_app):
    """Create Flask application context."""
    with flask_app.app_context():
        yield flask_app


@pytest.fixture(scope="session")
async def playwright():
    """Create Playwright instance."""
    async with async_playwright() as p:
        yield p


@pytest.fixture(scope="session")
async def browser(playwright: Playwright):
    """Create browser instance."""
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    yield browser
    await browser.close()


@pytest.fixture
async def context(browser: Browser):
    """Create browser context with permissions."""
    context = await browser.new_context(
        permissions=['microphone'],
        viewport={'width': 1280, 'height': 720}
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext):
    """Create page instance."""
    page = await context.new_page()
    yield page


@pytest.fixture
def sample_user():
    """Create sample user profile for testing."""
    return UserProfile(
        user_id="test_user_123",
        email="test@example.com",
        name="Test User",
        subscription_tier=SubscriptionTier.PREMIUM,
        learning_goal="raga_mastery",
        skill_level="intermediate",
        preferred_shruti_count=12
    )


@pytest.fixture
def pitch_detector():
    """Create pitch detector instance for testing."""
    return AdvancedPitchDetector()


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for testing."""
    import numpy as np
    # Generate test audio data (440Hz sine wave for A4)
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440.0  # A4
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return audio_data


@pytest.fixture
def test_server_url():
    """Test server URL."""
    return "http://localhost:5000"


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Cleanup any test files created during tests
    test_files = [
        "test_recording.wav",
        "test_output.json",
        "test_session.dat"
    ]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


class TestAudioMock:
    """Mock audio interface for testing."""
    
    def __init__(self):
        self.is_recording = False
        self.audio_data = None
    
    def start_recording(self):
        self.is_recording = True
    
    def stop_recording(self):
        self.is_recording = False
    
    def get_audio_data(self):
        return self.mock_audio_data()
    
    def mock_audio_data(self):
        import numpy as np
        # Return mock audio data
        return np.random.random(1024).astype(np.float32)


@pytest.fixture
def mock_audio():
    """Mock audio interface."""
    return TestAudioMock()


# Playwright helper functions
async def wait_for_audio_permission(page: Page):
    """Wait for audio permission to be granted."""
    await page.evaluate("""
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(() => console.log('Audio permission granted'))
            .catch(() => console.log('Audio permission denied'));
    """)


async def simulate_microphone_input(page: Page, frequency: float = 440.0):
    """Simulate microphone input for testing."""
    await page.evaluate(f"""
        // Mock AudioContext and microphone input
        const mockAudioContext = {{
            createAnalyser: () => ({{
                fftSize: 2048,
                frequencyBinCount: 1024,
                getFloatFrequencyData: (data) => {{
                    // Simulate frequency data for {frequency}Hz
                    const binIndex = Math.floor({frequency} * 1024 / 22050);
                    for (let i = 0; i < data.length; i++) {{
                        data[i] = i === binIndex ? -20 : -100;
                    }}
                }}
            }}),
            createMediaStreamSource: () => ({{
                connect: () => {{}}
            }})
        }};
        
        window.AudioContext = () => mockAudioContext;
        window.webkitAudioContext = () => mockAudioContext;
    """)


# Performance testing helpers
@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests."""
    metrics = {
        'response_times': [],
        'memory_usage': [],
        'cpu_usage': []
    }
    return metrics


async def measure_page_load_time(page: Page, url: str):
    """Measure page load time."""
    start_time = asyncio.get_event_loop().time()
    await page.goto(url)
    await page.wait_for_load_state('networkidle')
    end_time = asyncio.get_event_loop().time()
    return end_time - start_time


# Test data
TEST_FREQUENCIES = {
    'sa': 261.63,   # C4
    'ri': 293.66,   # D4
    'ga': 329.63,   # E4
    'ma': 349.23,   # F4
    'pa': 392.00,   # G4
    'dha': 440.00,  # A4
    'ni': 493.88    # B4
}

TEST_RAGAS = [
    'Bilaval',
    'Kalyan',
    'Khamaj',
    'Bhairav',
    'Bhairavi',
    'Asavari'
]