"""Schemas for discovery session APIs."""

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request body for creating a discovery session from a biomedical query."""

    query: str = Field(..., min_length=3, max_length=1000)


class SessionResponse(BaseModel):
    """Discovery session response returned by the API."""

    id: int
    name: str
    query: str
    objective: str
    status: str
    identified_target_name: str | None
    confidence_score: float | None
    molecules_generated: int
    molecules_passed_filter: int
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
