"""
Audio API Routes
Provides configuration for the client-side audio processing engine.
"""

from flask import Blueprint, jsonify
import logging

from api.rate_limiting import standard_rate_limit

logger = logging.getLogger(__name__)
audio_bp = Blueprint('audio', __name__)

# This is a static configuration for the client.
# In a real-world scenario, this could be loaded from a config file.
CLIENT_AUDIO_CONFIG = {
    'sample_rate': 44100,
    'fft_size': 4096,
    'buffer_size': 4096,
    'confidence_threshold': 0.85,
    'frequency_range': [80, 1200],
    'supported_formats': ['wav', 'mp3'],
}

@audio_bp.route('/config', methods=['GET'])
@standard_rate_limit
def get_audio_config():
    """
    Provides essential configuration to the client-side audio engine.
    This is a critical endpoint for the new architecture, as it allows the server
    to govern the client's behavior without processing audio itself.
    """
    logger.info("Client requested audio configuration.")
    return jsonify(CLIENT_AUDIO_CONFIG)

@audio_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for the audio API."""
    return jsonify({"status": "ok"}), 200