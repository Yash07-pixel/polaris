"""Drug target model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DrugTarget(Base):
    """A curated therapeutic target used for prototype discovery workflows."""

    __tablename__ = "drug_targets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    gene_symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    uniprot_id: Mapped[str] = mapped_column(String(16), nullable=False)
    disease_area: Mapped[str] = mapped_column(String(120), nullable=False)
    mechanism: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    molecules: Mapped[list["Molecule"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )
    discovery_sessions: Mapped[list["DiscoverySession"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )
