"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import DrugTarget, Molecule
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return basic application health."""

    return HealthResponse(status="ok", app_name=settings.APP_NAME, version=settings.APP_VERSION)


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """Return readiness state and curated dataset counts."""

    target_count = int(db.scalar(select(func.count()).select_from(DrugTarget)) or 0)
    molecule_count = int(db.scalar(select(func.count()).select_from(Molecule)) or 0)
    return ReadinessResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        targets=target_count,
        molecules=molecule_count,
    )
