"""
Security Input Validation Middleware
Prevents DoS attacks and validates all input data
"""

import base64
import logging
import os
import re
from functools import wraps
from typing import Any, Dict, Optional

import numpy as np
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Configuration constants
MAX_AUDIO_SIZE = 1024 * 1024 * 2  # 2MB max
MAX_AUDIO_DURATION = 30  # 30 seconds max
SAMPLE_RATE = 44100
MAX_JSON_SIZE = 1024 * 1024  # 1MB max JSON payload


class ValidationError(Exception):
    """Raised when input validation fails"""
    def __init__(self, message: str, status_code: int = 400, field: str = None):
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


def validate_audio_data(audio_b64: str) -> np.ndarray:
    """
    Validate and decode audio data with comprehensive security checks

    Args:
        audio_b64: Base64 encoded audio data

    Returns:
        np.ndarray: Validated audio array

    Raises:
        ValidationError: If validation fails
    """
    if not audio_b64:
        raise ValidationError("Audio data is required", field="audio_data")

    if not isinstance(audio_b64, str):
        raise ValidationError("Audio data must be base64 string", field="audio_data")

    # Check base64 string length (approximate size check)
    estimated_size = len(audio_b64) * 0.75  # Base64 is ~1.33x larger than original
    if estimated_size > MAX_AUDIO_SIZE:
        raise ValidationError(
            f"Audio data too large (max {MAX_AUDIO_SIZE//1024//1024}MB)",
            field="audio_data"
        )

    # Validate base64 format
    try:
        # Check if it's valid base64
        if not audio_b64.replace('+', '').replace('/', '').replace('=', '').isalnum():
            raise ValidationError("Invalid base64 characters", field="audio_data")

        audio_bytes = base64.b64decode(audio_b64, validate=True)
    except Exception as e:
        logger.warning(f"Base64 decode failed: {e}")
        raise ValidationError("Invalid base64 encoding", field="audio_data")

    # Check decoded size
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise ValidationError(
            f"Audio file too large (max {MAX_AUDIO_SIZE//1024//1024}MB)",
            field="audio_data"
        )

    # Minimum size check (at least 100 bytes)
    if len(audio_bytes) < 100:
        raise ValidationError("Audio data too small", field="audio_data")

    # Convert to numpy array
    try:
        # Try different data types
        if len(audio_bytes) % 4 == 0:
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        elif len(audio_bytes) % 2 == 0:
            # Convert from int16 to float32
            int_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_array = int_array.astype(np.float32) / 32768.0
        else:
            raise ValidationError("Invalid audio data format", field="audio_data")

    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}")
        raise ValidationError("Invalid audio format", field="audio_data")

    # Validate audio duration
    duration = len(audio_array) / SAMPLE_RATE
    if duration > MAX_AUDIO_DURATION:
        raise ValidationError(
            f"Audio duration too long (max {MAX_AUDIO_DURATION}s)",
            field="audio_data"
        )

    if duration < 0.1:  # Minimum 100ms
        raise ValidationError("Audio duration too short (min 0.1s)", field="audio_data")

    # Validate audio values are in reasonable range
    if np.any(np.isnan(audio_array)) or np.any(np.isinf(audio_array)):
        raise ValidationError("Audio contains invalid values", field="audio_data")

    # Check amplitude range (should be roughly -1 to 1 for normalized audio)
    max_amplitude = np.max(np.abs(audio_array))
    if max_amplitude > 10.0:  # Allow some headroom but prevent extreme values
        raise ValidationError("Audio amplitude out of range", field="audio_data")

    # Check for silence (all zeros)
    if max_amplitude < 1e-6:
        raise ValidationError("Audio appears to be silent", field="audio_data")

    logger.debug(f"Audio validation passed: {len(audio_array)} samples, {duration:.2f}s")
    return audio_array


def validate_json_request(f):
    """
    Decorator to validate JSON requests with size and format checks
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Content-Type
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400

        # Check content length
        content_length = request.content_length
        if content_length and content_length > MAX_JSON_SIZE:
            return jsonify({
                'error': f'Request too large (max {MAX_JSON_SIZE//1024}KB)'
            }), 413

        # Parse and validate JSON
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON data'}), 400

            # Basic structure validation
            if not isinstance(data, dict):
                return jsonify({'error': 'JSON must be an object'}), 400

        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
            return jsonify({'error': 'Malformed JSON'}), 400

        return f(*args, **kwargs)
    return decorated_function


def validate_frequency_parameter(frequency: Any) -> float:
    """
    Validate frequency parameter for Sa frequency setting

    Args:
        frequency: Input frequency value

    Returns:
        float: Validated frequency

    Raises:
        ValidationError: If validation fails
    """
    if frequency is None:
        raise ValidationError("Frequency is required", field="frequency")

    # Convert to float
    try:
        freq_value = float(frequency)
    except (TypeError, ValueError):
        raise ValidationError("Frequency must be a number", field="frequency")

    # Validate range (reasonable musical frequencies)
    if not (80.0 <= freq_value <= 800.0):
        raise ValidationError(
            "Frequency must be between 80Hz and 800Hz",
            field="frequency"
        )

    return freq_value


def validate_user_input(data: Dict[str, Any], required_fields: list = None) -> Dict[str, Any]:
    """
    Generic validation for user input data

    Args:
        data: Input data dictionary
        required_fields: List of required field names

    Returns:
        Dict[str, Any]: Validated data

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Input must be a JSON object")

    validated = {}
    required_fields = required_fields or []

    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    # Validate each field
    for key, value in data.items():
        # Basic sanitization
        if isinstance(value, str):
            # Limit string length
            if len(value) > 1000:
                raise ValidationError(f"Field '{key}' too long (max 1000 chars)")

            # Basic XSS prevention
            if any(char in value for char in ['<', '>', '"', "'"]):
                logger.warning(f"Potentially unsafe characters in field '{key}': {value}")
                # You might want to sanitize or reject based on your needs

        validated[key] = value

    return validated


def rate_limit_check(key: str, limit: int, window: int = 60) -> bool:
    """
    Simple in-memory rate limiting check.
    In production, use Redis or similar.

    Args:
        key: Unique identifier for rate limiting
        limit: Maximum requests allowed
        window: Time window in seconds

    Returns:
        bool: True if request should be allowed
    """
    # Placeholder implementation - use Redis-based rate limiting in production
    # See api/rate_limiting.py for full implementation
    _ = key, limit, window  # Suppress unused warnings
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal

    Args:
        filename: Input filename

    Returns:
        str: Sanitized filename
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")

    # Get just the filename without path
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\-_.]', '_', filename)

    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename[1:]

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename