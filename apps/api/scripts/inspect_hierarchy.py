"""Inspect the legal provision hierarchy built from retrieval JSONL data."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import LegalProvisionHierarchyIndex, ProvisionNode  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(PROJECT_ROOT / "data" / "retrieval"))
    parser.add_argument("--law-id", default="LDD_2024")
    parser.add_argument("--article", default="121")
    parser.add_argument("--clause", default="1")
    parser.add_argument("--point", default="b")
    parser.add_argument("--show-warnings", action="store_true")
    parser.add_argument("--warning-limit", type=int, default=20)
    args = parser.parse_args()

    started = time.perf_counter()
    index = LegalProvisionHierarchyIndex.from_jsonl_directory(args.data_dir)
    build_seconds = time.perf_counter() - started
    report = index.get_build_report()

    clause_number = args.clause.strip() or None if args.clause is not None else None
    point_number = args.point.strip() or None if args.point is not None else None
    lookup = index.lookup(
        args.law_id,
        args.article,
        clause_number,
        point_number,
    )
    exact = lookup.exact_node

    print(f"Build time: {build_seconds:.4f}s")
    print(f"Total nodes: {report.total_nodes}")
    print(f"Article nodes: {report.article_nodes}")
    print(f"Clause nodes: {report.clause_nodes}")
    print(f"Point nodes: {report.point_nodes}")
    print(f"Warning count: {report.warning_count}")
    print()
    print("Lookup:", lookup.location)
    print("Found:", lookup.found)
    print("Matched level:", lookup.matched_level.value if lookup.matched_level else None)
    print()
    print_node("Exact node", exact)

    if exact is not None:
        print_node("Parent", index.get_parent(exact.chunk_id))
        print_nodes("Children", index.get_children(exact.chunk_id))
        print_nodes("Siblings", index.get_siblings(exact.chunk_id))
        print_node("Previous sibling", index.get_previous_sibling(exact.chunk_id))
        print_node("Next sibling", index.get_next_sibling(exact.chunk_id))

    if args.show_warnings:
        print()
        print(f"Warnings (first {args.warning_limit}):")
        for warning in report.warnings[: args.warning_limit]:
            print(f"- {warning.code}: {warning.chunk_id} -> {warning.related_chunk_id} | {warning.message}")

    return 0


def print_nodes(title: str, nodes: list[ProvisionNode]) -> None:
    print(f"{title}: {len(nodes)}")
    for node in nodes:
        print_node("-", node)


def print_node(title: str, node: ProvisionNode | None) -> None:
    if node is None:
        print(f"{title}: None")
        return
    content_preview = _preview(node.content_clean)
    clause_lead_preview = _preview(node.clause_lead_clean)
    print(
        f"{title}: {node.chunk_id} | level={node.level.value} | "
        f"order_index={node.order_index} | is_retrievable={node.is_retrievable}"
    )
    print(f"  parent_id: {node.parent_id}")
    print(f"  child_ids: {list(node.child_ids)}")
    print(f"  previous_sibling_id: {node.previous_sibling_id}")
    print(f"  next_sibling_id: {node.next_sibling_id}")
    print(f"  content: {content_preview}")
    print(f"  clause_lead_clean: {clause_lead_preview}")


def _preview(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


if __name__ == "__main__":
    raise SystemExit(main())

