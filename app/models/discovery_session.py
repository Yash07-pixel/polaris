"""Discovery session model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiscoverySession(Base):
    """A simulated discovery run grouping candidate evaluation activity."""

    __tablename__ = "discovery_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("drug_targets.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESSING")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    molecules_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    molecules_passed_filter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    target: Mapped[DrugTarget | None] = relationship(back_populates="discovery_sessions")
    reports: Mapped[list["DiscoveryReport"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
