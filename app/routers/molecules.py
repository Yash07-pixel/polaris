"""Molecule retrieval, filtering, and ranking API routes."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from rdkit import Chem
from rdkit.Chem import QED
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.ml.admet_predictor import admet_predictor
from app.models import DiscoverySession, Molecule
from app.schemas.molecule import DockingDetailResponse, MoleculeResponse

SortMode = Literal["rank", "docking", "qed"]

router = APIRouter(prefix="/api/v1/molecules", tags=["molecules"])


@router.get("/", response_model=list[MoleculeResponse])
def list_molecules(
    lipinski_only: bool = Query(False),
    sort: SortMode = Query("rank"),
    db: Session = Depends(get_db),
) -> list[MoleculeResponse]:
    """Return ranked curated molecules across all demo targets."""

    molecules = db.scalars(
        select(Molecule).options(joinedload(Molecule.target)).order_by(Molecule.id)
    ).all()
    ranked = _rank_molecules(molecules, sort)
    if lipinski_only:
        ranked = [(molecule, rank) for molecule, rank in ranked if admet_predictor.passes_lipinski(molecule)]
    return [_to_response(molecule, rank) for molecule, rank in ranked]


@router.get("/session/{session_id}", response_model=list[MoleculeResponse])
def list_molecules_for_session(
    session_id: int,
    lipinski_only: bool = Query(False),
    sort: SortMode = Query("rank"),
    db: Session = Depends(get_db),
) -> list[MoleculeResponse]:
    """Return ranked curated molecules for a completed discovery session target."""

    session = db.scalar(select(DiscoverySession).where(DiscoverySession.id == session_id))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if session.target_id is None:
        return []

    molecules = db.scalars(
        select(Molecule)
        .options(joinedload(Molecule.target))
        .where(Molecule.target_id == session.target_id)
        .order_by(Molecule.id)
    ).all()
    ranked = _rank_molecules(molecules, sort)
    if lipinski_only:
        ranked = [(molecule, rank) for molecule, rank in ranked if admet_predictor.passes_lipinski(molecule)]
    return [_to_response(molecule, rank) for molecule, rank in ranked]


@router.get("/{molecule_id}", response_model=MoleculeResponse)
def get_molecule(molecule_id: int, db: Session = Depends(get_db)) -> MoleculeResponse:
    """Return detail for a single curated molecule."""

    molecule = db.scalar(
        select(Molecule)
        .options(joinedload(Molecule.target))
        .where(Molecule.id == molecule_id)
    )
    if molecule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Molecule not found.")

    target_molecules = db.scalars(
        select(Molecule)
        .options(joinedload(Molecule.target))
        .where(Molecule.target_id == molecule.target_id)
    ).all()
    rank_lookup = {candidate.id: rank for candidate, rank in _rank_molecules(target_molecules, "rank")}
    return _to_response(molecule, rank_lookup.get(molecule.id))


def _rank_molecules(molecules: list[Molecule], sort: SortMode) -> list[tuple[Molecule, int]]:
    """Rank molecules by target-local composite rank, then apply requested sort."""

    rank_lookup: dict[int, int] = {}
    by_target: dict[int, list[Molecule]] = {}
    for molecule in molecules:
        by_target.setdefault(molecule.target_id, []).append(molecule)

    for target_molecules in by_target.values():
        ordered = sorted(target_molecules, key=_rank_score, reverse=True)
        for index, molecule in enumerate(ordered, start=1):
            rank_lookup[molecule.id] = index

    if sort == "docking":
        ordered_molecules = sorted(molecules, key=lambda molecule: molecule.docking_score)
    elif sort == "qed":
        ordered_molecules = sorted(molecules, key=_qed_score, reverse=True)
    else:
        ordered_molecules = sorted(molecules, key=lambda molecule: (rank_lookup[molecule.id], molecule.target_id))

    return [(molecule, rank_lookup[molecule.id]) for molecule in ordered_molecules]


def _rank_score(molecule: Molecule) -> float:
    """Compute a prototype ranking score from curated docking, QED, and safety values."""

    safety_penalty = 0.2 if admet_predictor.is_problematic(molecule) else 0.0
    return (-molecule.docking_score * 0.6) + (_qed_score(molecule) * 3.0) - safety_penalty


def _qed_score(molecule: Molecule) -> float:
    """Calculate QED from curated SMILES without creating new molecules."""

    mol = Chem.MolFromSmiles(molecule.smiles)
    if mol is None:
        return 0.0
    return round(float(QED.qed(mol)), 3)


def _to_response(molecule: Molecule, rank: int | None) -> MoleculeResponse:
    """Convert a molecule model into ranked API output."""

    lipinski_pass = admet_predictor.passes_lipinski(molecule)
    is_filtered = admet_predictor.is_problematic(molecule)
    return MoleculeResponse(
        id=molecule.id,
        target_id=molecule.target_id,
        target_name=molecule.target.name,
        rank=rank,
        name=molecule.name,
        smiles=molecule.smiles,
        image_path=molecule.image_path,
        docking_score=molecule.docking_score,
        qed_score=_qed_score(molecule),
        molecular_weight=molecule.molecular_weight,
        logp=molecule.logp,
        h_bond_donors=molecule.h_bond_donors,
        h_bond_acceptors=molecule.h_bond_acceptors,
        tpsa=molecule.tpsa,
        rotatable_bonds=molecule.rotatable_bonds,
        bioavailability_score=molecule.bioavailability_score,
        solubility_log_s=molecule.solubility_log_s,
        herg_risk=molecule.herg_risk,
        ames_toxicity=molecule.ames_toxicity,
        hepatotoxicity=molecule.hepatotoxicity,
        is_toxic=molecule.is_toxic,
        lipinski_pass=lipinski_pass,
        is_filtered=is_filtered,
        filter_reason=_filter_reason(molecule, lipinski_pass),
        admet=[metric.__dict__ for metric in admet_predictor.evaluate(molecule)],
        docking_detail=_docking_detail(molecule) if rank == 1 else None,
    )


def _filter_reason(molecule: Molecule, lipinski_pass: bool) -> str | None:
    """Return the reason a molecule is marked problematic."""

    reasons: list[str] = []
    if not lipinski_pass:
        reasons.append("Lipinski rule-of-five issue")
    if molecule.is_toxic:
        reasons.append("Seeded toxicity concern")
    if molecule.ames_toxicity:
        reasons.append("Ames toxicity flag")
    if molecule.hepatotoxicity:
        reasons.append("Hepatotoxicity flag")
    if molecule.herg_risk.lower() == "high":
        reasons.append("High hERG risk")
    return "; ".join(reasons) if reasons else None


def _docking_detail(molecule: Molecule) -> DockingDetailResponse:
    """Return prototype binding details for rank-one molecules only."""

    target_details = {
        "EGFR": ("ATP hinge pocket", ["Met793", "Leu718", "Asp855"], ["hydrogen bond", "pi-stacking"], 1.18),
        "JAK2": ("JH1 ATP-binding cleft", ["Leu932", "Glu930", "Asp994"], ["hydrogen bond", "hydrophobic contact"], 1.34),
        "BACE1": ("Catalytic aspartyl pocket", ["Asp32", "Asp228", "Thr72"], ["salt bridge", "hydrogen bond"], 1.42),
        "TNF": ("Trimer interface groove", ["Tyr59", "Leu57", "Tyr119"], ["hydrophobic contact", "pi-stacking"], 1.51),
        "POL": ("Integrase metal-binding pocket", ["Asp64", "Asp116", "Glu152"], ["metal chelation", "hydrogen bond"], 1.27),
    }
    pocket, residues, interactions, rmsd = target_details.get(
        molecule.target.gene_symbol,
        ("Prototype binding pocket", ["ResidueA", "ResidueB"], ["hydrogen bond"], 1.5),
    )
    return DockingDetailResponse(
        binding_pocket=pocket,
        key_residues=residues,
        interaction_types=interactions,
        affinity=f"{molecule.docking_score:.1f} kcal/mol",
        rmsd=rmsd,
    )
