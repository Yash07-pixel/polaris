"""Database engine, sessions, and initialization helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
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
