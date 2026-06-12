"""Schemas for molecule ranking and detail APIs."""

from pydantic import BaseModel


class ADMETMetricResponse(BaseModel):
    """Traffic-light ADMET metric response."""

    label: str
    value: str | int | float | bool
    status: str
    detail: str


class DockingDetailResponse(BaseModel):
    """Mock docking detail shown for rank-one molecules."""

    binding_pocket: str
    key_residues: list[str]
    interaction_types: list[str]
    affinity: str
    rmsd: float


class MoleculeResponse(BaseModel):
    """Molecule ranking/list response."""

    id: int
    target_id: int
    target_name: str
    rank: int | None
    name: str
    smiles: str
    image_path: str | None
    docking_score: float
    qed_score: float
    molecular_weight: float
    logp: float
    h_bond_donors: int
    h_bond_acceptors: int
    tpsa: float
    rotatable_bonds: int
    bioavailability_score: float
    solubility_log_s: float
    herg_risk: str
    ames_toxicity: bool
    hepatotoxicity: bool
    is_toxic: bool
    lipinski_pass: bool
    is_filtered: bool
    filter_reason: str | None
    admet: list[ADMETMetricResponse]
    docking_detail: DockingDetailResponse | None = None
