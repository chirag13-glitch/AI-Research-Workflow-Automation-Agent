"""Health and readiness probe endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import get_settings
from backend.db.session import get_db

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check validating application state and database connectivity."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "mode": "Demo Mode" if settings.DEMO_MODE else "Live Mode",
        "database": db_status,
        "environment": settings.APP_ENV,
    }
