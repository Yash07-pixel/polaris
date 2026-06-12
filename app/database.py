"""Database engine, sessions, and initialization helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables."""

    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _refresh_session_tables_if_needed()


def _refresh_session_tables_if_needed() -> None:
    """Refresh prototype session tables when their shape changes between phases."""

    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "discovery_sessions" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("discovery_sessions")}
    required_columns = {
        "query",
        "confidence_score",
        "molecules_generated",
        "molecules_passed_filter",
        "failure_reason",
    }
    target_column = columns.get("target_id")
    target_is_required = bool(target_column and not target_column.get("nullable", True))
    if required_columns.issubset(columns) and not target_is_required:
        return

    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS discovery_reports"))
        connection.execute(text("DROP TABLE IF EXISTS discovery_sessions"))

    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
