"""NLP target identification service for the controlled MolGenix demo."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.curated_data.targets import CURATED_TARGETS


@dataclass(frozen=True)
class TargetIdentificationResult:
    """Structured result for NLP target identification."""

    target_key: str | None
    confidence_score: float
    source: str
    reason: str


class NLPService:
    """Identify one of the five predefined curated targets from user text."""

    keyword_map: dict[str, tuple[str, ...]] = {
        "egfr": (
            "egfr",
            "epidermal growth factor",
            "lung cancer",
            "non-small cell",
            "nsclc",
            "erbb1",
            "tyrosine kinase",
        ),
        "jak2": (
            "jak2",
            "janus kinase",
            "myeloproliferative",
            "polycythemia",
            "myelofibrosis",
            "thrombocythemia",
            "cytokine",
        ),
        "bace1": (
            "bace1",
            "beta-secretase",
            "beta secretase",
            "alzheimer",
            "amyloid",
            "neurodegenerative",
            "cns",
        ),
        "tnf": (
            "tnf",
            "tumor necrosis factor",
            "tumour necrosis factor",
            "autoimmune",
            "inflammation",
            "rheumatoid",
            "crohn",
            "psoriasis",
        ),
        "hiv_integrase": (
            "hiv integrase",
            "integrase",
            "hiv",
            "viral strand transfer",
            "strand transfer",
            "antiviral",
            "retroviral",
        ),
    }

    def __init__(self, settings: Settings | None = None) -> None:
        """Create an NLP service using configured Gemini settings."""

        self.settings = settings or get_settings()

    def identify_target(self, query: str) -> TargetIdentificationResult:
        """Identify a predefined target using Gemini with keyword fallback."""

        gemini_result = self._identify_with_gemini(query)
        if gemini_result.target_key is not None:
            return gemini_result
        return self._identify_with_keywords(query, fallback_reason=gemini_result.reason)

    def _identify_with_gemini(self, query: str) -> TargetIdentificationResult:
        """Ask Gemini to classify the query against only available demo targets."""

        if not self.settings.GEMINI_API_KEY:
            return TargetIdentificationResult(None, 0.0, "fallback", "Gemini API key is not configured.")

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(self.settings.GEMINI_MODEL)
            response = model.generate_content(
                self._build_prompt(query),
                generation_config={"response_mime_type": "application/json", "temperature": 0.0},
            )
            payload = self._parse_json_response(response.text)
            target_key = payload.get("target_key")
            confidence = float(payload.get("confidence_score", 0.0))
            reason = str(payload.get("reason", "Gemini classification completed."))

            if target_key is None:
                return TargetIdentificationResult(None, confidence, "gemini", reason)
            if target_key not in self.available_target_keys:
                return TargetIdentificationResult(None, 0.0, "fallback", "Gemini returned an unknown target.")
            return TargetIdentificationResult(
                target_key=target_key,
                confidence_score=round(max(0.0, min(confidence, 1.0)), 2),
                source="gemini",
                reason=reason,
            )
        except Exception as exc:
            return TargetIdentificationResult(None, 0.0, "fallback", f"Gemini failed: {exc}")

    def _identify_with_keywords(self, query: str, fallback_reason: str) -> TargetIdentificationResult:
        """Match the query with deterministic keywords for all demo targets."""

        normalized_query = self._normalize(query)
        scores: dict[str, int] = {}
        for target_key, keywords in self.keyword_map.items():
            scores[target_key] = sum(1 for keyword in keywords if self._normalize(keyword) in normalized_query)

        best_key, best_score = max(scores.items(), key=lambda item: item[1])
        if best_score == 0:
            return TargetIdentificationResult(None, 0.0, "fallback", "No demo target keywords matched.")

        confidence = round(min(0.95, 0.55 + (best_score * 0.1)), 2)
        return TargetIdentificationResult(
            target_key=best_key,
            confidence_score=confidence,
            source="fallback",
            reason=f"{fallback_reason} Keyword fallback matched {best_score} signal(s).",
        )

    def _build_prompt(self, query: str) -> str:
        """Build a constrained Gemini prompt that cannot introduce new targets."""

        available_targets = [
            {
                "target_key": target["key"],
                "name": target["name"],
                "gene_symbol": target["gene_symbol"],
                "disease_area": target["disease_area"],
                "mechanism": target["mechanism"],
            }
            for target in CURATED_TARGETS
        ]
        return (
            "You are classifying a user query for a controlled drug-discovery demo.\n"
            "Use only the available_targets list. Never invent or rename targets.\n"
            "Return strict JSON only with keys: target_key, confidence_score, reason.\n"
            "target_key must be one of the provided target_key values, or null if no target matches.\n"
            "confidence_score must be a number from 0 to 1.\n\n"
            f"available_targets: {json.dumps(available_targets, ensure_ascii=True)}\n"
            f"user_query: {json.dumps(query, ensure_ascii=True)}"
        )

    @property
    def available_target_keys(self) -> set[str]:
        """Return the allowed curated target keys."""

        return {target["key"] for target in CURATED_TARGETS}

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        """Parse Gemini JSON, tolerating fenced JSON blocks."""

        cleaned = text.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            cleaned = fenced.group(1).strip()
        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise ValueError("Gemini response JSON must be an object.")
        return payload

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for keyword matching."""

        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
