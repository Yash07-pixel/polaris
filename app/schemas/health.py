"""Health check schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response payload for the basic health endpoint."""

    status: str
    app_name: str
    version: str


class ReadinessResponse(HealthResponse):
    """Response payload for readiness checks with seed counts."""

    targets: int
    molecules: int
