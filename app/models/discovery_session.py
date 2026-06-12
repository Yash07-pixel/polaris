"""Discovery session model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiscoverySession(Base):
    """A simulated discovery run grouping candidate evaluation activity."""

    __tablename__ = "discovery_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("drug_targets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    target: Mapped["DrugTarget"] = relationship(back_populates="discovery_sessions")
    reports: Mapped[list["DiscoveryReport"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
