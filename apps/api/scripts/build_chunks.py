"""CLI for building retrieval JSONL chunks from normalized legal documents."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
API_ROOT = ROOT_DIR / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.ingestion.chunk_builder import build_chunks_for_document  # noqa: E402

LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Build retrieval chunks from normalized legal JSON.")
    parser.add_argument("--input-dir", default="data/normalized", help="Directory containing *_normalized.json files.")
    parser.add_argument("--output-dir", default="data/retrieval", help="Directory for retrieval JSONL output.")
    parser.add_argument("--file", dest="filename", help="Process only one normalized filename.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing chunk and report files.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are reported.")
    parser.add_argument("--dry-run", action="store_true", help="Build and validate without writing output files.")
    return parser.parse_args(argv)


def resolve_path(path_value: str) -> Path:
    """Resolve a CLI path relative to repository root when needed."""

    path = Path(path_value)
    return path if path.is_absolute() else ROOT_DIR / path


def iter_input_files(input_dir: Path, filename: str | None) -> list[Path]:
    """Return normalized JSON files in deterministic order."""

    if filename:
        path = input_dir / filename
        return [path] if path.name.endswith("_normalized.json") else []
    return sorted(input_dir.glob("*_normalized.json"))


def atomic_write_json(path: Path, payload: dict[str, Any], overwrite: bool) -> None:
    """Write one JSON file with a temporary file and atomic replacement."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        tmp_path.replace(path)
    except (OSError, TypeError):
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def atomic_write_jsonl(path: Path, chunks: list[dict[str, Any]], overwrite: bool) -> None:
    """Write chunks as JSONL, validate parseability, then replace output."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            for chunk in chunks:
                handle.write(json.dumps(chunk, ensure_ascii=False, separators=(",", ":")))
                handle.write("\n")
        _validate_jsonl_file(tmp_path, len(chunks))
        tmp_path.replace(path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def run_batch(input_dir: Path, output_dir: Path, filename: str | None, overwrite: bool, strict: bool, dry_run: bool) -> int:
    """Build retrieval chunks for a batch of normalized files."""

    files = iter_input_files(input_dir, filename)
    reports_dir = output_dir / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    totals = {
        "files": 0,
        "failed_files": 0,
        "input_units": 0,
        "output_chunks": 0,
        "clauses_split": 0,
        "point_chunks": 0,
        "article_leads_skipped": 0,
        "warnings": 0,
        "errors": 0,
    }

    if not files:
        LOGGER.error("No normalized JSON files found in %s", input_dir)
        return 1

    for input_path in files:
        LOGGER.info("Processing %s", input_path)
        try:
            normalized = json.loads(input_path.read_text(encoding="utf-8"))
            if not isinstance(normalized, dict):
                raise ValueError(f"{input_path} must contain a JSON object")
            result = build_chunks_for_document(normalized, input_path.name)
            report = result.report.to_dict()
            chunk_path = output_dir / report["output_file"]
            report_path = reports_dir / f"{report['law_id'] or input_path.stem}_chunk_report.json"

            if report["error_count"] == 0 and not dry_run:
                atomic_write_jsonl(chunk_path, result.chunks, overwrite)
            elif report["error_count"]:
                LOGGER.error("Validation failed for %s with %s errors; chunk output was not replaced", input_path, report["error_count"])
            if not dry_run:
                atomic_write_json(report_path, report, overwrite=True)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            totals["failed_files"] += 1
            LOGGER.error("Failed %s: %s", input_path, exc)
            continue

        totals["files"] += 1
        totals["input_units"] += int(report["input_units"])
        totals["output_chunks"] += int(report["output_chunks"])
        totals["clauses_split"] += int(report["clauses_split"])
        totals["point_chunks"] += int(report["point_chunks"])
        totals["article_leads_skipped"] += int(report["article_leads_skipped"])
        totals["warnings"] += int(report["warning_count"])
        totals["errors"] += int(report["error_count"])
        LOGGER.info(
            "Built %s chunks from %s units (split=%s points=%s warnings=%s errors=%s)",
            report["output_chunks"],
            report["input_units"],
            report["clauses_split"],
            report["point_chunks"],
            report["warning_count"],
            report["error_count"],
        )

    LOGGER.info("Processed normalized files: %s", totals["files"])
    LOGGER.info("Input legal units: %s", totals["input_units"])
    LOGGER.info("Output chunks: %s", totals["output_chunks"])
    LOGGER.info("Clauses split: %s", totals["clauses_split"])
    LOGGER.info("Point chunks: %s", totals["point_chunks"])
    LOGGER.info("Article leads skipped: %s", totals["article_leads_skipped"])
    LOGGER.info("Warnings: %s", totals["warnings"])
    LOGGER.info("Errors: %s", totals["errors"])
    LOGGER.info("Output directory: %s", output_dir)

    if totals["failed_files"] or totals["errors"] or (strict and totals["warnings"]):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the retrieval chunk builder CLI."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args(argv)
    return run_batch(
        input_dir=resolve_path(args.input_dir),
        output_dir=resolve_path(args.output_dir),
        filename=args.filename,
        overwrite=args.overwrite,
        strict=args.strict,
        dry_run=args.dry_run,
    )


def _validate_jsonl_file(path: Path, expected_lines: int) -> None:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            count += 1
            json.loads(line)
    if count != expected_lines:
        raise ValueError(f"JSONL line count {count} does not match chunk count {expected_lines}")


if __name__ == "__main__":
    raise SystemExit(main())
