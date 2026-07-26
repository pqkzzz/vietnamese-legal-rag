"""Inspect direct legal references for one retrieval chunk."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import LegalProvisionHierarchyIndex, LegalReferenceParser, LegalReferenceResolver  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(PROJECT_ROOT / "data" / "retrieval"))
    parser.add_argument("--chunk-id", required=True)
    parser.add_argument("--show-content", action="store_true")
    parser.add_argument("--show-raw", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    hierarchy = LegalProvisionHierarchyIndex.from_jsonl_directory(args.data_dir)
    node = hierarchy.get_node(args.chunk_id)
    if node is None:
        print(f"Chunk not found: {args.chunk_id}", file=sys.stderr)
        return 1

    reference_parser = LegalReferenceParser()
    resolver = LegalReferenceResolver(hierarchy, reference_parser)

    parse_started = time.perf_counter()
    references = reference_parser.parse_node(node)
    parse_latency = time.perf_counter() - parse_started

    resolve_started = time.perf_counter()
    resolved = [resolver.resolve(reference) for reference in references]
    resolve_latency = time.perf_counter() - resolve_started

    structured_count = sum(1 for reference in references if reference.parser_source == "structured_metadata")
    regex_count = sum(1 for reference in references if reference.parser_source == "content_regex")
    raw_count = sum(1 for reference in references if reference.parser_source == "raw_reference")

    print(f"Source chunk: {node.chunk_id}")
    print(f"Structured cross_references count: {len(node.cross_references)}")
    print(f"Parsed references: {len(references)}")
    print(f"Structured parsed: {structured_count}")
    print(f"Raw-reference parsed: {raw_count}")
    print(f"Regex parsed: {regex_count}")
    print(f"Parse latency: {parse_latency:.4f}s")
    print(f"Resolve latency: {resolve_latency:.4f}s")
    print()

    if args.show_content:
        print("Content preview:")
        print(_preview(node.content_clean, 800))
        print()

    for index, item in enumerate(resolved[: args.limit], start=1):
        reference = item.reference
        print(f"[{index}] source={reference.parser_source} type={reference.reference_type.value} confidence={reference.confidence:.2f}")
        print(f"  target_unit_id: {reference.target_unit_id}")
        print(
            "  target_location:",
            {
                "law_id": reference.target_law_id,
                "article": reference.target_article_number,
                "clause": reference.target_clause_number,
                "point": reference.target_point_number,
            },
        )
        print(f"  anchor_text: {reference.anchor_text}")
        print(f"  raw_text: {reference.raw_text}")
        print(f"  status: {item.status.value}")
        print(f"  exact_node: {item.exact_node.chunk_id if item.exact_node else None}")
        print(f"  resolved_node_ids: {[target.chunk_id for target in item.resolved_nodes]}")
        print(f"  warnings: {item.warnings}")
        if args.show_raw:
            print("  metadata:", json.dumps(_jsonable(reference.metadata), ensure_ascii=False, indent=2))
        print()

    if len(resolved) > args.limit:
        print(f"... {len(resolved) - args.limit} more references not shown")

    return 0


def _preview(value: str, limit: int) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
