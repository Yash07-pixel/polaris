"""Validation helpers for simulated MolGenix seed data."""

from collections import Counter

from rdkit import Chem

from app.mock_data.molecules import MOCK_MOLECULES
from app.mock_data.targets import MOCK_TARGETS

EXPECTED_TARGET_COUNT = 5
EXPECTED_MOLECULES_PER_TARGET = 8
EXPECTED_MOLECULE_COUNT = EXPECTED_TARGET_COUNT * EXPECTED_MOLECULES_PER_TARGET


def validate_mock_data() -> None:
    """Validate strict prototype data requirements before database seeding."""

    target_keys = [target["key"] for target in MOCK_TARGETS]
    if len(MOCK_TARGETS) != EXPECTED_TARGET_COUNT:
        raise ValueError(f"Expected {EXPECTED_TARGET_COUNT} targets, found {len(MOCK_TARGETS)}.")
    if len(set(target_keys)) != EXPECTED_TARGET_COUNT:
        raise ValueError("Mock target keys must be unique.")
    if len(MOCK_MOLECULES) != EXPECTED_MOLECULE_COUNT:
        raise ValueError(f"Expected {EXPECTED_MOLECULE_COUNT} molecules, found {len(MOCK_MOLECULES)}.")

    counts = Counter(str(molecule["target_key"]) for molecule in MOCK_MOLECULES)
    for target_key in target_keys:
        if counts[target_key] != EXPECTED_MOLECULES_PER_TARGET:
            raise ValueError(
                f"Expected {EXPECTED_MOLECULES_PER_TARGET} molecules for {target_key}, "
                f"found {counts[target_key]}."
            )

    unknown_targets = set(counts) - set(target_keys)
    if unknown_targets:
        raise ValueError(f"Molecules reference unknown target keys: {sorted(unknown_targets)}.")

    toxic_by_target: Counter[str] = Counter()
    for molecule in MOCK_MOLECULES:
        if float(molecule["docking_score"]) >= 0:
            raise ValueError(f"{molecule['name']} has a non-negative docking score.")
        smiles = str(molecule["smiles"]).strip()
        if not smiles:
            raise ValueError(f"{molecule['name']} is missing a SMILES string.")
        if Chem.MolFromSmiles(smiles) is None:
            raise ValueError(f"{molecule['name']} has invalid SMILES: {smiles}.")
        if bool(molecule["is_toxic"]):
            toxic_by_target[str(molecule["target_key"])] += 1

    missing_toxic_targets = [target_key for target_key in target_keys if toxic_by_target[target_key] < 1]
    if missing_toxic_targets:
        raise ValueError(f"At least one toxic molecule is required per target: {missing_toxic_targets}.")
