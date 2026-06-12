"""FastAPI application factory and startup flow for MolGenix."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.mock_data.validation import validate_mock_data
from app.routers.health import router as health_router
from app.routers.molecules import router as molecules_router
from app.routers.reports import router as reports_router
from app.routers.sessions import router as sessions_router
from app.seed import seed_database
from app.utils.molecule_image import pregenerate_molecule_images


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables, validate mock data, and seed when empty."""

    init_db()
    validate_mock_data()
    with SessionLocal() as db:
        seed_database(db)
        pregenerate_molecule_images(db)
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
    Path("static").mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(health_router)
    app.include_router(sessions_router)
    app.include_router(molecules_router)
    app.include_router(reports_router)
    return app


app = create_app()
