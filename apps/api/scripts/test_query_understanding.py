"""Inspect rule-based query understanding and metadata filter planning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.query_understanding import QueryUnderstandingService  # noqa: E402
from app.modules.retrieval.metadata_filter_builder import MetadataFilterBuilder  # noqa: E402

DEFAULT_QUERY = "Theo điểm b khoản 1 Điều 121 Luật Đất đai 2024, trường hợp nào được cấp giấy chứng nhận?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default=DEFAULT_QUERY)
    args = parser.parse_args()

    understanding = QueryUnderstandingService().understand(args.query)
    filter_plan = MetadataFilterBuilder().build(understanding)
    print(
        json.dumps(
            {
                "query_understanding": understanding.to_dict(),
                "filter_plan": filter_plan.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



