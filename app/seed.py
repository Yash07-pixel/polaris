"""Database seeding for the MolGenix prototype."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.curated_data.molecules import CURATED_MOLECULES
from app.curated_data.targets import CURATED_TARGETS
from app.curated_data.validation import validate_curated_data
from app.models import DrugTarget, Molecule


def _table_count(db: Session, model: type[DrugTarget] | type[Molecule]) -> int:
    """Return the row count for a SQLAlchemy model."""

    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def seed_database(db: Session) -> None:
    """Seed curated targets and molecules when the prototype database is empty."""

    validate_curated_data()

    target_count = _table_count(db, DrugTarget)
    molecule_count = _table_count(db, Molecule)
    if target_count > 0 or molecule_count > 0:
        _sync_existing_seed_data(db)
        return

    targets_by_key: dict[str, DrugTarget] = {}
    for target_data in CURATED_TARGETS:
        target = DrugTarget(
            name=target_data["name"],
            gene_symbol=target_data["gene_symbol"],
            uniprot_id=target_data["uniprot_id"],
            disease_area=target_data["disease_area"],
            mechanism=target_data["mechanism"],
            description=target_data["description"],
        )
        targets_by_key[target_data["key"]] = target
        db.add(target)

    db.flush()

    for molecule_data in CURATED_MOLECULES:
        data = dict(molecule_data)
        target_key = str(data.pop("target_key"))
        molecule = Molecule(target_id=targets_by_key[target_key].id, **data)
        db.add(molecule)

    db.commit()


def _sync_existing_seed_data(db: Session) -> None:
    """Synchronize existing prototype rows with the curated dataset without duplicating data."""

    targets_by_key: dict[str, DrugTarget] = {}
    for target_data in CURATED_TARGETS:
        target = db.scalar(select(DrugTarget).where(DrugTarget.name == target_data["name"]))
        if target is None:
            continue
        target.gene_symbol = target_data["gene_symbol"]
        target.uniprot_id = target_data["uniprot_id"]
        target.disease_area = target_data["disease_area"]
        target.mechanism = target_data["mechanism"]
        target.description = target_data["description"]
        targets_by_key[target_data["key"]] = target

    for molecule_data in CURATED_MOLECULES:
        molecule = db.scalar(select(Molecule).where(Molecule.name == str(molecule_data["name"])))
        if molecule is None:
            continue
        target_key = str(molecule_data["target_key"])
        if target_key in targets_by_key:
            molecule.target_id = targets_by_key[target_key].id
        for key, value in molecule_data.items():
            if key != "target_key":
                setattr(molecule, key, value)

    db.commit()
