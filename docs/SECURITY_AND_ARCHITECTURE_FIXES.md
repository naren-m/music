# 🛡️ Security & Architecture Fixes - Implementation Guide

**Project**: Carnatic Music Learning Platform
**Version**: 2.0
**Date**: September 2024
**Priority**: CRITICAL - Production Blocker Issues

---

## 🚨 CRITICAL SECURITY VULNERABILITIES

### 1. SQL Injection Vulnerability

**File**: `migrations/init_db.py:56`
**Risk Level**: 🔴 CRITICAL
**CVSS Score**: 9.8 (Critical)

#### Current Vulnerable Code:
```python
cursor.execute(f"CREATE DATABASE {config.postgresql_db}")
```

#### Issue Description:
Direct string interpolation in SQL execution allows SQL injection attacks. An attacker could manipulate the database name to execute arbitrary SQL commands.

#### Fix Implementation:
```python
# BEFORE (VULNERABLE)
cursor.execute(f"CREATE DATABASE {config.postgresql_db}")

# AFTER (SECURE)
from psycopg2 import sql
cursor.execute(
    sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier(config.postgresql_db)
    )
)

# Additional validation
import re
def validate_db_name(db_name):
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', db_name):
        raise ValueError("Invalid database name format")
    if len(db_name) > 63:  # PostgreSQL limit
        raise ValueError("Database name too long")
    return db_name

# Use in config
validated_db_name = validate_db_name(config.postgresql_db)
```

#### Files to Modify:
1. `migrations/init_db.py` - Lines 50-56
2. `config/database.py` - Add validation function

---

### 2. Authentication Bypass Vulnerability

**File**: `api/auth/routes.py:16-50`
**Risk Level**: 🔴 CRITICAL
**CVSS Score**: 8.9 (High)

#### Current Vulnerable Code:
```python
@auth_bp.route('/guest', methods=['POST'])
def create_guest_session():
    user_id = str(uuid.uuid4())  # No rate limiting
    session['user_id'] = user_id
    session['user_type'] = 'guest'
    return jsonify({'user_id': user_id}), 201
```

#### Issues:
1. No rate limiting - allows session flooding
2. No input validation
3. Sessions never expire
4. No CSRF protection

#### Fix Implementation:

**Step 1: Add Rate Limiting**
```python
# Install: pip install Flask-Limiter redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route('/guest', methods=['POST'])
@limiter.limit("5 per minute")  # Strict rate limit for guest creation
def create_guest_session():
    # Validate request
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    # Optional: Add simple bot detection
    if not data.get('human_verification'):
        return jsonify({'error': 'Human verification required'}), 400

    user_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour expiry

    session['user_id'] = user_id
    session['user_type'] = 'guest'
    session['expires_at'] = expires_at.isoformat()
    session['created_at'] = datetime.utcnow().isoformat()

    return jsonify({
        'user_id': user_id,
        'user_type': 'guest',
        'expires_at': expires_at.isoformat(),
        'session_created': True
    }), 201
```

**Step 2: Add Session Validation Middleware**
```python
# Create new file: api/auth/middleware.py
from functools import wraps
from datetime import datetime
from flask import session, request, jsonify

def require_valid_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        expires_at = session.get('expires_at')

        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        # Check session expiry
        if expires_at:
            expiry_time = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expiry_time:
                session.clear()
                return jsonify({'error': 'Session expired'}), 401

        return f(*args, **kwargs)
    return decorated_function

# Usage in protected routes
@audio_bp.route('/detect', methods=['POST'])
@require_valid_session
def detect_pitch():
    # ... existing code
```

#### Files to Create/Modify:
1. `api/auth/middleware.py` - NEW FILE
2. `api/auth/routes.py` - Modify existing routes
3. `requirements-v2.txt` - Add Flask-Limiter

---

### 3. Hardcoded Secrets Exposure

**Files**: Multiple locations
**Risk Level**: 🔴 CRITICAL
**CVSS Score**: 9.1 (Critical)

#### Current Vulnerable Code:
```python
# config/settings.py:11
SECRET_KEY = os.environ.get('SECRET_KEY') or 'carnatic-learning-dev-key-2024'

# launch_server.py:28
app.config['SECRET_KEY'] = 'carnatic_learning_dev_key'

# config/database.py:34
postgresql_password: str = os.getenv('POSTGRES_PASSWORD', 'carnatic_pass')
```

#### Fix Implementation:

**Step 1: Create Environment Template**
```bash
# Create .env.example file
SECRET_KEY=your-production-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=carnatic_learning
POSTGRES_USER=carnatic_user
POSTGRES_PASSWORD=your-secure-database-password
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
STRIPE_SECRET_KEY=your-stripe-secret-key
```

**Step 2: Secure Configuration Loading**
```python
# config/settings.py - UPDATED
import os
import secrets
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Generate secure secret if not provided
    _secret_key = os.environ.get('SECRET_KEY')
    if not _secret_key:
        if os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError("SECRET_KEY must be set in production")
        _secret_key = secrets.token_urlsafe(32)
        print(f"WARNING: Generated temporary SECRET_KEY: {_secret_key}")

    SECRET_KEY = _secret_key

    # Validate required environment variables in production
    @classmethod
    def validate_production_config(cls):
        required_vars = [
            'SECRET_KEY', 'POSTGRES_PASSWORD', 'POSTGRES_USER',
            'POSTGRES_HOST', 'POSTGRES_DB'
        ]

        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing and os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError(f"Missing required environment variables: {missing}")

# config/database.py - UPDATED
@dataclass
class DatabaseConfig:
    postgresql_user: str = os.getenv('POSTGRES_USER')
    postgresql_password: str = os.getenv('POSTGRES_PASSWORD')

    def __post_init__(self):
        # Remove default fallbacks in production
        if os.getenv('FLASK_ENV') == 'production':
            if not self.postgresql_user or not self.postgresql_password:
                raise ValueError("Database credentials must be provided in production")
```

**Step 3: Update Docker Configuration**
```yaml
# docker-compose.yml - Add environment file
version: '3.8'
services:
  carnatic-app:
    build: .
    env_file:
      - .env  # Load from environment file
    environment:
      - FLASK_ENV=production
    # Remove hardcoded values
```

#### Files to Modify:
1. `.env.example` - NEW FILE
2. `config/settings.py` - Remove all defaults
3. `config/database.py` - Remove password defaults
4. `launch_server.py` - Remove hardcoded secret
5. `docker-compose.yml` - Use env_file
6. `.gitignore` - Add .env

---

### 4. Input Validation Vulnerability

**File**: `api/audio/routes.py:35-72`
**Risk Level**: 🟡 HIGH
**CVSS Score**: 7.5 (High)

#### Current Vulnerable Code:
```python
@audio_bp.route('/detect', methods=['POST'])
def detect_pitch():
    data = request.get_json()
    audio_b64 = data.get('audio_data')  # No validation
    audio_bytes = base64.b64decode(audio_b64)  # Could be huge
    audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
```

#### Fix Implementation:
```python
# Create new file: api/validation.py
import base64
import numpy as np
from flask import request, jsonify
from functools import wraps

# Configuration constants
MAX_AUDIO_SIZE = 1024 * 1024 * 2  # 2MB max
MAX_AUDIO_DURATION = 30  # 30 seconds max
SAMPLE_RATE = 44100

class ValidationError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

def validate_audio_data(audio_b64: str) -> np.ndarray:
    """Validate and decode audio data with security checks"""

    if not audio_b64:
        raise ValidationError("Audio data is required")

    if not isinstance(audio_b64, str):
        raise ValidationError("Audio data must be base64 string")

    # Check base64 string length (approximate size check)
    if len(audio_b64) > MAX_AUDIO_SIZE * 1.5:  # Base64 is ~1.33x larger
        raise ValidationError("Audio data too large")

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        raise ValidationError("Invalid base64 encoding")

    # Check decoded size
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise ValidationError("Audio file too large")

    try:
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
    except Exception:
        raise ValidationError("Invalid audio format")

    # Validate audio duration
    duration = len(audio_array) / SAMPLE_RATE
    if duration > MAX_AUDIO_DURATION:
        raise ValidationError("Audio duration too long")

    if duration < 0.1:  # Minimum 100ms
        raise ValidationError("Audio duration too short")

    # Validate audio values are in reasonable range
    if np.any(np.isnan(audio_array)) or np.any(np.isinf(audio_array)):
        raise ValidationError("Audio contains invalid values")

    if np.max(np.abs(audio_array)) > 10.0:  # Reasonable amplitude limit
        raise ValidationError("Audio amplitude out of range")

    return audio_array

def validate_json_request(f):
    """Decorator to validate JSON requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        try:
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON data'}), 400
        except Exception:
            return jsonify({'error': 'Malformed JSON'}), 400

        return f(*args, **kwargs)
    return decorated_function

# Update api/audio/routes.py
from .validation import validate_audio_data, validate_json_request, ValidationError

@audio_bp.route('/detect', methods=['POST'])
@require_valid_session  # From auth middleware
@validate_json_request
def detect_pitch():
    try:
        data = request.get_json()

        # Validate and decode audio data
        audio_array = validate_audio_data(data.get('audio_data'))

        # Process with validated data
        result = carnatic_engine.detect_shruti(audio_array)

        if result and result.confidence > audio_config.confidence_threshold:
            return jsonify({
                'detected': True,
                'shruti': {
                    'name': result.shruti.name,
                    'western_equiv': result.shruti.western_equiv,
                    'frequency': float(result.detected_frequency),
                    'confidence': float(result.confidence),
                    'cent_deviation': float(result.cent_deviation)
                },
                'timestamp': result.timestamp
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No pitch detected or confidence too low'
            })

    except ValidationError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        # Log the error but don't expose details
        logger.error(f"Audio processing error: {str(e)}")
        return jsonify({'error': 'Audio processing failed'}), 500
```

#### Files to Create/Modify:
1. `api/validation.py` - NEW FILE
2. `api/audio/routes.py` - Add validation
3. `config/settings.py` - Add size limits

---

## ⚡ CRITICAL PERFORMANCE ISSUES

### 5. Memory Leaks in WebSocket Management

**File**: `api/audio/websocket.py:18-44`
**Risk Level**: 🟡 HIGH

#### Current Problem Code:
```python
active_sessions = {}  # Never properly cleaned up
audio_engines = weakref.WeakValueDictionary()  # Not sufficient
executor = ThreadPoolExecutor(max_workers=8)  # Per module, not shared
```

#### Fix Implementation:
```python
# Create new file: core/managers/session_manager.py
import time
import threading
import weakref
from typing import Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from core.services.audio_engine import CarnaticAudioEngine, AudioConfig

@dataclass
class SessionData:
    user_id: Optional[str]
    connected_at: float
    last_activity: float
    audio_engine: CarnaticAudioEngine
    performance_stats: Dict

    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        return time.time() - self.last_activity > timeout_seconds

class SessionManager:
    """Thread-safe session management with automatic cleanup"""

    def __init__(self, cleanup_interval: int = 300):  # 5 minutes
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._shared_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="audio-proc")
        self._cleanup_thread = None
        self._shutdown = threading.Event()
        self._start_cleanup_daemon()

    def create_session(self, session_id: str, user_id: Optional[str] = None) -> SessionData:
        with self._lock:
            if session_id in self._sessions:
                # Update existing session
                session_data = self._sessions[session_id]
                session_data.last_activity = time.time()
                return session_data

            # Create new session
            config = AudioConfig(enable_parallel_processing=True)
            audio_engine = CarnaticAudioEngine(config)

            session_data = SessionData(
                user_id=user_id,
                connected_at=time.time(),
                last_activity=time.time(),
                audio_engine=audio_engine,
                performance_stats={'processed_chunks': 0, 'avg_latency': 0}
            )

            self._sessions[session_id] = session_data
            return session_data

    def get_session(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_activity = time.time()
            return session

    def remove_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _start_cleanup_daemon(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while not self._shutdown.wait(self._cleanup_interval):
                self._cleanup_expired_sessions()

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self._lock:
            expired_sessions = [
                sid for sid, session in self._sessions.items()
                if session.is_expired()
            ]

            for sid in expired_sessions:
                del self._sessions[sid]

            if expired_sessions:
                print(f"Cleaned up {len(expired_sessions)} expired sessions")

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                'active_sessions': len(self._sessions),
                'total_memory_mb': sum(
                    session.performance_stats.get('memory_usage', 0)
                    for session in self._sessions.values()
                ),
                'thread_pool_size': self._shared_executor._max_workers,
                'pending_tasks': len(self._shared_executor._threads)
            }

    def shutdown(self):
        """Clean shutdown of session manager"""
        self._shutdown.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        self._shared_executor.shutdown(wait=True)
        with self._lock:
            self._sessions.clear()

# Global instance
session_manager = SessionManager()

# Update api/audio/websocket.py
from core.managers.session_manager import session_manager

def register_audio_events(socketio):
    @socketio.on('connect')
    def handle_connect(auth):
        session_id = request.sid
        user_id = auth.get('user_id') if auth else None

        # Create managed session
        session_data = session_manager.create_session(session_id, user_id)

        # Join rooms
        join_room('audio_detection')
        if user_id:
            join_room(f'user_{user_id}')

        emit('connected', {
            'message': 'Connected to Carnatic Learning Server',
            'session_id': session_id,
            'performance_mode': 'optimized'
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        session_id = request.sid
        session_manager.remove_session(session_id)
        leave_room('audio_detection')

    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        session_id = request.sid
        session_data = session_manager.get_session(session_id)

        if not session_data:
            emit('error', {'message': 'Session not found'})
            return

        try:
            # Process with managed session
            audio_data = np.array(data.get('audio_data', []), dtype=np.float32)
            result = session_data.audio_engine.detect_shruti(audio_data)

            if result:
                emit('shruti_detected', {
                    'shruti_name': result.shruti.name if result.shruti else None,
                    'frequency': round(result.detected_frequency, 2),
                    'cent_deviation': round(result.cent_deviation, 1),
                    'confidence': round(result.confidence, 3),
                    'timestamp': result.timestamp
                })

        except Exception as e:
            emit('processing_error', {'message': 'Audio processing failed'})
```

#### Files to Create/Modify:
1. `core/managers/session_manager.py` - NEW FILE
2. `api/audio/websocket.py` - Complete rewrite using manager
3. `core/services/audio_engine.py` - Add memory monitoring

---

### 6. Thread Pool Inefficiency

**File**: `core/services/audio_engine.py:72-108`
**Risk Level**: 🟡 HIGH

#### Current Problem:
```python
class AdvancedPitchDetector:
    def __init__(self, config: AudioConfig):
        # Creates executor per instance - resource waste
        self._executor = ThreadPoolExecutor(max_workers=config.max_worker_threads)
```

#### Fix Implementation:
```python
# Create new file: core/managers/thread_manager.py
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

class ThreadPoolManager:
    """Singleton thread pool manager for efficient resource usage"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._audio_pool = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="audio-processing"
        )
        self._general_pool = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="general-tasks"
        )
        self._initialized = True

    def get_audio_executor(self) -> ThreadPoolExecutor:
        return self._audio_pool

    def get_general_executor(self) -> ThreadPoolExecutor:
        return self._general_pool

    def shutdown(self):
        self._audio_pool.shutdown(wait=True)
        self._general_pool.shutdown(wait=True)

# Global instance
thread_manager = ThreadPoolManager()

# Update core/services/audio_engine.py
from core.managers.thread_manager import thread_manager

class AdvancedPitchDetector:
    def __init__(self, config: AudioConfig):
        self.config = config
        # Remove: self._executor = ThreadPoolExecutor(...)
        # Use shared pool instead
        self._executor = thread_manager.get_audio_executor()

        # Rest of initialization remains same
        self._autocorr_threshold = 0.3
        self._harmonic_threshold = 0.1
        # ... existing code

    def detect_pitch(self, audio_data: np.ndarray) -> Optional[PitchDetectionResult]:
        """Detect pitch using shared thread pool"""
        if len(audio_data) < self.config.buffer_size:
            return None

        windowed = audio_data * np.hanning(len(audio_data))

        if self.config.enable_parallel_processing:
            # Use shared executor with timeout
            futures = []
            futures.append(self._executor.submit(self._autocorrelation_pitch, windowed))
            futures.append(self._executor.submit(self._harmonic_product_spectrum, windowed))
            futures.append(self._executor.submit(self._cepstrum_pitch, windowed))

            # Collect with timeout for real-time processing
            try:
                results = [f.result(timeout=0.05) for f in futures]
                freq_autocorr, freq_harmonic, freq_cepstrum = results
            except TimeoutError:
                # Cancel pending futures and fallback to sequential
                for future in futures:
                    future.cancel()
                return self._sequential_detection(windowed)
        else:
            freq_autocorr = self._autocorrelation_pitch(windowed)
            freq_harmonic = self._harmonic_product_spectrum(windowed)
            freq_cepstrum = self._cepstrum_pitch(windowed)

        # ... rest of method unchanged

    def _sequential_detection(self, windowed_data: np.ndarray) -> Optional[PitchDetectionResult]:
        """Fallback sequential processing"""
        freq_autocorr = self._autocorrelation_pitch(windowed_data)
        freq_harmonic = self._harmonic_product_spectrum(windowed_data)
        freq_cepstrum = self._cepstrum_pitch(windowed_data)

        fundamental = self._combine_pitch_estimates([
            freq_autocorr, freq_harmonic, freq_cepstrum
        ])

        if fundamental is None:
            return None

        # Calculate features and return result
        # ... (same as in main detect_pitch method)
```

#### Files to Create/Modify:
1. `core/managers/thread_manager.py` - NEW FILE
2. `core/services/audio_engine.py` - Use shared pools
3. `api/audio/websocket.py` - Remove individual executors

---

## 🏗️ ARCHITECTURE IMPROVEMENTS

### 7. Centralized Error Handling

**Current Issue**: Inconsistent error handling across the application

#### Implementation:
```python
# Create new file: api/error_handlers.py
import logging
from flask import jsonify, current_app
from werkzeug.http import HTTP_STATUS_CODES

logger = logging.getLogger(__name__)

class APIException(Exception):
    """Base API exception with consistent error response format"""

    def __init__(self, message: str, status_code: int = 500, payload: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

class ValidationError(APIException):
    def __init__(self, message: str, field: str = None):
        super().__init__(message, 400)
        if field:
            self.payload['field'] = field

class AuthenticationError(APIException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, 401)

class AuthorizationError(APIException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403)

class ResourceNotFoundError(APIException):
    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, 404)

class RateLimitError(APIException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429)

def register_error_handlers(app):
    """Register centralized error handlers"""

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = {
            'error': {
                'message': error.message,
                'type': error.__class__.__name__,
                'status_code': error.status_code
            }
        }
        response['error'].update(error.payload)

        # Log error details for debugging
        logger.error(f"API Error: {error.__class__.__name__}: {error.message}")

        return jsonify(response), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({
            'error': {
                'message': 'Bad request',
                'type': 'ValidationError',
                'status_code': 400
            }
        }), 400

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}")

        error_response = {
            'error': {
                'message': 'Internal server error',
                'type': 'InternalError',
                'status_code': 500
            }
        }

        # Include error details in development
        if current_app.debug:
            error_response['error']['details'] = str(error)

        return jsonify(error_response), 500

# Update all route files to use consistent error handling
# Example: api/audio/routes.py
from api.error_handlers import ValidationError, APIException

@audio_bp.route('/detect', methods=['POST'])
@require_valid_session
@validate_json_request
def detect_pitch():
    try:
        data = request.get_json()
        audio_array = validate_audio_data(data.get('audio_data'))

        result = carnatic_engine.detect_shruti(audio_array)

        if not result:
            raise ValidationError("No pitch detected", "audio_data")

        if result.confidence < audio_config.confidence_threshold:
            raise ValidationError("Confidence too low", "audio_data")

        return jsonify({
            'detected': True,
            'shruti': {
                'name': result.shruti.name,
                'western_equiv': result.shruti.western_equiv,
                'frequency': float(result.detected_frequency),
                'confidence': float(result.confidence),
                'cent_deviation': float(result.cent_deviation)
            },
            'timestamp': result.timestamp
        })

    except ValidationError:
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Unexpected error in pitch detection: {str(e)}")
        raise APIException("Audio processing failed")
```

#### Files to Create/Modify:
1. `api/error_handlers.py` - NEW FILE
2. `api/__init__.py` - Register error handlers
3. All route files - Use consistent exceptions

---

## 🔧 DEPLOYMENT & INFRASTRUCTURE

### 8. Environment Configuration Security

#### Create Secure Deployment Scripts:
```bash
#!/bin/bash
# deploy/setup_production.sh

set -e

echo "Setting up Carnatic Music Platform production environment..."

# Check required environment variables
required_vars=(
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "POSTGRES_USER"
    "POSTGRES_HOST"
    "POSTGRES_DB"
    "REDIS_PASSWORD"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "ERROR: $var environment variable is not set"
        exit 1
    fi
done

# Validate secret key strength
if [[ ${#SECRET_KEY} -lt 32 ]]; then
    echo "ERROR: SECRET_KEY must be at least 32 characters long"
    exit 1
fi

# Create secure directories
mkdir -p /app/logs /app/uploads /app/static
chmod 750 /app/logs /app/uploads

# Set secure permissions
find /app -name "*.py" -exec chmod 644 {} \;
find /app -type d -exec chmod 755 {} \;

# Install production dependencies
pip install --no-cache-dir -r requirements-v2.txt

# Run database migrations
python migrations/init_db.py

# Start application
exec python app_v2.py
```

#### Update Docker for Security:
```dockerfile
# Dockerfile - Updated for security
FROM python:3.9-slim

# Create non-root user first
RUN groupadd -r carnatic && useradd -r -g carnatic -m carnatic

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libsndfile1-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements-v2.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-v2.txt

# Copy application code
COPY . .

# Remove sensitive files
RUN rm -f .env .env.example deploy/*.sh

# Set ownership and permissions
RUN chown -R carnatic:carnatic /app && \
    find /app -type f -name "*.py" -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \;

# Switch to non-root user
USER carnatic

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/v1/health || exit 1

# Environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 5001

CMD ["python", "app_v2.py"]
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Critical Security (Week 1)
- [ ] Fix SQL injection in `migrations/init_db.py`
- [ ] Remove all hardcoded secrets from source code
- [ ] Create `.env.example` and update configurations
- [ ] Implement input validation for audio endpoints
- [ ] Add authentication middleware to sensitive routes
- [ ] Create centralized error handling system

### Phase 2: Performance & Architecture (Week 2)
- [ ] Implement session manager for WebSocket connections
- [ ] Create shared thread pool manager
- [ ] Update all services to use managed resources
- [ ] Add memory monitoring and cleanup
- [ ] Implement rate limiting on all endpoints

### Phase 3: Testing & Quality (Week 3-4)
- [ ] Create comprehensive test suite (target 80% coverage)
- [ ] Add security integration tests
- [ ] Implement performance benchmarking
- [ ] Add automated security scanning to CI/CD
- [ ] Create deployment automation scripts

### Phase 4: Production Readiness (Week 4)
- [ ] Complete Docker security hardening
- [ ] Set up monitoring and alerting
- [ ] Create backup and disaster recovery procedures
- [ ] Document API endpoints with OpenAPI/Swagger
- [ ] Perform penetration testing

---

## 🧪 TESTING REQUIREMENTS

### Security Tests Required:
```python
# tests/security/test_sql_injection.py
def test_database_creation_sql_injection():
    """Test that database creation is safe from SQL injection"""
    malicious_db_name = "test'; DROP TABLE users; --"

    with pytest.raises(ValueError):
        validate_db_name(malicious_db_name)

# tests/security/test_auth_bypass.py
def test_guest_session_rate_limiting():
    """Test that guest session creation is rate limited"""
    # Attempt to create many sessions quickly
    for i in range(10):
        response = client.post('/api/v1/auth/guest')
        if i < 5:
            assert response.status_code == 201
        else:
            assert response.status_code == 429

# tests/security/test_input_validation.py
def test_oversized_audio_rejection():
    """Test that oversized audio uploads are rejected"""
    oversized_audio = 'A' * (1024 * 1024 * 5)  # 5MB

    response = client.post('/api/v1/audio/detect', json={
        'audio_data': oversized_audio
    })

    assert response.status_code == 400
    assert 'too large' in response.json['error']
```

---

## 📊 SUCCESS METRICS

### Security Metrics:
- [ ] Zero hardcoded secrets in source code
- [ ] All endpoints require authentication
- [ ] 100% input validation coverage
- [ ] Automated security scan passes

### Performance Metrics:
- [ ] WebSocket memory usage stable under load
- [ ] Audio processing latency < 50ms p95
- [ ] Session cleanup prevents memory leaks
- [ ] Thread pool utilization optimized

### Quality Metrics:
- [ ] 80%+ test coverage achieved
- [ ] Zero critical security vulnerabilities
- [ ] API response time < 200ms p95
- [ ] Error handling consistency 100%

---

## 🆘 SUPPORT & ESCALATION

### Critical Issues:
- **Security vulnerabilities**: Fix immediately, deploy within 24 hours
- **Memory leaks**: Monitor closely, fix within 72 hours
- **Authentication bypass**: Disable affected endpoints until fixed

### Contact Information:
- **Lead Engineer**: [Your contact]
- **Security Team**: [Security contact]
- **DevOps Team**: [DevOps contact]

### Emergency Procedures:
1. Document the issue with steps to reproduce
2. Assess impact and affected users
3. Implement temporary mitigation if possible
4. Deploy fix to staging environment first
5. Validate fix resolves issue
6. Deploy to production with monitoring

---

**Document Version**: 1.0
**Last Updated**: September 2024
**Next Review**: After Phase 1 completion