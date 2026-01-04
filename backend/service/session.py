"""
Session Management for Nexus AA Service

Provides secure session management with:
- Absolute timeout (30 minutes)
- Idle timeout (5 minutes of inactivity)
- Redis-based storage
- Automatic cleanup
"""
import secrets
import time
import json
import hashlib
from typing import Optional, Dict
from backend.service.redis_client import redis_client

# Configuration
SESSION_ABSOLUTE_TIMEOUT = 30 * 60  # 30 minutes absolute expiration
SESSION_IDLE_TIMEOUT = 5 * 60       # 5 minutes idle timeout


class SessionManager:
    """Manages user sessions with automatic expiration"""

    @staticmethod
    def create_session(password: str) -> str:
        """
        Create a new session after successful authentication.

        Args:
            password: User's password (will be hashed for verification)

        Returns:
            Session token (secure random string)
        """
        session_token = secrets.token_urlsafe(32)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        session_data = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "password_hash": password_hash
        }

        # Store in Redis with absolute expiration
        redis_client.setex(
            f"session:{session_token}",
            SESSION_ABSOLUTE_TIMEOUT,
            json.dumps(session_data)
        )

        return session_token

    @staticmethod
    def verify_session(session_token: str) -> Optional[Dict]:
        """
        Verify if a session is valid.

        Checks:
        1. Session exists in Redis
        2. Not exceeded idle timeout

        Args:
            session_token: Session token to verify

        Returns:
            Session data if valid, None otherwise
        """
        data = redis_client.get(f"session:{session_token}")
        if not data:
            return None
        print('data:', data)
        session = data

        # Check idle timeout
        if time.time() - session["last_activity"] > SESSION_IDLE_TIMEOUT:
            SessionManager.destroy_session(session_token)
            return None

        return session

    @staticmethod
    def update_activity(session_token: str) -> bool:
        """
        Update last activity time for a session.

        Args:
            session_token: Session token

        Returns:
            True if updated successfully, False if session not found
        """
        data = redis_client.get(f"session:{session_token}")
        if not data:
            return False

        session = data
        session["last_activity"] = time.time()

        # Get remaining TTL for absolute expiration
        remaining_ttl = redis_client.ttl(f"session:{session_token}")

        if remaining_ttl > 0:
            redis_client.setex(
                f"session:{session_token}",
                remaining_ttl,
                json.dumps(session)
            )
            return True

        return False

    @staticmethod
    def destroy_session(session_token: str):
        """
        Destroy a session (logout).

        Args:
            session_token: Session token to destroy
        """
        redis_client.delete(f"session:{session_token}")

    @staticmethod
    def get_session_info(session_token: str) -> Optional[Dict]:
        """
        Get session information (for debugging/monitoring).

        Args:
            session_token: Session token

        Returns:
            Session info including creation time, last activity, and remaining time
        """
        session = SessionManager.verify_session(session_token)
        if not session:
            return None

        remaining_ttl = redis_client.ttl(f"session:{session_token}")
        idle_time = time.time() - session["last_activity"]

        return {
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "idle_seconds": int(idle_time),
            "remaining_seconds": remaining_ttl,
            "will_expire_at": time.time() + remaining_ttl
        }
