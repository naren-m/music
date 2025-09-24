"""
Audio API Routes
Handles audio processing, synthesis, and real-time detection
"""

from flask import Blueprint, request, jsonify
import numpy as np
import base64
import json
from io import BytesIO

from core.services.audio_engine import CarnaticAudioEngine, AudioConfig
from core.models.shruti import ShrutiSystem

audio_bp = Blueprint('audio', __name__)

# Initialize detection engines
audio_config = AudioConfig()
carnatic_engine = CarnaticAudioEngine(audio_config)


@audio_bp.route('/config', methods=['GET'])
def get_audio_config():
    """Get audio configuration"""
    return {
        'sample_rate': audio_config.sample_rate,
        'buffer_size': audio_config.buffer_size,
        'fft_size': audio_config.fft_size,
        'supported_formats': ['wav', 'mp3', 'flac'],
        'frequency_range': audio_config.frequency_range,
        'confidence_threshold': audio_config.confidence_threshold
    }


@audio_bp.route('/detect', methods=['POST'])
def detect_pitch():
    """Detect pitch from audio data"""
    try:
        data = request.get_json()
        
        # Get audio data (base64 encoded)
        audio_b64 = data.get('audio_data')
        if not audio_b64:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Detect pitch using Carnatic engine
        result = carnatic_engine.detect_shruti(audio_array)
        
        if result and result.confidence > audio_config.confidence_threshold:
            return jsonify({
                'detected': True,
                'shruti': {
                    'name': result.detected_shruti.name,
                    'western_equiv': result.detected_shruti.western_equiv,
                    'frequency': result.fundamental_frequency,
                    'confidence': result.confidence,
                    'cents_deviation': result.cents_deviation
                },
                'timestamp': result.timestamp
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No pitch detected or confidence too low'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/detect-western', methods=['POST'])
def detect_western_note():
    """Detect Western note from audio data"""
    try:
        data = request.get_json()
        
        # Get audio data (base64 encoded)
        audio_b64 = data.get('audio_data')
        if not audio_b64:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Detect pitch using basic detection
        result = carnatic_engine.detect_pitch(audio_array)
        
        if result and result.confidence > audio_config.confidence_threshold:
            # Convert frequency to Western note
            western_note = frequency_to_note(result.fundamental_frequency)
            
            return jsonify({
                'detected': True,
                'note': western_note,
                'frequency': result.fundamental_frequency,
                'confidence': result.confidence,
                'timestamp': result.timestamp
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No pitch detected or confidence too low'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def frequency_to_note(frequency):
    """Convert frequency to Western note name"""
    if frequency <= 0:
        return None
    
    # A4 = 440 Hz reference
    A4 = 440.0
    C0 = A4 * np.power(2, -4.75)
    
    # Calculate semitones from C0
    semitones = 12 * np.log2(frequency / C0)
    note_number = int(round(semitones))
    
    # Note names
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_number // 12
    note_index = note_number % 12
    
    return f"{note_names[note_index]}{octave}"