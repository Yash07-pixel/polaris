"""AI-assisted simulated research report generation service."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.ml.admet_predictor import admet_predictor
from app.models import DiscoveryReport, DiscoverySession, Molecule
from app.routers.molecules import _qed_score, _rank_molecules
from app.utils.pdf_builder import build_report_pdf, report_path_for_id


class ReportService:
    """Generate Gemini or fallback summaries and build downloadable PDFs."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Create a report service with configured Gemini settings."""

        self.settings = settings or get_settings()

    def generate_report(self, db: Session, session_id: int) -> DiscoveryReport:
        """Generate a simulated research report for a completed discovery session."""

        session = db.scalar(
            select(DiscoverySession)
            .options(joinedload(DiscoverySession.target))
            .where(DiscoverySession.id == session_id)
        )
        if session is None:
            raise ValueError("Session not found.")
        if session.target_id is None or session.status != "COMPLETE":
            raise ValueError("Reports can only be generated for completed sessions with an identified target.")

        molecules = db.scalars(
            select(Molecule)
            .options(joinedload(Molecule.target))
            .where(Molecule.target_id == session.target_id)
        ).all()
        ranked = _rank_molecules(molecules, "rank")
        top_candidates = ranked[:3]
        druggability_score = self._druggability_score(top_candidates)
        summary = self._generate_summary(session, top_candidates, druggability_score)
        recommendation = "Recommend orthogonal assay confirmation, preliminary selectivity screening, and wet-lab validation before any further interpretation."

        report = DiscoveryReport(
            session_id=session.id,
            title=f"MolGenix Report - {session.target.name}",
            summary=summary,
            recommendation=recommendation,
            druggability_score=druggability_score,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        pdf_path = report_path_for_id(report.id)
        build_report_pdf(pdf_path, session, summary, ranked, druggability_score)
        report.pdf_path = pdf_path.as_posix()
        db.commit()
        db.refresh(report)
        return report

    def _generate_summary(
        self,
        session: DiscoverySession,
        top_candidates: list[tuple[Molecule, int]],
        druggability_score: float,
    ) -> str:
        """Generate a three-paragraph scientific summary using Gemini or fallback text."""

        if not self.settings.GEMINI_API_KEY:
            return self._fallback_summary(session, top_candidates, druggability_score)

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(self.settings.GEMINI_MODEL)
            response = model.generate_content(
                self._build_prompt(session, top_candidates, druggability_score),
                generation_config={"temperature": 0.2},
            )
            summary = response.text.strip()
            if not self._summary_meets_requirements(summary):
                return self._fallback_summary(session, top_candidates, druggability_score)
            return summary
        except Exception:
            return self._fallback_summary(session, top_candidates, druggability_score)

    def _build_prompt(
        self,
        session: DiscoverySession,
        top_candidates: list[tuple[Molecule, int]],
        druggability_score: float,
    ) -> str:
        """Build the constrained Gemini prompt for demo-only report prose."""

        candidate_payload = [
            {
                "rank": rank,
                "name": molecule.name,
                "docking_score": molecule.docking_score,
                "qed_score": _qed_score(molecule),
                "admet_problematic": admet_predictor.is_problematic(molecule),
                "herg_risk": molecule.herg_risk,
                "ames_toxicity": molecule.ames_toxicity,
                "hepatotoxicity": molecule.hepatotoxicity,
            }
            for molecule, rank in top_candidates
        ]
        return (
            "Write a demo-only medicinal chemistry executive summary for MolGenix.\n"
            "Requirements: exactly 3 paragraphs, 150-200 words total, professional medicinal chemistry tone, "
            "mention top candidates, docking scores, ADMET findings, and recommend wet-lab validation. "
            "Do not claim real biomedical validity. Do not introduce molecules not listed below.\n\n"
            f"target: {session.target.name if session.target else 'unknown'}\n"
            f"query: {session.query}\n"
            f"druggability_score: {druggability_score:.1f}/100\n"
            f"top_candidates: {json.dumps(candidate_payload, ensure_ascii=True)}"
        )

    def _fallback_summary(
        self,
        session: DiscoverySession,
        top_candidates: list[tuple[Molecule, int]],
        druggability_score: float,
    ) -> str:
        """Return deterministic fallback prose satisfying the report requirements."""

        target_name = session.target.name if session.target else "the matched demo target"
        candidate_text = ", ".join(
            f"{molecule.name} (rank {rank}, docking {molecule.docking_score:.1f} kcal/mol)"
            for molecule, rank in top_candidates
        )
        best = top_candidates[0][0]
        admet_notes = [
            f"{molecule.name}: hERG {molecule.herg_risk}, Ames {'positive' if molecule.ames_toxicity else 'negative'}, liver {'flagged' if molecule.hepatotoxicity else 'not flagged'}"
            for molecule, _ in top_candidates
        ]

        return (
            f"This simulated MolGenix analysis maps the query to {target_name} and ranks only pre-seeded mock candidates. "
            f"The leading candidates are {candidate_text}. The composite demo druggability score is {druggability_score:.1f}/100, driven by negative docking scores, seeded physicochemical properties, and safety flags rather than real experimental evidence.\n\n"
            f"{best.name} is the top-ranked prototype molecule and combines the strongest local rank with a docking score of {best.docking_score:.1f} kcal/mol. "
            f"ADMET review remains cautious: {'; '.join(admet_notes)}. Toxic or problematic molecules are retained in the report to make filtering decisions transparent, not to recommend advancement.\n\n"
            "Overall, this report supports a demo triage narrative only. The candidate set should be treated as a simulated medicinal chemistry exercise, with any apparent binding or ADMET advantage requiring independent synthesis review, orthogonal assays, selectivity profiling, and wet-lab validation before scientific or operational conclusions are drawn."
        )

    @staticmethod
    def _summary_meets_requirements(summary: str) -> bool:
        """Return whether generated summary shape matches Phase 4 constraints."""

        paragraphs = [part for part in summary.split("\n\n") if part.strip()]
        word_count = len(summary.split())
        return len(paragraphs) == 3 and 150 <= word_count <= 200

    @staticmethod
    def _druggability_score(top_candidates: list[tuple[Molecule, int]]) -> float:
        """Compute a simulated report-level druggability score."""

        if not top_candidates:
            return 0.0
        scores: list[float] = []
        for molecule, _ in top_candidates:
            docking_component = min(45.0, -molecule.docking_score * 4.5)
            qed_component = _qed_score(molecule) * 25.0
            admet_component = 30.0 if not admet_predictor.is_problematic(molecule) else 15.0
            scores.append(docking_component + qed_component + admet_component)
        return round(sum(scores) / len(scores), 1)


def ensure_report_file_exists(report: DiscoveryReport) -> Path:
    """Return the report PDF path or raise when the file is unavailable."""

    if not report.pdf_path:
        raise FileNotFoundError("Report PDF path is missing.")
    path = Path(report.pdf_path)
    if not path.exists():
        raise FileNotFoundError("Report PDF file is missing.")
    return path
