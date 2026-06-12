"""Report generation and download API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DiscoveryReport
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.services.report_service import ReportService, ensure_report_file_exists

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)) -> ReportResponse:
    """Generate a simulated scientific report and PDF for a session."""

    try:
        report = ReportService().generate_report(db, payload.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(report)


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)) -> FileResponse:
    """Download a generated report PDF."""

    report = db.get(DiscoveryReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    try:
        pdf_path = ensure_report_file_exists(report)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )


@router.get("/session/{session_id}", response_model=list[ReportResponse])
def list_reports_for_session(session_id: int, db: Session = Depends(get_db)) -> list[ReportResponse]:
    """List generated reports for a discovery session."""

    reports = db.scalars(
        select(DiscoveryReport)
        .where(DiscoveryReport.session_id == session_id)
        .order_by(DiscoveryReport.created_at.desc(), DiscoveryReport.id.desc())
    ).all()
    return [_to_response(report) for report in reports]


def _to_response(report: DiscoveryReport) -> ReportResponse:
    """Convert a report model into API metadata."""

    return ReportResponse(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        summary=report.summary,
        recommendation=report.recommendation,
        pdf_path=report.pdf_path,
        download_url=f"/api/v1/reports/{report.id}/download",
        druggability_score=report.druggability_score,
        created_at=report.created_at,
    )
