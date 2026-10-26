"""FastAPI main application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes_health import router as health_router
from backend.api.routes_tasks import router as tasks_router
from backend.api.routes_evals import router as evals_router
from backend.config import get_settings
from backend.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hooks: initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Bounded, stateful AI Research & Workflow Automation Agent with verified citations, LangSmith tracing, and offline demo mode",
    lifespan=lifespan,
)

# CORS setup for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(evals_router)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "demo_mode": settings.DEMO_MODE,
    }
