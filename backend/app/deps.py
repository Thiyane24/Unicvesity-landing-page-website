"""
Reusable FastAPI dependencies.

Right now: just a simple bearer-token guard for admin endpoints.
For real production, swap this out for JWT/OAuth, but the shape
of the dependency stays the same.
"""
from __future__ import annotations

import hmac
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# auto_error=False so we can return 401 with our own message format
_bearer_scheme = HTTPBearer(auto_error=False)


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """
    Guard /api/admin/* endpoints.

    Open the admin page with:
        Authorization: Bearer <ADMIN_TOKEN>

    Or, from the URL, by sending the token as `?token=...` and letting the
    frontend JS attach the header before calling the API.
    """
    expected = settings.ADMIN_TOKEN

    # Constant-time compare to avoid timing attacks.
    if creds is None or creds.scheme.lower() != "bearer" or not hmac.compare_digest(
        creds.credentials or "", expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return creds.credentials  # so the route can echo it for audit logs
