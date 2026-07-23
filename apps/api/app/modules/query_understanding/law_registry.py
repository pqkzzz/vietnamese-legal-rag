"""Load and validate the legal document registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.modules.query_understanding.normalizer import fold_text, normalize_query

PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "metadata" / "law_registry.json"


@dataclass(frozen=True)
class LawRegistryEntry:
    law_id: str
    official_title: str
    full_name: str | None
    document_number: str | None
    document_type: str | None
    issued_year: int | None
    aliases: list[str]
    abbreviations: list[str]
    domain: str | None


class LawRegistry:
    """In-memory registry with validated legal document aliases."""

    def __init__(self, entries: list[LawRegistryEntry]) -> None:
        self.entries = entries
        self.by_law_id = {entry.law_id: entry for entry in entries}
        self.by_lookup: dict[str, list[LawRegistryEntry]] = {}
        for entry in entries:
            values = [entry.law_id, entry.official_title]
            if entry.full_name:
                values.append(entry.full_name)
            if entry.document_number:
                values.append(entry.document_number)
            values.extend(entry.aliases)
            values.extend(entry.abbreviations)
            for value in values:
                key = _lookup_key(value)
                self.by_lookup.setdefault(key, [])
                if entry not in self.by_lookup[key]:
                    self.by_lookup[key].append(entry)

    @classmethod
    def load(cls, path: Path = DEFAULT_REGISTRY_PATH) -> "LawRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("laws"), list):
            raise ValueError("law_registry.json must contain a laws list")
        entries: list[LawRegistryEntry] = []
        seen_law_ids: set[str] = set()
        for item in data["laws"]:
            if not isinstance(item, dict):
                raise ValueError("Each law registry item must be an object")
            law_id = _required_str(item, "law_id")
            if law_id in seen_law_ids:
                raise ValueError(f"Duplicate law_id in registry: {law_id}")
            seen_law_ids.add(law_id)
            aliases = item.get("aliases") or []
            abbreviations = item.get("abbreviations") or []
            if not isinstance(aliases, list) or not all(isinstance(alias, str) for alias in aliases):
                raise ValueError(f"Aliases for {law_id} must be a list of strings")
            if not isinstance(abbreviations, list) or not all(isinstance(alias, str) for alias in abbreviations):
                raise ValueError(f"Abbreviations for {law_id} must be a list of strings")
            entries.append(
                LawRegistryEntry(
                    law_id=law_id,
                    official_title=_required_str(item, "official_title"),
                    full_name=_optional_str(item.get("full_name")),
                    document_number=_optional_str(item.get("document_number")),
                    document_type=_optional_str(item.get("document_type")),
                    issued_year=item.get("issued_year") if isinstance(item.get("issued_year"), int) else None,
                    aliases=[normalize_query(alias) for alias in aliases],
                    abbreviations=[normalize_query(alias) for alias in abbreviations],
                    domain=_optional_str(item.get("domain")),
                )
            )
        registry = cls(entries)
        ambiguous = {key: values for key, values in registry.by_lookup.items() if len(values) > 1 and len(key) > 4}
        if ambiguous:
            names = ", ".join(sorted(ambiguous)[:5])
            raise ValueError(f"Ambiguous registry aliases: {names}")
        return registry

    def get(self, law_id: str) -> LawRegistryEntry | None:
        return self.by_law_id.get(law_id)

    def lookup_exact(self, text: str) -> list[LawRegistryEntry]:
        return self.by_lookup.get(_lookup_key(text), [])


def _lookup_key(value: str) -> str:
    return fold_text(normalize_query(value))


def _required_str(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Registry field {field} must be a non-empty string")
    return normalize_query(value)


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = normalize_query(value)
    return cleaned or None
