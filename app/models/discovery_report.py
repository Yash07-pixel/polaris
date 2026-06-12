"""Discovery report model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiscoveryReport(Base):
    """A simulated report generated from a discovery session."""

    __tablename__ = "discovery_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("discovery_sessions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    session: Mapped["DiscoverySession"] = relationship(back_populates="reports")
