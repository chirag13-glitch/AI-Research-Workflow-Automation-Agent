"""Authentication, API Key verification, and Task ownership enforcement."""
import hashlib
import hmac
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import get_settings
from backend.db.session import get_db, hash_key
from backend.models.orm import User, ApiKey, Task

settings = get_settings()


async def get_api_key_from_headers(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """Extract API key from Bearer token or X-API-Key header."""
    if x_api_key:
        return x_api_key.strip()
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()
    # If DEMO_MODE is true and no header is provided, use default test key for seamless local dev
    if settings.DEMO_MODE:
        return settings.DEFAULT_TEST_USER_KEY
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing API key. Provide via 'X-API-Key' or 'Authorization: Bearer <key>'.",
    )


async def get_current_user(
    raw_key: str = Depends(get_api_key_from_headers),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate API key against database and return authenticated User."""
    key_h = hash_key(raw_key)
    query = (
        select(User)
        .join(ApiKey, ApiKey.user_id == User.id)
        .where(ApiKey.key_hash == key_h, ApiKey.is_active.is_(True), User.is_active.is_(True))
    )
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key.",
        )
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce admin privileges for restricted endpoints (e.g. evaluations)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation.",
        )
    return current_user


async def verify_task_ownership(
    task_id: str,
    user: User,
    db: AsyncSession,
) -> Task:
    """Ensure task exists and caller is owner or admin."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    if not user.is_admin and task.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this research task.",
        )
    return task
