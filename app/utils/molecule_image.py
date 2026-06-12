"""RDKit molecule image generation utilities."""

from pathlib import Path

from PIL import Image
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Molecule

IMAGE_DIR = Path("static") / "molecules"
IMAGE_SIZE = (900, 680)


def image_path_for_molecule(molecule: Molecule) -> Path:
    """Return the deterministic PNG path for a molecule."""

    return IMAGE_DIR / f"{molecule.id}_{molecule.name.lower().replace(' ', '_')}.png"


def generate_molecule_image(smiles: str, output_path: Path) -> None:
    """Parse SMILES, generate 2D coordinates, and save a PNG structure image."""

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES cannot be rendered: {smiles}")

    AllChem.Compute2DCoords(mol)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Draw.MolToFile(mol, str(output_path), size=IMAGE_SIZE, kekulize=True)


def pregenerate_molecule_images(db: Session) -> None:
    """Generate missing molecule PNGs and store their paths in the database."""

    molecules = db.scalars(select(Molecule).order_by(Molecule.id)).all()
    changed = False
    for molecule in molecules:
        path = image_path_for_molecule(molecule)
        if not path.exists() or _image_is_low_resolution(path):
            generate_molecule_image(molecule.smiles, path)
        stored_path = path.as_posix()
        if molecule.image_path != stored_path:
            molecule.image_path = stored_path
            changed = True

    if changed:
        db.commit()


def _image_is_low_resolution(path: Path) -> bool:
    """Return whether an existing molecule PNG should be regenerated."""

    try:
        with Image.open(path) as image:
            width, height = image.size
        return width < IMAGE_SIZE[0] or height < IMAGE_SIZE[1]
    except OSError:
        return True
