"""FastAPI application factory and startup flow for MolGenix."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Path("static").mkdir(exist_ok=True)
    Path("styles").mkdir(exist_ok=True)
    Path("js").mkdir(exist_ok=True)
    _register_exception_handlers(app)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/styles", StaticFiles(directory="styles"), name="styles")
    app.mount("/js", StaticFiles(directory="js"), name="js")
    app.include_router(health_router)
    app.include_router(sessions_router)
    app.include_router(molecules_router)
    app.include_router(reports_router)

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        """Serve the MolGenix single-page demo frontend."""

        return FileResponse("index.html")

    @app.get("/app", include_in_schema=False)
    def frontend_alias() -> FileResponse:
        """Serve the MolGenix frontend from an explicit app route."""

        return FileResponse("index.html")

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register stable JSON errors for the demo API."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Request validation failed.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": str(exc)},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "A demo database operation failed."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Unexpected demo server error."},
        )


app = create_app()
