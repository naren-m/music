"""
Audio API Routes
Handles audio processing, synthesis, and real-time detection
"""

from flask import Blueprint, request, jsonify
import numpy as np
import logging
from typing import Optional

from core.services.audio_engine import CarnaticAudioEngine, AudioConfig
from core.models.shruti import ShrutiSystem
from api.validation import (
    validate_audio_data, validate_json_request, validate_frequency_parameter,
    ValidationError
)
from api.error_handlers import AudioProcessingError, create_error_response
from api.rate_limiting import audio_rate_limit, standard_rate_limit

logger = logging.getLogger(__name__)

audio_bp = Blueprint('audio', __name__)

# Initialize detection engines
audio_config = AudioConfig()
carnatic_engine = CarnaticAudioEngine(audio_config)


@audio_bp.route('/config', methods=['GET'])
@standard_rate_limit
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
@audio_rate_limit
@validate_json_request
def detect_pitch():
    """Detect Carnatic shruti from audio data - Security hardened"""
    try:
        data = request.get_json()

        # Validate and decode audio data with security checks
        audio_array = validate_audio_data(data.get('audio_data'))

        # Process with validated data
        result = carnatic_engine.detect_shruti(audio_array)

        if result and result.confidence > audio_config.confidence_threshold:
            return jsonify({
                'detected': True,
                'shruti': {
                    'name': result.shruti.name,
                    'western_equiv': result.shruti.western_equiv,
                    'frequency': round(float(result.detected_frequency), 2),
                    'confidence': round(float(result.confidence), 3),
                    'cent_deviation': round(float(result.cent_deviation), 1)
                },
                'timestamp': result.timestamp
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No pitch detected or confidence too low',
                'confidence': round(float(result.confidence), 3) if result else 0.0
            })

    except ValidationError as e:
        logger.warning(f"Audio validation failed: {e.message}")
        error_response = {'error': e.message}
        if e.field:
            error_response['field'] = e.field
        return jsonify(error_response), e.status_code

    except Exception as e:
        logger.error(f"Audio processing error: {str(e)}")
        raise AudioProcessingError(
            'Audio processing failed',
            status_code=500,
            error_code='SHRUTI_DETECTION_FAILED'
        )


@audio_bp.route('/detect-western', methods=['POST'])
@audio_rate_limit
@validate_json_request
def detect_western_note():
    """Detect Western note from audio data - Security hardened"""
    try:
        data = request.get_json()

        # Validate and decode audio data with security checks
        audio_array = validate_audio_data(data.get('audio_data'))

        # Detect pitch using basic detection
        result = carnatic_engine.pitch_detector.detect_pitch(audio_array)

        if result and result.confidence > audio_config.confidence_threshold:
            # Convert frequency to Western note
            western_note = frequency_to_note(result.fundamental_frequency)

            return jsonify({
                'detected': True,
                'note': western_note,
                'frequency': round(float(result.fundamental_frequency), 2),
                'confidence': round(float(result.confidence), 3),
                'timestamp': result.timestamp
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No pitch detected or confidence too low',
                'confidence': round(float(result.confidence), 3) if result else 0.0
            })

    except ValidationError as e:
        logger.warning(f"Audio validation failed: {e.message}")
        error_response = {'error': e.message}
        if e.field:
            error_response['field'] = e.field
        return jsonify(error_response), e.status_code

    except Exception as e:
        logger.error(f"Western note detection error: {str(e)}")
        raise AudioProcessingError(
            'Note detection failed',
            status_code=500,
            error_code='WESTERN_NOTE_DETECTION_FAILED'
        )


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