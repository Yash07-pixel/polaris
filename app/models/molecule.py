"""Molecule model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Molecule(Base):
    """A simulated candidate molecule with computed prototype properties."""

    __tablename__ = "molecules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("drug_targets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    smiles: Mapped[str] = mapped_column(String(500), nullable=False)
    molecular_weight: Mapped[float] = mapped_column(Float, nullable=False)
    logp: Mapped[float] = mapped_column(Float, nullable=False)
    h_bond_donors: Mapped[int] = mapped_column(Integer, nullable=False)
    h_bond_acceptors: Mapped[int] = mapped_column(Integer, nullable=False)
    tpsa: Mapped[float] = mapped_column(Float, nullable=False)
    rotatable_bonds: Mapped[int] = mapped_column(Integer, nullable=False)
    bioavailability_score: Mapped[float] = mapped_column(Float, nullable=False)
    solubility_log_s: Mapped[float] = mapped_column(Float, nullable=False)
    clearance_ml_min_kg: Mapped[float] = mapped_column(Float, nullable=False)
    half_life_hours: Mapped[float] = mapped_column(Float, nullable=False)
    herg_risk: Mapped[str] = mapped_column(String(24), nullable=False)
    ames_toxicity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hepatotoxicity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ld50_mg_kg: Mapped[float] = mapped_column(Float, nullable=False)
    docking_score: Mapped[float] = mapped_column(Float, nullable=False)
    synthetic_accessibility: Mapped[float] = mapped_column(Float, nullable=False)
    is_toxic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    target: Mapped["DrugTarget"] = relationship(back_populates="molecules")
