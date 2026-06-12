"""Schemas for report generation and download APIs."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Request body for generating a simulated research report."""

    session_id: int = Field(..., ge=1)


class ReportResponse(BaseModel):
    """Report metadata returned by report APIs."""

    id: int
    session_id: int
    title: str
    summary: str
    recommendation: str
    pdf_path: str | None
    download_url: str
    druggability_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
