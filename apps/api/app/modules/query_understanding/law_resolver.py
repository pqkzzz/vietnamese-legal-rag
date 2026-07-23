"""Resolve legal document mentions in user queries."""

from __future__ import annotations

from difflib import SequenceMatcher

from app.modules.query_understanding.law_registry import LawRegistry, LawRegistryEntry
from app.modules.query_understanding.models import ResolvedLaw
from app.modules.query_understanding.normalizer import fold_text, normalize_query

HIGH_CONFIDENCE = 0.9


class LawResolver:
    """Rule-based law resolver using exact, substring, and conservative fuzzy matching."""

    def __init__(self, registry: LawRegistry | None = None) -> None:
        self.registry = registry or LawRegistry.load()

    def resolve(self, query: str) -> tuple[list[ResolvedLaw], list[str], bool]:
        normalized_query = normalize_query(query)
        folded_query = fold_text(normalized_query)
        candidates: dict[str, ResolvedLaw] = {}
        warnings: list[str] = []

        for entry in self.registry.entries:
            if entry.document_number and fold_text(entry.document_number) in folded_query:
                self._add(candidates, entry, entry.document_number, "document_number_exact", 1.0)
            for text, match_type, confidence in self._entry_texts(entry):
                folded_text = fold_text(text)
                if folded_query == folded_text:
                    self._add(candidates, entry, text, match_type + "_exact", confidence)
                elif self._allow_substring_match(folded_query, folded_text, match_type):
                    self._add(candidates, entry, text, match_type + "_substring", min(confidence, 0.95))

        if not candidates:
            fuzzy = self._fuzzy_match(folded_query)
            if fuzzy is not None:
                entry, matched_text, score = fuzzy
                self._add(candidates, entry, matched_text, "fuzzy", score)

        results = sorted(candidates.values(), key=lambda item: (-item.confidence, item.law_id))
        needs_clarification = False
        if len(results) > 1 and results[0].confidence - results[1].confidence < 0.05:
            needs_clarification = True
            warnings.append("Ambiguous law mention: multiple registry entries have similar confidence.")
        return results, warnings, needs_clarification

    def _entry_texts(self, entry: LawRegistryEntry) -> list[tuple[str, str, float]]:
        texts: list[tuple[str, str, float]] = [(entry.official_title, "official_title", 1.0)]
        if entry.full_name:
            texts.append((entry.full_name, "full_name", 1.0))
        for alias in entry.aliases:
            texts.append((alias, "alias", 0.98))
        for abbreviation in entry.abbreviations:
            texts.append((abbreviation, "abbreviation", 0.98))
        return texts

    def _allow_substring_match(self, folded_query: str, folded_text: str, match_type: str) -> bool:
        if len(folded_text) < 4 or folded_text not in folded_query:
            return False
        if match_type in {"official_title", "full_name"}:
            return len(folded_text) >= 8
        if match_type == "abbreviation":
            return len(folded_text) >= 4
        if any(char.isdigit() for char in folded_text):
            return True
        if folded_text.startswith(("luat ", "bo luat ")):
            return True
        return False

    def _fuzzy_match(self, folded_query: str) -> tuple[LawRegistryEntry, str, float] | None:
        best: tuple[LawRegistryEntry, str, float] | None = None
        second_score = 0.0
        for entry in self.registry.entries:
            for text, match_type, _ in self._entry_texts(entry):
                folded_text = fold_text(text)
                if match_type == "alias" and not folded_text.startswith(("luat ", "bo luat ")):
                    continue
                if len(folded_text) < 8:
                    continue
                score = SequenceMatcher(None, folded_query, folded_text).ratio()
                if score > (best[2] if best else 0.0):
                    second_score = best[2] if best else 0.0
                    best = (entry, text, score)
                elif score > second_score:
                    second_score = score
        if best is None:
            return None
        if best[2] >= 0.86 and best[2] - second_score >= 0.05:
            return best
        return None

    def _add(
        self,
        candidates: dict[str, ResolvedLaw],
        entry: LawRegistryEntry,
        matched_text: str,
        match_type: str,
        confidence: float,
    ) -> None:
        current = candidates.get(entry.law_id)
        result = ResolvedLaw(
            law_id=entry.law_id,
            official_title=entry.official_title,
            matched_text=matched_text,
            match_type=match_type,
            confidence=round(confidence, 3),
        )
        if current is None or result.confidence > current.confidence:
            candidates[entry.law_id] = result
