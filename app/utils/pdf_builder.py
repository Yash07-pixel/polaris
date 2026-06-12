"""ReportLab PDF builder for simulated MolGenix research reports."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rdkit import Chem
from rdkit.Chem import QED

from app.ml.admet_predictor import admet_predictor
from app.models import DiscoverySession, Molecule

REPORT_DIR = Path("static") / "reports"


def report_path_for_id(report_id: int) -> Path:
    """Return the deterministic PDF path for a report ID."""

    return REPORT_DIR / f"molgenix_report_{report_id}.pdf"


def build_report_pdf(
    output_path: Path,
    session: DiscoverySession,
    summary: str,
    molecules: list[tuple[Molecule, int]],
    druggability_score: float,
) -> None:
    """Build a three-page simulated research report PDF."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="Disclaimer", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#8A1F11")))
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    story: list[object] = []
    _build_cover_page(story, styles, session, summary, druggability_score)
    story.append(PageBreak())
    _build_candidate_page(story, styles, molecules)
    story.append(PageBreak())
    _build_admet_page(story, styles, molecules)
    document.build(story)


def _build_cover_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    session: DiscoverySession,
    summary: str,
    druggability_score: float,
) -> None:
    """Append cover, executive summary, and score content."""

    target_name = session.target.name if session.target else "No target identified"
    story.append(Paragraph("MolGenix Simulated Discovery Report", styles["Title"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(f"Session: {session.name}", styles["Heading2"]))
    story.append(Paragraph(f"Identified target: {target_name}", styles["BodyText"]))
    story.append(Paragraph(f"Original query: {session.query}", styles["BodyText"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    for paragraph in summary.split("\n\n"):
        story.append(Paragraph(paragraph, styles["BodyText"]))
        story.append(Spacer(1, 0.12 * inch))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Druggability score: {druggability_score:.1f} / 100", styles["Heading2"]))
    story.append(
        Paragraph(
            "This score is a simulated composite of mock docking, QED, Lipinski, and seeded safety flags.",
            styles["BodyText"],
        )
    )


def _build_candidate_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append ranked table and structure diagrams."""

    story.append(Paragraph("Ranked Candidate Table", styles["Heading1"]))
    table_data: list[list[object]] = [["Rank", "Molecule", "Docking", "QED", "ADMET", "Flag"]]
    for molecule, rank in molecules:
        admet_status = "Problematic" if admet_predictor.is_problematic(molecule) else "Acceptable"
        table_data.append(
            [
                rank,
                molecule.name,
                f"{molecule.docking_score:.1f}",
                f"{_qed_score(molecule):.2f}",
                admet_status,
                "Toxic" if molecule.is_toxic else "Review" if admet_status == "Problematic" else "Clear",
            ]
        )

    table = Table(table_data, colWidths=[0.45 * inch, 1.45 * inch, 0.75 * inch, 0.55 * inch, 1.1 * inch, 0.75 * inch])
    table.setStyle(_table_style())
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("Molecule Structure Diagrams", styles["Heading2"]))

    image_cells: list[list[object]] = []
    row: list[object] = []
    for molecule, rank in molecules[:6]:
        caption = Paragraph(f"Rank {rank}: {molecule.name}", styles["Small"])
        image_path = Path(molecule.image_path or "")
        cell: list[object] = [caption]
        if image_path.exists():
            cell.append(Image(str(image_path), width=1.7 * inch, height=1.25 * inch))
        else:
            cell.append(Paragraph("Image unavailable", styles["Small"]))
        row.append(cell)
        if len(row) == 3:
            image_cells.append(row)
            row = []
    if row:
        image_cells.append(row)

    image_table = Table(image_cells, colWidths=[2.1 * inch, 2.1 * inch, 2.1 * inch])
    image_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(image_table)


def _build_admet_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append ADMET detail, methodology, and disclaimer."""

    story.append(Paragraph("ADMET Detail", styles["Heading1"]))
    for molecule, rank in molecules[:3]:
        story.append(Paragraph(f"Rank {rank}: {molecule.name}", styles["Heading3"]))
        table_data = [["Metric", "Value", "Signal"]]
        for metric in admet_predictor.evaluate(molecule):
            table_data.append([metric.label, str(metric.value), metric.status])
        table = Table(table_data, colWidths=[1.7 * inch, 2.0 * inch, 1.0 * inch])
        table.setStyle(_table_style())
        story.append(table)
        story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Methodology", styles["Heading2"]))
    story.append(
        Paragraph(
            "Molecules are retrieved from the local pre-seeded MolGenix demo database. Structures are rendered from seeded SMILES with RDKit. Docking, ADMET, QED ranking, and druggability values are simulated prototype signals and are not experimental or validated computational results.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.16 * inch))
    story.append(Paragraph("Disclaimer", styles["Heading2"]))
    story.append(
        Paragraph(
            "Demo-only scientific report. This PDF must not be used for clinical, diagnostic, investment, regulatory, or laboratory decision-making without independent expert validation.",
            styles["Disclaimer"],
        )
    )


def _table_style() -> TableStyle:
    """Return a consistent table style for report pages."""

    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B9C2CC")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
        ]
    )


def _qed_score(molecule: Molecule) -> float:
    """Calculate QED from the seeded SMILES for PDF display."""

    mol = Chem.MolFromSmiles(molecule.smiles)
    if mol is None:
        return 0.0
    return float(QED.qed(mol))
