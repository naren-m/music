"""
Session Manager
Handles user sessions, resource allocation, and cleanup for audio processing.
"""

import time
import threading
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from core.services.audio_engine import CarnaticAudioEngine, AudioConfig

logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Stores all data related to an active user session"""
    session_id: str
    user_id: Optional[str]
    created_at: float
    last_activity: float
    audio_engine: CarnaticAudioEngine
    # Store minimal history for current exercise/context, not infinite global history
    # For long-term stats, we should flush to DB, not keep in memory
    current_context: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        """Check if session has been inactive for too long"""
        return (time.time() - self.last_activity) > timeout_seconds

class SessionManager:
    """
    Thread-safe session management with automatic cleanup.
    Prevents memory leaks by enforcing timeouts and limits.
    """

    def __init__(self, cleanup_interval: int = 300, session_timeout: int = 1800):
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._session_timeout = session_timeout
        self._shutdown_event = threading.Event()
        
        # Shared thread pool for all sessions to prevent thread explosion
        # Instead of each AudioEngine having its own pool
        self._shared_executor = ThreadPoolExecutor(
            max_workers=8, 
            thread_name_prefix="audio_session_worker"
        )
        
        # Start cleanup background thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, 
            daemon=True,
            name="SessionCleanupThread"
        )
        self._cleanup_thread.start()
        
        logger.info("SessionManager initialized")

    def create_session(self, session_id: str, user_id: Optional[str] = None) -> SessionData:
        """Create a new session or reset existing one"""
        with self._lock:
            if session_id in self._sessions:
                logger.info(f"Resetting existing session {session_id}")
                # We could preserve some state, but for now we reset to ensure clean slate
                # But let's keep the engine instance to avoid re-init overhead if possible?
                # Actually, simpler to just update last_activity if it exists, 
                # but 'create' usually implies new.
                # Let's return existing if found, just update activity
                session = self._sessions[session_id]
                session.last_activity = time.time()
                if user_id:
                    session.user_id = user_id
                return session

            logger.info(f"Creating new session {session_id} (User: {user_id})")
            
            # Initialize audio engine
            config = AudioConfig()
            # If we wanted to share the executor, we'd need to modify AudioEngine to accept it
            # For now, AudioEngine uses its internal logic or none (the one we wrote doesn't use executor for detecting)
            engine = CarnaticAudioEngine(config)
            
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                created_at=time.time(),
                last_activity=time.time(),
                audio_engine=engine
            )
            
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session and update its activity timestamp"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_activity = time.time()
            return session

    def remove_session(self, session_id: str):
        """Manually remove a session (e.g. on disconnect)"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.debug(f"Removed session {session_id}")

    def _cleanup_loop(self):
        """Background loop to remove expired sessions"""
        while not self._shutdown_event.is_set():
            try:
                self._cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
            
            # Sleep for interval or until shutdown
            if self._shutdown_event.wait(self._cleanup_interval):
                break

    def _cleanup_expired_sessions(self):
        """Check and remove sessions that have timed out"""
        with self._lock:
            now = time.time()
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if (now - session.last_activity) > self._session_timeout
            ]
            
            for sid in expired_ids:
                logger.info(f"Cleaning up expired session {sid}")
                del self._sessions[sid]
                
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions. Active count: {len(self._sessions)}")

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down SessionManager...")
        self._shutdown_event.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)
        self._shared_executor.shutdown(wait=False)
        with self._lock:
            self._sessions.clear()

# Global singleton instance
session_manager = SessionManager()
