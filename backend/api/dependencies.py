"""FastAPI dependencies re-exports."""
from backend.db.session import get_db
from backend.services.auth import (
    get_current_user,
    get_admin_user,
    verify_task_ownership,
    get_api_key_from_headers,
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_admin_user",
    "verify_task_ownership",
    "get_api_key_from_headers",
]
