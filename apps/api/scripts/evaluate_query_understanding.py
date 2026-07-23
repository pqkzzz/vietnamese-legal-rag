"""Evaluate query understanding against the dense evaluation query set."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.query_understanding import QueryUnderstandingService  # noqa: E402
from app.modules.retrieval.metadata_filter_builder import MetadataFilterBuilder  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(PROJECT_ROOT / "data" / "evaluation" / "dense_eval.jsonl"))
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "evaluation" / "results" / "query_understanding_eval_results.json"),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    service = QueryUnderstandingService()
    builder = MetadataFilterBuilder()

    total = 0
    law_gold_count = 0
    law_correct = 0
    false_positive_law_filter = 0
    route_counts: Counter[str] = Counter()
    citation_queries = 0
    mismatches: list[dict[str, object]] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            item = json.loads(line)
            query = str(item.get("query") or item.get("question") or "")
            gold_law_id = item.get("search_law_id")
            understanding = service.understand(query)
            plan = builder.build(understanding)
            route_counts[plan.route] += 1
            predicted_law_id = plan.hard_filters.get("law_id")
            if understanding.citations:
                citation_queries += 1
            if gold_law_id:
                law_gold_count += 1
                if predicted_law_id == gold_law_id:
                    law_correct += 1
                elif len(mismatches) < 20:
                    mismatches.append(
                        {
                            "query": query,
                            "gold_law_id": gold_law_id,
                            "predicted_law_id": predicted_law_id,
                            "route": plan.route,
                            "resolved_laws": [law.to_dict() for law in understanding.resolved_laws[:3]],
                        }
                    )
            elif predicted_law_id:
                false_positive_law_filter += 1
                if len(mismatches) < 20:
                    mismatches.append(
                        {
                            "query": query,
                            "gold_law_id": None,
                            "predicted_law_id": predicted_law_id,
                            "route": plan.route,
                        }
                    )

    report = {
        "total_queries": total,
        "law_gold_count": law_gold_count,
        "law_filter_accuracy_when_gold_present": round(law_correct / law_gold_count, 4) if law_gold_count else None,
        "false_positive_law_filter_count": false_positive_law_filter,
        "citation_query_count": citation_queries,
        "route_distribution": dict(route_counts),
        "mismatches_sample": mismatches,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



