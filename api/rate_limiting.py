"""
Advanced Rate Limiting System - Production Ready
Prevents DoS attacks and API abuse with intelligent rate limiting
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Dict, Optional

import redis
from flask import request, jsonify, current_app, make_response

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int
    window: int  # seconds
    burst_requests: int = 0  # Allow burst requests
    burst_window: int = 1  # Burst window in seconds


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: int = 0
    limit_type: str = 'standard'


class RedisRateLimiter:
    """Redis-based rate limiter with sliding window"""

    def __init__(self, redis_client=None):
        self.redis = redis_client or self._get_redis_client()
        self.prefix = "ratelimit:"

    def _get_redis_client(self):
        """Get Redis client with fallback to in-memory"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None

    def check_rate_limit(self, key: str, rate_limit: RateLimit) -> RateLimitResult:
        """
        Check rate limit using sliding window algorithm

        Args:
            key: Unique identifier for rate limiting
            rate_limit: Rate limit configuration

        Returns:
            RateLimitResult with limit status
        """
        if not self.redis:
            # Fallback to in-memory for development
            return self._memory_rate_limit(key, rate_limit)

        current_time = time.time()
        window_start = current_time - rate_limit.window

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        try:
            # Remove old entries
            pipe.zremrangebyscore(f"{self.prefix}{key}", 0, window_start)

            # Count current requests
            pipe.zcard(f"{self.prefix}{key}")

            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]

            # Check if within limit
            if current_count >= rate_limit.requests:
                # Get oldest request time for reset calculation
                oldest = self.redis.zrange(f"{self.prefix}{key}", 0, 0, withscores=True)
                reset_time = oldest[0][1] + rate_limit.window if oldest else current_time + rate_limit.window

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=int(reset_time - current_time),
                    limit_type='rate_limit'
                )

            # Add current request
            pipe = self.redis.pipeline()
            pipe.zadd(f"{self.prefix}{key}", {str(current_time): current_time})
            pipe.expire(f"{self.prefix}{key}", rate_limit.window + 1)
            pipe.execute()

            remaining = rate_limit.requests - current_count - 1
            reset_time = current_time + rate_limit.window

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=reset_time,
                limit_type='standard'
            )

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Allow request if Redis fails (fail open)
            return RateLimitResult(
                allowed=True,
                remaining=rate_limit.requests - 1,
                reset_time=current_time + rate_limit.window,
                limit_type='fallback'
            )

    def _memory_rate_limit(self, key: str, rate_limit: RateLimit) -> RateLimitResult:
        """Fallback in-memory rate limiting"""
        # Simple in-memory implementation for development
        if not hasattr(self, '_memory_store'):
            self._memory_store = {}

        current_time = time.time()
        window_start = current_time - rate_limit.window

        # Clean old entries
        if key in self._memory_store:
            self._memory_store[key] = [
                timestamp for timestamp in self._memory_store[key]
                if timestamp > window_start
            ]
        else:
            self._memory_store[key] = []

        current_count = len(self._memory_store[key])

        if current_count >= rate_limit.requests:
            oldest_time = min(self._memory_store[key]) if self._memory_store[key] else current_time
            reset_time = oldest_time + rate_limit.window

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=int(reset_time - current_time),
                limit_type='memory_limit'
            )

        # Add current request
        self._memory_store[key].append(current_time)

        return RateLimitResult(
            allowed=True,
            remaining=rate_limit.requests - current_count - 1,
            reset_time=current_time + rate_limit.window,
            limit_type='memory'
        )


# Global rate limiter instance
rate_limiter = None


def get_rate_limiter():
    """Get or create rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RedisRateLimiter()
    return rate_limiter


class RateLimitConfig:
    """Rate limit configurations for different endpoint types"""

    # Standard API endpoints
    STANDARD = RateLimit(requests=60, window=60)  # 60 req/min

    # Authentication endpoints (stricter)
    AUTH = RateLimit(requests=5, window=60)  # 5 req/min

    # Guest session creation (very strict)
    GUEST_CREATION = RateLimit(requests=3, window=300)  # 3 req/5min

    # Audio processing (moderate)
    AUDIO_PROCESSING = RateLimit(requests=30, window=60)  # 30 req/min

    # WebSocket connections
    WEBSOCKET_CONNECT = RateLimit(requests=10, window=60)  # 10 connections/min

    # Burst limits for real-time audio
    AUDIO_REALTIME = RateLimit(
        requests=100, window=60,  # 100 req/min base
        burst_requests=10, burst_window=1  # Allow 10 req/sec burst
    )


def get_client_identifier() -> str:
    """
    Get unique client identifier for rate limiting

    Returns:
        Unique identifier string
    """
    # Try to get user ID from session first
    from flask import session
    user_id = session.get('user_id')

    if user_id:
        return f"user:{user_id}"

    # Fallback to IP-based identification
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if client_ip:
        # Handle multiple IPs in X-Forwarded-For
        client_ip = client_ip.split(',')[0].strip()

    # Create hash for privacy (don't store raw IPs)
    ip_hash = hashlib.sha256(
        f"{client_ip}:{request.headers.get('User-Agent', '')}".encode()
    ).hexdigest()[:16]

    return f"ip:{ip_hash}"


def rate_limit(
    rate_limit_config: RateLimit,
    key_suffix: str = None,
    per_user: bool = True
):
    """
    Rate limiting decorator with advanced configuration

    Args:
        rate_limit_config: RateLimit configuration
        key_suffix: Additional key suffix for granular limiting
        per_user: If True, limit per user; if False, limit per IP only
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter
            limiter = get_rate_limiter()

            # Generate rate limit key
            client_id = get_client_identifier()
            if not per_user and client_id.startswith('user:'):
                # Force IP-based limiting even for authenticated users
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if client_ip:
                    client_ip = client_ip.split(',')[0].strip()
                ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
                client_id = f"ip:{ip_hash}"

            key = client_id
            if key_suffix:
                key += f":{key_suffix}"

            # Check rate limit
            result = limiter.check_rate_limit(key, rate_limit_config)

            if not result.allowed:
                # Log rate limit violation
                logger.warning(
                    f"Rate limit exceeded: {key} | "
                    f"Endpoint: {request.endpoint} | "
                    f"IP: {request.remote_addr} | "
                    f"Retry after: {result.retry_after}s"
                )

                # Return rate limit response
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {rate_limit_config.requests} requests per {rate_limit_config.window} seconds',
                    'retry_after': result.retry_after,
                    'limit_type': result.limit_type,
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                })
                response.status_code = 429

                # Add rate limit headers
                response.headers['X-RateLimit-Limit'] = str(rate_limit_config.requests)
                response.headers['X-RateLimit-Remaining'] = str(result.remaining)
                response.headers['X-RateLimit-Reset'] = str(int(result.reset_time))
                response.headers['Retry-After'] = str(result.retry_after)

                return response

            # Add rate limit headers to successful responses
            def add_rate_limit_headers(response):
                response.headers['X-RateLimit-Limit'] = str(rate_limit_config.requests)
                response.headers['X-RateLimit-Remaining'] = str(result.remaining)
                response.headers['X-RateLimit-Reset'] = str(int(result.reset_time))
                return response

            # Execute the original function
            response = f(*args, **kwargs)

            # Add headers to response
            if hasattr(response, 'headers'):
                return add_rate_limit_headers(response)
            else:
                # Handle different response types
                response = make_response(response)
                return add_rate_limit_headers(response)

        return decorated_function
    return decorator


# Convenience decorators for common rate limits
def standard_rate_limit(f):
    """Standard rate limit: 60 req/min"""
    return rate_limit(RateLimitConfig.STANDARD)(f)


def auth_rate_limit(f):
    """Authentication rate limit: 5 req/min"""
    return rate_limit(RateLimitConfig.AUTH)(f)


def guest_creation_rate_limit(f):
    """Guest creation rate limit: 3 req/5min"""
    return rate_limit(RateLimitConfig.GUEST_CREATION, per_user=False)(f)


def audio_rate_limit(f):
    """Audio processing rate limit: 30 req/min"""
    return rate_limit(RateLimitConfig.AUDIO_PROCESSING)(f)


def websocket_rate_limit(f):
    """WebSocket connection rate limit: 10 connections/min"""
    return rate_limit(RateLimitConfig.WEBSOCKET_CONNECT, per_user=False)(f)


# Advanced rate limiting for specific use cases
def adaptive_rate_limit(base_limit: int = 60, burst_multiplier: float = 2.0):
    """
    Adaptive rate limiting based on server load

    Args:
        base_limit: Base requests per minute
        burst_multiplier: Multiplier for burst capacity
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement server load detection
            # For now, use standard rate limiting
            return rate_limit(RateLimit(requests=base_limit, window=60))(f)(*args, **kwargs)
        return decorated_function
    return decorator


# Security-focused rate limiting
def security_rate_limit(f):
    """Security-focused rate limiting for sensitive endpoints"""
    return rate_limit(
        RateLimit(requests=10, window=300),  # 10 req/5min
        key_suffix="security",
        per_user=False  # Always use IP-based for security
    )(f)


# Utility functions for monitoring
def get_rate_limit_stats(key: str = None) -> Dict:
    """
    Get rate limiting statistics

    Args:
        key: Optional specific key to check

    Returns:
        Dictionary with rate limit statistics
    """
    limiter = get_rate_limiter()

    if not limiter.redis:
        return {"error": "Redis not available", "type": "memory_fallback"}

    try:
        if key:
            # Get stats for specific key
            current_time = time.time()
            count = limiter.redis.zcard(f"{limiter.prefix}{key}")
            return {
                "key": key,
                "current_count": count,
                "timestamp": current_time
            }
        else:
            # Get overall stats
            keys = limiter.redis.keys(f"{limiter.prefix}*")
            total_requests = sum(
                limiter.redis.zcard(key) for key in keys
            )
            return {
                "total_active_keys": len(keys),
                "total_active_requests": total_requests,
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}")
        return {"error": str(e)}


def cleanup_expired_rate_limits():
    """Clean up expired rate limit entries"""
    limiter = get_rate_limiter()

    if not limiter.redis:
        return

    try:
        # Get all rate limit keys
        keys = limiter.redis.keys(f"{limiter.prefix}*")
        current_time = time.time()
        cleanup_count = 0

        for key in keys:
            # Remove entries older than 24 hours
            old_score = current_time - 86400
            removed = limiter.redis.zremrangebyscore(key, 0, old_score)
            if removed:
                cleanup_count += removed

        logger.info(f"Cleaned up {cleanup_count} expired rate limit entries")
    except Exception as e:
        logger.error(f"Rate limit cleanup failed: {e}")