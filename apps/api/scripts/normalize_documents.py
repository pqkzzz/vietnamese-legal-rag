"""CLI for normalizing raw legal JSON documents."""

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
if str(ROOT_DIR / "apps" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from app.modules.legal_parser.normalizer import normalize_file, output_filename_for  # noqa: E402

LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Normalize raw Vietnamese legal JSON documents.")
    parser.add_argument("--input-dir", default="data/raw", help="Directory containing raw .json files.")
    parser.add_argument("--output-dir", default="data/normalized", help="Directory for normalized output files.")
    parser.add_argument("--file", dest="filename", help="Process only one raw JSON filename.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing normalized files.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any warning or error is reported.")
    return parser.parse_args(argv)


def resolve_path(path_value: str) -> Path:
    """Resolve a CLI path relative to repository root when needed."""

    path = Path(path_value)
    return path if path.is_absolute() else ROOT_DIR / path


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON with a temp file and atomic replacement."""

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


def iter_input_files(input_dir: Path, filename: str | None) -> list[Path]:
    """Return input JSON files in deterministic order."""

    if filename:
        path = input_dir / filename
        return [path] if path.suffix.lower() == ".json" else []
    return sorted(input_dir.glob("*.json"))


def run_batch(input_dir: Path, output_dir: Path, filename: str | None, overwrite: bool, strict: bool) -> int:
    """Normalize a directory of raw documents and return a process exit code."""

    files = iter_input_files(input_dir, filename)
    output_dir.mkdir(parents=True, exist_ok=True)

    totals = {
        "files": 0,
        "input_units": 0,
        "output_units": 0,
        "warnings": 0,
        "errors": 0,
        "failed_files": 0,
    }

    if not files:
        LOGGER.error("No JSON files found in %s", input_dir)
        return 1

    for input_path in files:
        LOGGER.info("Processing %s", input_path)
        try:
            if not input_path.exists():
                raise FileNotFoundError(input_path)
            normalized = normalize_file(input_path)
            report = normalized["normalization_report"]
            output_path = output_dir / output_filename_for(normalized, input_path.stem)
            if output_path.exists() and not overwrite:
                raise FileExistsError(f"{output_path} exists; pass --overwrite to replace it")
            atomic_write_json(output_path, normalized)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            totals["failed_files"] += 1
            LOGGER.error("Failed %s: %s", input_path, exc)
            continue

        totals["files"] += 1
        totals["input_units"] += int(report["total_input_units"])
        totals["output_units"] += int(report["total_output_units"])
        totals["warnings"] += int(report["warning_count"])
        totals["errors"] += int(report["error_count"])
        LOGGER.info(
            "Wrote %s (input=%s output=%s warnings=%s errors=%s)",
            output_path,
            report["total_input_units"],
            report["total_output_units"],
            report["warning_count"],
            report["error_count"],
        )

    LOGGER.info(
        "Batch complete: files=%s failed=%s input=%s output=%s warnings=%s errors=%s output_dir=%s",
        totals["files"],
        totals["failed_files"],
        totals["input_units"],
        totals["output_units"],
        totals["warnings"],
        totals["errors"],
        output_dir,
    )
    LOGGER.info("Normalized %s files", totals["files"])
    LOGGER.info("Input units: %s", totals["input_units"])
    LOGGER.info("Output units: %s", totals["output_units"])
    LOGGER.info("Warnings: %s", totals["warnings"])
    LOGGER.info("Errors: %s", totals["errors"])
    LOGGER.info("Output directory: %s", output_dir)

    if totals["failed_files"] or totals["errors"] or (strict and totals["warnings"]):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the normalization CLI."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args(argv)
    return run_batch(
        input_dir=resolve_path(args.input_dir),
        output_dir=resolve_path(args.output_dir),
        filename=args.filename,
        overwrite=args.overwrite,
        strict=args.strict,
    )


if __name__ == "__main__":
    raise SystemExit(main())


