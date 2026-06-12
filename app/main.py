"""FastAPI application factory and startup flow for MolGenix."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.mock_data.validation import validate_mock_data
from app.routers.health import router as health_router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables, validate mock data, and seed when empty."""

    init_db()
    validate_mock_data()
    with SessionLocal() as db:
        seed_database(db)
    yield


def create_app() -> FastAPI:
    """Create and configure the MolGenix FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered drug discovery prototype backend using mock data only.",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
