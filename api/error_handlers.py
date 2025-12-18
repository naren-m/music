"""
Centralized Error Handling System
Secure error handling with consistent responses and logging
"""

import logging
import traceback
from datetime import datetime, timezone
from flask import Flask, request, jsonify, current_app
from werkzeug.exceptions import HTTPException

from api.validation import ValidationError
from api.auth.middleware import AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

# Security-focused error messages (prevent information disclosure)
GENERIC_ERROR_MESSAGES = {
    400: "Invalid request format",
    401: "Authentication required",
    403: "Access denied",
    404: "Resource not found",
    413: "Request too large",
    429: "Too many requests",
    500: "Internal server error",
    503: "Service temporarily unavailable"
}


class SecurityError(Exception):
    """Raised when security validation fails"""
    def __init__(self, message: str, status_code: int = 403, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'SECURITY_ERROR'
        super().__init__(message)


class AudioProcessingError(Exception):
    """Raised when audio processing fails"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'AUDIO_ERROR'
        super().__init__(message)


def register_error_handlers(app: Flask):
    """Register all error handlers with the Flask app"""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle input validation errors with secure logging"""
        logger.warning(
            f"Validation error: {error.message} | "
            f"Field: {error.field} | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint}"
        )

        response = {
            'error': error.message,
            'error_code': 'VALIDATION_ERROR'
        }

        if error.field:
            response['field'] = error.field

        return jsonify(response), error.status_code

    @app.errorhandler(AuthenticationError)
    def handle_auth_error(error):
        """Handle authentication errors with security logging"""
        logger.warning(
            f"Authentication error: {error.message} | "
            f"IP: {request.remote_addr} | "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')} | "
            f"Endpoint: {request.endpoint}"
        )

        return jsonify({
            'error': error.message,
            'error_code': 'AUTH_ERROR'
        }), error.status_code

    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error):
        """Handle rate limiting with security monitoring"""
        logger.warning(
            f"Rate limit exceeded: {error.message} | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint}"
        )

        return jsonify({
            'error': error.message,
            'error_code': 'RATE_LIMIT_ERROR',
            'retry_after': 60
        }), error.status_code

    @app.errorhandler(SecurityError)
    def handle_security_error(error):
        """Handle security violations with immediate alerting"""
        logger.error(
            f"SECURITY VIOLATION: {error.message} | "
            f"IP: {request.remote_addr} | "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')} | "
            f"Endpoint: {request.endpoint} | "
            f"Session: {request.cookies.get('session', 'None')}"
        )

        # In production, trigger security alerts here
        if current_app.config.get('FLASK_ENV') == 'production':
            # TODO: Integrate with security monitoring system
            pass

        return jsonify({
            'error': 'Security policy violation',
            'error_code': error.error_code
        }), error.status_code

    @app.errorhandler(AudioProcessingError)
    def handle_audio_error(error):
        """Handle audio processing errors safely"""
        logger.error(
            f"Audio processing error: {error.message} | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint}"
        )

        return jsonify({
            'error': error.message,
            'error_code': error.error_code,
            'message': 'Please try again with different audio data'
        }), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions with secure error messages"""
        # Log the actual error details
        logger.info(
            f"HTTP {error.code}: {error.description} | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint} | "
            f"Method: {request.method}"
        )

        # Return generic message to prevent information disclosure
        generic_message = GENERIC_ERROR_MESSAGES.get(
            error.code,
            "An error occurred"
        )

        return jsonify({
            'error': generic_message,
            'error_code': f'HTTP_{error.code}'
        }), error.code

    @app.errorhandler(413)
    def handle_request_too_large(error):
        """Handle request size limits with detailed logging"""
        logger.warning(
            f"Request too large: {request.content_length} bytes | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint}"
        )

        return jsonify({
            'error': 'Request too large',
            'error_code': 'REQUEST_TOO_LARGE',
            'max_size': '2MB'
        }), 413

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors with secure logging"""
        error_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')

        # Log full error details for debugging
        logger.error(
            f"Unexpected error [{error_id}]: {str(error)} | "
            f"Type: {type(error).__name__} | "
            f"IP: {request.remote_addr} | "
            f"Endpoint: {request.endpoint} | "
            f"Method: {request.method} | "
            f"Traceback: {traceback.format_exc()}"
        )

        # Return generic error to prevent information disclosure
        response = {
            'error': 'Internal server error',
            'error_code': 'UNEXPECTED_ERROR'
        }

        # Include error ID in development for debugging
        if current_app.config.get('FLASK_ENV') != 'production':
            response['error_id'] = error_id
            response['debug_info'] = str(error)

        return jsonify(response), 500

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors with path logging"""
        logger.info(
            f"404 Not Found: {request.url} | "
            f"IP: {request.remote_addr} | "
            f"Method: {request.method} | "
            f"Referrer: {request.headers.get('Referer', 'None')}"
        )

        return jsonify({
            'error': 'Resource not found',
            'error_code': 'NOT_FOUND'
        }), 404

    @app.before_request
    def log_request_info():
        """Log request information for security monitoring"""
        if current_app.config.get('LOG_REQUESTS', True):
            logger.debug(
                f"Request: {request.method} {request.path} | "
                f"IP: {request.remote_addr} | "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')} | "
                f"Content-Length: {request.content_length}"
            )

    @app.after_request
    def log_response_info(response):
        """Log response information for monitoring"""
        if current_app.config.get('LOG_RESPONSES', False):
            logger.debug(
                f"Response: {response.status_code} | "
                f"Content-Length: {response.content_length} | "
                f"Path: {request.path}"
            )
        return response


def create_error_response(
    message: str,
    status_code: int = 400,
    error_code: str = None,
    details: dict = None
):
    """
    Create standardized error response

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details (development only)

    Returns:
        Flask response tuple
    """
    response = {
        'error': message,
        'error_code': error_code or f'HTTP_{status_code}'
    }

    # Add details in development only
    if details and current_app.config.get('FLASK_ENV') != 'production':
        response['details'] = details

    return jsonify(response), status_code


def log_security_event(event_type: str, details: dict):
    """
    Log security events for monitoring and alerting

    Args:
        event_type: Type of security event
        details: Event details
    """
    logger.error(
        f"SECURITY EVENT: {event_type} | "
        f"IP: {request.remote_addr} | "
        f"Details: {details} | "
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
    )

    # In production, this would integrate with SIEM/monitoring
    if current_app.config.get('FLASK_ENV') == 'production':
        # TODO: Send to security monitoring system
        pass


def validate_request_security():
    """
    Perform basic security validation on all requests

    Raises:
        SecurityError: If security violation is detected
    """
    # Check for suspicious headers
    suspicious_headers = [
        'X-Forwarded-Host', 'X-Host', 'X-Original-Host'
    ]

    for header in suspicious_headers:
        if header in request.headers:
            log_security_event('SUSPICIOUS_HEADER', {
                'header': header,
                'value': request.headers[header]
            })

    # Check for path traversal attempts
    if '..' in request.path or '//' in request.path:
        raise SecurityError("Invalid path detected", 400, 'PATH_TRAVERSAL')

    # Check for SQL injection patterns in query parameters
    sql_patterns = ['union', 'select', 'insert', 'delete', 'drop', 'exec']
    for param, value in request.args.items():
        if isinstance(value, str):
            value_lower = value.lower()
            if any(pattern in value_lower for pattern in sql_patterns):
                log_security_event('SQL_INJECTION_ATTEMPT', {
                    'parameter': param,
                    'value': value[:100]  # Truncate for security
                })
                raise SecurityError("Invalid input detected", 400, 'SQL_INJECTION')


# Security middleware function
def security_middleware():
    """Apply security checks to all requests"""
    try:
        validate_request_security()
    except SecurityError:
        # Re-raise to be handled by error handler
        raise
    except Exception as e:
        logger.error(f"Security middleware error: {str(e)}")
        # Don't block requests for middleware errors
        pass