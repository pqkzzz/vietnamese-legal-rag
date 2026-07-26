from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import LegalDependencyDetector, LegalProvisionHierarchyIndex, LegalReferenceParser, ProvisionNode


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Inspect dependency signals for one legal retrieval chunk.")
    parser.add_argument("--chunk-id", required=True, help="Chunk ID to inspect.")
    parser.add_argument("--data-dir", default=str(REPO_ROOT / "data" / "retrieval"), help="Directory containing *_chunks.jsonl files.")
    parser.add_argument("--show-content", action="store_true", help="Print full node content.")
    parser.add_argument("--show-parent", action="store_true", help="Include parent preview when available.")
    parser.add_argument("--show-siblings", action="store_true", help="Include sibling previews.")
    parser.add_argument("--show-references", action="store_true", help="Include parsed reference details.")
    args = parser.parse_args()

    start = time.perf_counter()
    hierarchy = LegalProvisionHierarchyIndex.from_jsonl_directory(args.data_dir)
    node = hierarchy.get_node(args.chunk_id)
    if node is None:
        print(json.dumps({"error": "chunk_id not found", "chunk_id": args.chunk_id}, ensure_ascii=False, indent=2))
        return 1

    reference_parser = LegalReferenceParser()
    references = reference_parser.parse_node(node)
    signal = LegalDependencyDetector().detect(node, hierarchy=hierarchy, parsed_references=references)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    parent = hierarchy.get_parent(node.chunk_id)
    children = hierarchy.get_children(node.chunk_id)
    siblings = hierarchy.get_siblings(node.chunk_id)

    result: dict[str, Any] = {
        "chunk_id": node.chunk_id,
        "level": node.level.value,
        "location": {
            "law_id": node.law_id,
            "article_number": node.article_number,
            "clause_number": node.clause_number,
            "point_number": node.point_number,
        },
        "content_preview": _preview(node.content_clean),
        "clause_lead_clean_preview": _preview(node.clause_lead_clean),
        "parent_id": node.parent_id,
        "parent_available": parent is not None,
        "child_count": len(children),
        "sibling_count": len(siblings),
        "parsed_reference_count": len(references),
        "signal": signal.to_dict(),
        "latency_ms": latency_ms,
    }

    if args.show_content:
        result["content_clean"] = node.content_clean
        result["clause_lead_clean"] = node.clause_lead_clean
    if args.show_parent:
        result["parent"] = _node_summary(parent) if parent else None
    if args.show_siblings:
        result["siblings"] = [_node_summary(sibling) for sibling in siblings]
    if args.show_references:
        result["references"] = [reference.to_dict() for reference in references]

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _preview(value: str | None, *, limit: int = 220) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _node_summary(node: ProvisionNode | None) -> dict[str, Any] | None:
    if node is None:
        return None
    return {
        "chunk_id": node.chunk_id,
        "level": node.level.value,
        "article_number": node.article_number,
        "clause_number": node.clause_number,
        "point_number": node.point_number,
        "content_preview": _preview(node.content_clean, limit=160),
    }


if __name__ == "__main__":
    raise SystemExit(main())

