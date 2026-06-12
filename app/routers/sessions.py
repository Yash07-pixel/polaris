"""Discovery session API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import DiscoverySession, DrugTarget, Molecule
from app.schemas.session import SessionCreate, SessionResponse
from app.services.nlp_service import NLPService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionResponse:
    """Create a discovery session and identify the best matching demo target."""

    session = DiscoverySession(
        name=_build_session_name(payload.query),
        query=payload.query,
        objective=payload.query,
        status="PROCESSING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    result = NLPService().identify_target(payload.query)
    if result.target_key is None:
        session.status = "FAILED"
        session.confidence_score = result.confidence_score
        session.failure_reason = result.reason
        db.commit()
        db.refresh(session)
        return _to_response(session)

    target = db.scalar(select(DrugTarget).where(DrugTarget.name == _target_name_for_key(result.target_key)))
    if target is None:
        session.status = "FAILED"
        session.confidence_score = 0.0
        session.failure_reason = "Matched target is not present in the database."
        db.commit()
        db.refresh(session)
        return _to_response(session)

    session.target_id = target.id
    session.status = "COMPLETE"
    session.confidence_score = result.confidence_score
    session.molecules_generated = _count_molecules(db, target.id)
    session.molecules_passed_filter = _count_passed_filter(db, target.id)
    session.failure_reason = None
    db.commit()
    db.refresh(session)
    return _to_response(session)


@router.get("/", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionResponse]:
    """List discovery sessions, newest first."""

    sessions = db.scalars(
        select(DiscoverySession)
        .options(joinedload(DiscoverySession.target))
        .order_by(DiscoverySession.created_at.desc(), DiscoverySession.id.desc())
    ).all()
    return [_to_response(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionResponse:
    """Return a single discovery session by ID."""

    session = db.scalar(
        select(DiscoverySession)
        .options(joinedload(DiscoverySession.target))
        .where(DiscoverySession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return _to_response(session)


def _build_session_name(query: str) -> str:
    """Create a compact display name from the submitted query."""

    compact = " ".join(query.strip().split())
    return compact[:80] if compact else "Untitled discovery session"


def _count_molecules(db: Session, target_id: int) -> int:
    """Count all curated molecules associated with a target."""

    return int(db.scalar(select(func.count()).select_from(Molecule).where(Molecule.target_id == target_id)) or 0)


def _count_passed_filter(db: Session, target_id: int) -> int:
    """Count target molecules that pass the prototype safety filter."""

    return int(
        db.scalar(
            select(func.count())
            .select_from(Molecule)
            .where(Molecule.target_id == target_id, Molecule.is_toxic.is_(False))
        )
        or 0
    )


def _target_name_for_key(target_key: str) -> str:
    """Resolve a curated target key to the seeded database target name."""

    from app.curated_data.targets import CURATED_TARGETS

    for target in CURATED_TARGETS:
        if target["key"] == target_key:
            return target["name"]
    raise ValueError(f"Unknown target key: {target_key}")


def _to_response(session: DiscoverySession) -> SessionResponse:
    """Convert a database session model into an API response."""

    return SessionResponse(
        id=session.id,
        name=session.name,
        query=session.query,
        objective=session.objective,
        status=session.status,
        identified_target_name=session.target.name if session.target else None,
        confidence_score=session.confidence_score,
        molecules_generated=session.molecules_generated,
        molecules_passed_filter=session.molecules_passed_filter,
        failure_reason=session.failure_reason,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
