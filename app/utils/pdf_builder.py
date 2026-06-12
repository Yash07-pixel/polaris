"""ReportLab PDF builder for MolGenix research-style reports."""

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rdkit import Chem
from rdkit.Chem import QED

from app.ml.admet_predictor import admet_predictor
from app.models import DiscoverySession, Molecule

REPORT_DIR = Path("static") / "reports"
NAVY = colors.HexColor("#0B1F33")
TEAL = colors.HexColor("#2E8077")
GOLD = colors.HexColor("#B9964D")
LIGHT_BG = colors.HexColor("#F7F9F8")
BORDER = colors.HexColor("#D8E1DE")
TEXT = colors.HexColor("#182320")
MUTED = colors.HexColor("#66736F")
RED = colors.HexColor("#B9505B")
GREEN = colors.HexColor("#3E8561")
AMBER = colors.HexColor("#B98722")
CARD_WIDTH = 3.08 * inch
CARD_HEIGHT = 3.46 * inch
IMAGE_BOX_WIDTH = 2.68 * inch
IMAGE_BOX_HEIGHT = 1.9 * inch
METRIC_WIDTH = 2.58 * inch


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
    """Build a publication-style computational screening report."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    styles = _build_styles()
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="MolGenix Computational Screening Report",
        author="MolGenix",
    )

    story: list[object] = []
    _build_cover_page(story, styles, session, summary, druggability_score, molecules)
    story.append(PageBreak())
    _build_results_page(story, styles, molecules)
    story.append(PageBreak())
    _build_structure_pages(story, styles, molecules)
    story.append(PageBreak())
    _build_admet_methodology_page(story, styles, molecules)
    document.build(story)


def _build_styles() -> dict[str, ParagraphStyle]:
    """Create report-specific typography styles."""

    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=NAVY,
            spaceAfter=14,
        ),
        "kicker": ParagraphStyle(
            "Kicker",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=TEAL,
            uppercase=True,
            spaceAfter=5,
        ),
        "h1": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "h2": ParagraphStyle(
            "SubHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=TEXT,
            spaceAfter=6,
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.5,
            textColor=MUTED,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=TEXT,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=10.5,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=5,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=8.6,
            textColor=colors.white,
            wordWrap="CJK",
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=9.2,
            textColor=TEXT,
            wordWrap="CJK",
        ),
        "table_label": ParagraphStyle(
            "TableLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.4,
            leading=9.2,
            textColor=MUTED,
            wordWrap="CJK",
        ),
    }


def _build_cover_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    session: DiscoverySession,
    summary: str,
    druggability_score: float,
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append cover page, executive summary, and screening highlights."""

    target_name = session.target.name if session.target else "No target identified"
    top = molecules[:3]
    story.append(Paragraph("MOLGENIX COMPUTATIONAL SCREENING BRIEF", styles["kicker"]))
    story.append(Paragraph("Computational Medicinal Chemistry Report", styles["title"]))
    story.append(_info_table(session, target_name, druggability_score, len(molecules), styles))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("1. Executive Summary", styles["h1"]))
    for paragraph in summary.split("\n\n"):
        story.append(Paragraph(paragraph, styles["body"]))
    story.append(Spacer(1, 0.08 * inch))

    story.append(Paragraph("Key Findings", styles["h2"]))
    finding_rows = [
        ["Finding", "Interpretation"],
        [
            "Target mapping",
            f"The query was mapped to {target_name}; all downstream results are constrained to the local curated benchmark dataset.",
        ],
        [
            "Top candidates",
            ", ".join(f"{m.name} ({m.docking_score:.1f} kcal/mol)" for m, _ in top),
        ],
        [
            "Developability",
            _screening_interpretation(top),
        ],
    ]
    table = _research_table(finding_rows, [1.35 * inch, 5.15 * inch], styles, header_bg=NAVY)
    story.append(table)
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        Paragraph(
            "This report is a prototype decision-support artifact for research review. It is structured to expose ranking logic, ADMET liabilities, and follow-up hypotheses without implying experimental validity.",
            styles["muted"],
        )
    )


def _info_table(
    session: DiscoverySession,
    target_name: str,
    druggability_score: float,
    molecule_count: int,
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Return a compact metadata table for the cover page."""

    data = [
        ["Target", target_name, "Druggability", f"{druggability_score:.1f} / 100"],
        ["Query", session.query, "Candidates", str(molecule_count)],
        ["Status", session.status, "Report Type", "Computational screening brief"],
    ]
    table = Table(
        [
            [
                _pdf_cell(row[0], styles, label=True),
                _pdf_cell(row[1], styles),
                _pdf_cell(row[2], styles, label=True),
                _pdf_cell(row[3], styles),
            ]
            for row in data
        ],
        colWidths=[0.85 * inch, 3.05 * inch, 1.05 * inch, 1.55 * inch],
        splitByRow=1,
    )
    table.setStyle(_metadata_table_style())
    return table


def _build_results_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append ranked results table and interpretation."""

    story.append(Paragraph("2. Ranked Candidate Results", styles["h1"]))
    story.append(
        Paragraph(
            "Candidates are ordered by a prototype composite ranking that weights docking-score signals, RDKit QED, and curated safety-style flags. Toxic or problematic molecules remain visible to preserve review transparency.",
            styles["body"],
        )
    )

    table_data: list[list[object]] = [["Rank", "Molecule", "Docking", "QED", "Lipinski", "Safety", "Interpretation"]]
    for molecule, rank in molecules:
        safety = _safety_label(molecule)
        table_data.append(
            [
                str(rank),
                molecule.name,
                f"{molecule.docking_score:.1f}",
                f"{_qed_score(molecule):.2f}",
                "Pass" if admet_predictor.passes_lipinski(molecule) else "Fail",
                safety,
                _candidate_interpretation(molecule),
            ]
        )

    table = _research_table(
        table_data,
        [0.42 * inch, 1.0 * inch, 0.62 * inch, 0.46 * inch, 0.62 * inch, 0.74 * inch, 2.63 * inch],
        styles,
        header_bg=NAVY,
        highlight_top=True,
    )
    story.append(table)
    story.append(Spacer(1, 0.14 * inch))
    story.append(Paragraph("Screening Interpretation", styles["h2"]))
    story.append(
        Paragraph(
            _ranking_commentary(molecules),
            styles["body"],
        )
    )


def _build_structure_pages(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append large publication-style compound structure panels."""

    story.append(Paragraph("3. Compound Structure Panels", styles["h1"]))
    story.append(
        Paragraph(
            "The highest-ranked compounds are shown as enlarged RDKit-rendered structure panels to improve medicinal chemistry readability and rapid visual inspection.",
            styles["body"],
        )
    )
    candidates = molecules[:6]
    for index in range(0, len(candidates), 2):
        row_candidates = candidates[index : index + 2]
        cards: list[object] = [_compound_panel(molecule, rank, styles) for molecule, rank in row_candidates]
        if len(cards) == 1:
            cards.append("")

        row_table = Table(
            [cards],
            colWidths=[CARD_WIDTH, CARD_WIDTH],
            rowHeights=[CARD_HEIGHT],
            splitByRow=1,
        )
        row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(KeepTogether([row_table]))
        story.append(Spacer(1, 0.14 * inch))


def _compound_panel(molecule: Molecule, rank: int, styles: dict[str, ParagraphStyle]) -> list[object]:
    """Return a compound panel with larger structure image and key metrics."""

    image_path = Path(molecule.image_path or "")
    image_flowable: object
    if image_path.exists():
        image_flowable = _contained_image(image_path, IMAGE_BOX_WIDTH, IMAGE_BOX_HEIGHT)
    else:
        image_flowable = Paragraph("Structure image unavailable", styles["muted"])

    image_box = Table([[image_flowable]], colWidths=[IMAGE_BOX_WIDTH], rowHeights=[IMAGE_BOX_HEIGHT])
    image_box.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    metric_table = Table(
        [
            [_pdf_cell("Docking", styles, label=True), _pdf_cell(f"{molecule.docking_score:.1f} kcal/mol", styles)],
            [_pdf_cell("QED", styles, label=True), _pdf_cell(f"{_qed_score(molecule):.2f}", styles)],
            [_pdf_cell("Status", styles, label=True), _pdf_cell(_safety_label(molecule), styles)],
        ],
        colWidths=[0.72 * inch, METRIC_WIDTH - 0.72 * inch],
        rowHeights=[0.22 * inch, 0.22 * inch, 0.22 * inch],
    )
    metric_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("FONTSIZE", (0, 0), (-1, -1), 7.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    card = Table(
        [
            [Paragraph(f"Rank {rank}  |  {molecule.name}", styles["caption"])],
            [image_box],
            [metric_table],
        ],
        colWidths=[CARD_WIDTH - 0.26 * inch],
        rowHeights=[0.34 * inch, 2.12 * inch, 0.84 * inch],
    )
    card.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 1), (0, 1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 1), (0, 1), 0),
                ("BOTTOMPADDING", (0, 1), (0, 1), 0),
                ("TOPPADDING", (0, 2), (0, 2), 6),
            ]
        )
    )
    return [card]


def _contained_image(image_path: Path, max_width: float, max_height: float) -> Image:
    """Return a ReportLab image scaled to fit within fixed bounds."""

    image = Image(str(image_path))
    width_scale = max_width / image.imageWidth
    height_scale = max_height / image.imageHeight
    scale = min(width_scale, height_scale)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    return image


def _build_admet_methodology_page(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    molecules: list[tuple[Molecule, int]],
) -> None:
    """Append ADMET interpretation and methodology."""

    story.append(Paragraph("4. ADMET and Developability Interpretation", styles["h1"]))
    top = molecules[:3]
    for molecule, rank in top:
        story.append(KeepTogether(_admet_candidate_block(molecule, rank, styles)))

    story.append(Paragraph("Comparative ADMET Notes", styles["h2"]))
    story.append(
        Paragraph(
            _admet_commentary(top),
            styles["body"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    story.append(Paragraph("5. Methodology and Simulation Scope", styles["h1"]))
    methodology = (
        "MolGenix maps the user query to one predefined research target using Gemini when configured, with a deterministic keyword fallback for demo reliability. "
        "Candidate molecules are retrieved exclusively from the local SQLite seed database; no external pharmaceutical databases are queried and no new molecules are generated. "
        "RDKit is used to parse curated SMILES, calculate QED, and render 2D structures. Docking-score values, ADMET-style signals, toxicity flags, and druggability scores are prototype screening features designed to support a transparent product demonstration."
    )
    story.append(Paragraph(methodology, styles["body"]))
    story.append(
        Paragraph(
            "Ranking assumptions: more negative docking-score values are treated as stronger prototype binding signals, QED is used as a drug-likeness proxy, and curated toxicity or Lipinski liabilities reduce the composite interpretation. These assumptions are not validated computational chemistry methods.",
            styles["muted"],
        )
    )


def _admet_candidate_block(molecule: Molecule, rank: int, styles: dict[str, ParagraphStyle]) -> list[object]:
    """Return a compact ADMET block for one candidate."""

    table_data = [["Metric", "Value", "Signal", "Interpretation"]]
    for metric in admet_predictor.evaluate(molecule):
        table_data.append([metric.label, str(metric.value), metric.status, _metric_interpretation(metric.label, metric.status)])
    table = _research_table(table_data, [1.1 * inch, 1.0 * inch, 0.65 * inch, 3.55 * inch], styles, header_bg=TEAL)
    return [
        Paragraph(f"Rank {rank}: {molecule.name}", styles["h2"]),
        table,
        Spacer(1, 0.09 * inch),
    ]


def _research_table(
    rows: list[list[object]],
    col_widths: list[float],
    styles: dict[str, ParagraphStyle],
    header_bg: colors.Color = NAVY,
    highlight_top: bool = False,
) -> Table:
    """Return a wrapping, constrained table for PDF report content."""

    wrapped_rows = [
        [
            _pdf_cell(cell, styles, header=row_index == 0)
            for cell in row
        ]
        for row_index, row in enumerate(rows)
    ]
    table = Table(wrapped_rows, colWidths=col_widths, repeatRows=1, splitByRow=1)
    table.setStyle(_table_style(header_bg=header_bg, highlight_top=highlight_top))
    return table


def _pdf_cell(
    value: object,
    styles: dict[str, ParagraphStyle],
    *,
    header: bool = False,
    label: bool = False,
) -> Paragraph:
    """Return a paragraph table cell with safe wrapping and escaping."""

    style_name = "table_header" if header else "table_label" if label else "table_cell"
    text = escape(str(value))
    return Paragraph(text, styles[style_name])


def _metadata_table_style() -> TableStyle:
    """Return a compact style for the cover metadata table."""

    return TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, colors.white]),
        ]
    )


def _table_style(header_bg: colors.Color = NAVY, highlight_top: bool = False) -> TableStyle:
    """Return a consistent publication-style table style."""

    commands: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("LEADING", (0, 0), (-1, -1), 9.2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ]
    if highlight_top:
        commands.extend(
            [
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFF8E6")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ]
        )
    return TableStyle(commands)


def _qed_score(molecule: Molecule) -> float:
    """Calculate QED from the curated SMILES for PDF display."""

    mol = Chem.MolFromSmiles(molecule.smiles)
    if mol is None:
        return 0.0
    return float(QED.qed(mol))


def _safety_label(molecule: Molecule) -> str:
    """Return a concise safety label for report tables."""

    if molecule.is_toxic:
        return "Toxic flag"
    if admet_predictor.is_problematic(molecule):
        return "Review"
    return "Balanced"


def _candidate_interpretation(molecule: Molecule) -> str:
    """Return a concise medicinal chemistry interpretation for a candidate."""

    if molecule.is_toxic:
        return "Retained for transparency; curated toxicity flag limits developability."
    if molecule.herg_risk.lower() == "high":
        return "Binding signal requires cardiac liability review."
    if not admet_predictor.passes_lipinski(molecule):
        return "Physicochemical profile requires optimization."
    return "Good prototype balance of binding and ADMET-style signals."


def _screening_interpretation(top: list[tuple[Molecule, int]]) -> str:
    """Summarize top-candidate screening profile."""

    clean = [molecule.name for molecule, _ in top if not admet_predictor.is_problematic(molecule)]
    if clean:
        return f"{', '.join(clean)} show the cleanest prototype developability balance among the top-ranked candidates."
    return "Top-ranked candidates retain notable prototype liabilities and should be treated as optimization starting points only."


def _ranking_commentary(molecules: list[tuple[Molecule, int]]) -> str:
    """Return concise commentary following the ranking table."""

    top = molecules[0][0]
    toxic_count = sum(1 for molecule, _ in molecules if molecule.is_toxic)
    clean_count = sum(1 for molecule, _ in molecules if not admet_predictor.is_problematic(molecule))
    return (
        f"{top.name} leads the prototype ranking with a docking score of {top.docking_score:.1f} kcal/mol and QED of {_qed_score(top):.2f}. "
        f"{clean_count} of {len(molecules)} candidates show no curated safety or Lipinski problem flags, while {toxic_count} toxic candidates remain visible for risk tracking. "
        "The table should be read as a prioritization aid for demo triage, not as evidence of biological activity."
    )


def _admet_commentary(top: list[tuple[Molecule, int]]) -> str:
    """Return interpretation-driven ADMET commentary for top candidates."""

    names = ", ".join(molecule.name for molecule, _ in top)
    hERG = [molecule.name for molecule, _ in top if molecule.herg_risk.lower() != "low"]
    liver = [molecule.name for molecule, _ in top if molecule.hepatotoxicity]
    return (
        f"The top-candidate ADMET review focuses on {names}. hERG risk is treated as a cardiac safety triage signal; "
        f"{', '.join(hERG) if hERG else 'none of the top candidates'} require additional ion-channel attention in this prototype screen. "
        f"Hepatotoxicity flags are {'present in ' + ', '.join(liver) if liver else 'not present among the top candidates'}, while solubility and bioavailability scores frame formulation and exposure risk. "
        "In a real program, these signals would motivate analog design, orthogonal assay confirmation, and exposure optimization."
    )


def _metric_interpretation(label: str, status: str) -> str:
    """Return a readable interpretation for an ADMET metric traffic light."""

    if label == "hERG Risk":
        return "Cardiac liability watch item." if status != "Green" else "Low curated cardiac concern."
    if label == "Hepatotoxicity":
        return "Liver safety flag limits progression." if status == "Red" else "No curated liver flag."
    if label == "Ames Toxicity":
        return "Mutagenicity flag requires deprioritization." if status == "Red" else "No curated mutagenicity flag."
    if label == "Solubility":
        return "May affect formulation and exposure." if status != "Green" else "Favorable prototype solubility."
    if label == "Bioavailability":
        return "Exposure may need optimization." if status != "Green" else "Favorable prototype oral exposure."
    if label == "Lipinski":
        return "Drug-likeness concern." if status == "Red" else "Rule-of-five profile acceptable."
    return "Prototype developability signal."
