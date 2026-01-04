"""
Authentication Middleware for Nexus AA Service

Provides session-based authentication for protected endpoints.
"""
from fastapi import Header, HTTPException, Depends
from typing import Optional
from backend.service.session import SessionManager


async def verify_session_token(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> str:
    """
    Verify session token from request header.

    This is a FastAPI dependency that can be used to protect endpoints.

    Usage:
        @app.get("/protected")
        async def protected_endpoint(session_token: str = Depends(verify_session_token)):
            # This endpoint requires valid session
            ...

    Args:
        x_session_token: Session token from X-Session-Token header

    Returns:
        Valid session token

    Raises:
        HTTPException: 401 if session is invalid or expired
    """
    if not x_session_token:
        raise HTTPException(
            status_code=401,
            detail="Missing session token. Please unlock wallet first."
        )

    session = SessionManager.verify_session(x_session_token)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid. Please unlock wallet again."
        )

    # Update last activity time
    SessionManager.update_activity(x_session_token)

    return x_session_token


async def optional_session_token(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> Optional[str]:
    """
    Optional session token verification.

    Returns session token if valid, None if missing or invalid.
    Does not raise exception.

    Usage:
        @app.get("/public-or-private")
        async def endpoint(session_token: Optional[str] = Depends(optional_session_token)):
            if session_token:
                # User is authenticated
                ...
            else:
                # User is not authenticated
                ...

    Args:
        x_session_token: Session token from X-Session-Token header

    Returns:
        Valid session token or None
    """
    if not x_session_token:
        return None

    session = SessionManager.verify_session(x_session_token)

    if session:
        SessionManager.update_activity(x_session_token)
        return x_session_token

    return None
