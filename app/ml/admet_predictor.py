"""Traffic-light ADMET visualization helpers for simulated molecule data."""

from dataclasses import dataclass
from typing import Literal

from app.models import Molecule

TrafficLight = Literal["Green", "Yellow", "Red"]


@dataclass(frozen=True)
class ADMETMetric:
    """A single ADMET metric formatted for traffic-light visualization."""

    label: str
    value: str | int | float | bool
    status: TrafficLight
    detail: str


class ADMETPredictor:
    """Create mock traffic-light ADMET summaries from pre-seeded values."""

    def evaluate(self, molecule: Molecule) -> list[ADMETMetric]:
        """Return traffic-light ADMET metrics for a molecule."""

        return [
            ADMETMetric(
                label="Lipinski",
                value="Pass" if self.passes_lipinski(molecule) else "Fail",
                status="Green" if self.passes_lipinski(molecule) else "Red",
                detail="Rule-of-five screen using seeded molecular properties.",
            ),
            ADMETMetric(
                label="Solubility",
                value=molecule.solubility_log_s,
                status=self._solubility_status(molecule.solubility_log_s),
                detail="Simulated logS; less negative values are treated as more soluble.",
            ),
            ADMETMetric(
                label="hERG Risk",
                value=molecule.herg_risk,
                status=self._risk_status(molecule.herg_risk),
                detail="Seeded cardiac ion-channel liability flag.",
            ),
            ADMETMetric(
                label="Ames Toxicity",
                value=molecule.ames_toxicity,
                status="Red" if molecule.ames_toxicity else "Green",
                detail="Seeded mutagenicity screen flag.",
            ),
            ADMETMetric(
                label="Hepatotoxicity",
                value=molecule.hepatotoxicity,
                status="Red" if molecule.hepatotoxicity else "Green",
                detail="Seeded liver safety flag.",
            ),
            ADMETMetric(
                label="Bioavailability",
                value=molecule.bioavailability_score,
                status=self._bioavailability_status(molecule.bioavailability_score),
                detail="Simulated oral bioavailability score.",
            ),
            ADMETMetric(
                label="Clearance",
                value=molecule.clearance_ml_min_kg,
                status=self._clearance_status(molecule.clearance_ml_min_kg),
                detail="Simulated clearance in mL/min/kg.",
            ),
        ]

    def passes_lipinski(self, molecule: Molecule) -> bool:
        """Return whether the molecule passes a simple Lipinski filter."""

        return (
            molecule.molecular_weight <= 500
            and molecule.logp <= 5
            and molecule.h_bond_donors <= 5
            and molecule.h_bond_acceptors <= 10
        )

    def is_problematic(self, molecule: Molecule) -> bool:
        """Return whether seeded safety or drug-likeness signals are problematic."""

        return molecule.is_toxic or not self.passes_lipinski(molecule)

    @staticmethod
    def _risk_status(risk: str) -> TrafficLight:
        """Map low/medium/high seeded risk values to traffic lights."""

        normalized = risk.lower()
        if normalized == "low":
            return "Green"
        if normalized == "medium":
            return "Yellow"
        return "Red"

    @staticmethod
    def _solubility_status(log_s: float) -> TrafficLight:
        """Map simulated solubility values to traffic lights."""

        if log_s >= -3.5:
            return "Green"
        if log_s >= -5.0:
            return "Yellow"
        return "Red"

    @staticmethod
    def _bioavailability_status(score: float) -> TrafficLight:
        """Map simulated bioavailability scores to traffic lights."""

        if score >= 0.55:
            return "Green"
        if score >= 0.45:
            return "Yellow"
        return "Red"

    @staticmethod
    def _clearance_status(clearance: float) -> TrafficLight:
        """Map simulated clearance values to traffic lights."""

        if clearance <= 10:
            return "Green"
        if clearance <= 16:
            return "Yellow"
        return "Red"


admet_predictor = ADMETPredictor()
