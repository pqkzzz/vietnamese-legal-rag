"""Validate the dense retrieval gold evaluation dataset."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
RETRIEVAL_DIR = ROOT_DIR / "data" / "retrieval"
DATASET_PATH = ROOT_DIR / "data" / "evaluation" / "dense_eval.jsonl"
REPORT_PATH = ROOT_DIR / "data" / "evaluation" / "dense_eval_report.json"
EXPECTED_CASE_COUNT = 48


def load_chunks(retrieval_dir: Path) -> dict[str, dict[str, Any]]:
    """Load all retrieval chunks keyed by chunk_id."""

    chunks: dict[str, dict[str, Any]] = {}
    for path in sorted(retrieval_dir.glob("*_chunks.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                chunk = json.loads(line)
                chunk_id = chunk.get("chunk_id")
                if isinstance(chunk_id, str):
                    chunks[chunk_id] = chunk
    return chunks


def load_dataset(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    """Load dataset JSONL, recording parse errors instead of crashing."""

    cases: list[dict[str, Any]] = []
    if not path.exists():
        errors.append(f"Dataset does not exist: {path}")
        return cases
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON on line {line_number}: {exc}")
                continue
            if not isinstance(case, dict):
                errors.append(f"Line {line_number} is not a JSON object")
                continue
            cases.append(case)
    return cases


def validate(cases: list[dict[str, Any]], chunks: dict[str, dict[str, Any]]) -> tuple[list[str], list[str], dict[str, Any]]:
    """Validate dataset and return errors, warnings, and distribution report."""

    errors: list[str] = []
    warnings: list[str] = []
    valid_law_ids = sorted({chunk.get("payload", {}).get("law_id") for chunk in chunks.values() if chunk.get("payload", {}).get("law_id")})
    ids = [case.get("id") for case in cases]
    queries = [case.get("query") for case in cases]
    law_distribution: Counter[str] = Counter()
    filter_distribution: Counter[str] = Counter()
    gold_unit_type_distribution: Counter[str] = Counter()
    gold_usage: Counter[str] = Counter()
    single_gold_cases = 0
    multi_gold_cases = 0
    total_gold_chunks = 0

    if len(cases) != EXPECTED_CASE_COUNT:
        errors.append(f"Expected {EXPECTED_CASE_COUNT} cases, found {len(cases)}")

    expected_ids = [f"eval_{index:03d}" for index in range(1, EXPECTED_CASE_COUNT + 1)]
    if ids != expected_ids:
        errors.append("IDs must be consecutive from eval_001 to eval_048")
    duplicate_ids = [case_id for case_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Duplicate case IDs: {duplicate_ids}")

    normalized_queries = [_normalize_query(query) for query in queries if isinstance(query, str)]
    duplicate_queries = [query for query, count in Counter(normalized_queries).items() if count > 1]
    if duplicate_queries:
        errors.append(f"Duplicate normalized queries: {duplicate_queries}")

    for case in cases:
        case_id = str(case.get("id"))
        query = case.get("query")
        gold_ids = case.get("relevant_chunk_ids")
        search_law_id = case.get("search_law_id")

        if not isinstance(query, str) or not query.strip():
            errors.append(f"{case_id}: query is empty or not a string")
        elif len(query.split()) < 7:
            warnings.append(f"{case_id}: query may be too short")
        elif len(query.split()) > 40:
            warnings.append(f"{case_id}: query may be too long")

        if search_law_id is not None and search_law_id not in valid_law_ids:
            errors.append(f"{case_id}: invalid search_law_id {search_law_id}")
        filter_distribution["with_filter" if search_law_id is not None else "without_filter"] += 1

        if not isinstance(gold_ids, list) or not gold_ids:
            errors.append(f"{case_id}: relevant_chunk_ids must be a non-empty list")
            continue
        if len(gold_ids) != len(set(gold_ids)):
            errors.append(f"{case_id}: duplicate gold chunk IDs within case")
        if len(gold_ids) == 1:
            single_gold_cases += 1
        else:
            multi_gold_cases += 1
        total_gold_chunks += len(gold_ids)

        gold_laws: set[str] = set()
        for chunk_id in gold_ids:
            chunk = chunks.get(chunk_id)
            gold_usage[str(chunk_id)] += 1
            if chunk is None:
                errors.append(f"{case_id}: gold chunk does not exist: {chunk_id}")
                continue
            payload = chunk.get("payload", {})
            gold_law = payload.get("law_id")
            gold_laws.add(str(gold_law))
            gold_unit_type_distribution[str(chunk.get("unit_type"))] += 1
            if payload.get("is_retrievable") is not True:
                errors.append(f"{case_id}: gold chunk is not retrievable: {chunk_id}")
            if payload.get("document_status") != "effective":
                errors.append(f"{case_id}: gold document is not effective: {chunk_id}")
            if payload.get("provision_status") != "effective":
                errors.append(f"{case_id}: gold provision is not effective: {chunk_id}")
            if search_law_id is not None and gold_law != search_law_id:
                errors.append(f"{case_id}: gold chunk {chunk_id} is not in search_law_id {search_law_id}")
        if len(gold_laws) == 1:
            law_distribution[next(iter(gold_laws))] += 1
        elif len(gold_laws) > 1:
            errors.append(f"{case_id}: gold chunks span multiple laws: {sorted(gold_laws)}")

    for law_id in valid_law_ids:
        if law_distribution[law_id] != 6:
            errors.append(f"Law {law_id} must have exactly 6 cases, found {law_distribution[law_id]}")
        with_filter = sum(1 for case in cases if case.get("search_law_id") == law_id and _case_law(case, chunks) == law_id)
        without_filter = sum(1 for case in cases if case.get("search_law_id") is None and _case_law(case, chunks) == law_id)
        if with_filter != 3 or without_filter != 3:
            errors.append(f"Law {law_id} must have 3 filtered and 3 unfiltered cases, found {with_filter}/{without_filter}")

    if multi_gold_cases < 8:
        errors.append(f"Expected at least 8 multi-gold cases, found {multi_gold_cases}")

    for chunk_id, count in gold_usage.items():
        if count > 3:
            warnings.append(f"Gold chunk {chunk_id} is used {count} times")

    report = {
        "dataset": "data/evaluation/dense_eval.jsonl",
        "case_count": len(cases),
        "law_distribution": dict(sorted(law_distribution.items())),
        "filter_distribution": dict(filter_distribution),
        "gold_unit_type_distribution": dict(sorted(gold_unit_type_distribution.items())),
        "single_gold_cases": single_gold_cases,
        "multi_gold_cases": multi_gold_cases,
        "total_gold_chunks": total_gold_chunks,
        "validation_passed": not errors,
        "warning_count": len(warnings),
        "error_count": len(errors),
        "warnings": warnings,
        "errors": errors,
    }
    return errors, warnings, report


def main() -> int:
    """Run dataset validation and write a JSON summary report."""

    errors: list[str] = []
    chunks = load_chunks(RETRIEVAL_DIR)
    cases = load_dataset(DATASET_PATH, errors)
    validation_errors, warnings, report = validate(cases, chunks)
    errors.extend(validation_errors)
    report["validation_passed"] = not errors
    report["error_count"] = len(errors)
    report["errors"] = errors
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Cases: {report['case_count']}")
    print(f"Law distribution: {report['law_distribution']}")
    print(f"Filter distribution: {report['filter_distribution']}")
    print(f"Gold unit types: {report['gold_unit_type_distribution']}")
    print(f"Single-gold cases: {report['single_gold_cases']}")
    print(f"Multi-gold cases: {report['multi_gold_cases']}")
    print(f"Total gold chunks: {report['total_gold_chunks']}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errors: {len(errors)}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def _normalize_query(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _case_law(case: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> str | None:
    gold_ids = case.get("relevant_chunk_ids")
    if not isinstance(gold_ids, list) or not gold_ids:
        return None
    chunk = chunks.get(gold_ids[0])
    if not chunk:
        return None
    return chunk.get("payload", {}).get("law_id")


if __name__ == "__main__":
    raise SystemExit(main())
