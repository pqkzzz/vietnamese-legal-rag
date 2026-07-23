"""Compare Dense, BM25 and Hybrid retrieval evaluation results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "results"
)

DENSE_RESULT_PATH = (
    RESULTS_DIR / "dense_eval_results.json"
)

SPARSE_RESULT_PATH = (
    RESULTS_DIR / "sparse_eval_results.json"
)

HYBRID_RESULT_PATH = (
    RESULTS_DIR / "hybrid_eval_results.json"
)

OUTPUT_JSON_PATH = (
    RESULTS_DIR / "retrieval_pipeline_comparison.json"
)

OUTPUT_MARKDOWN_PATH = (
    RESULTS_DIR / "retrieval_pipeline_comparison.md"
)


METRIC_NAMES = [
    "hit@1",
    "recall@1",
    "hit@3",
    "recall@3",
    "hit@5",
    "recall@5",
    "hit@10",
    "recall@10",
    "mrr@10",
    "latency_seconds",
]


def load_json(path: Path) -> dict[str, Any]:
    """Load and validate one evaluation result file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy result file: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"File không chứa JSON object: {path}"
        )

    if not isinstance(data.get("summary"), dict):
        raise ValueError(
            f"Result thiếu summary: {path}"
        )

    if not isinstance(data.get("per_query"), list):
        raise ValueError(
            f"Result thiếu per_query: {path}"
        )

    return data


def map_queries(
    result: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Map each evaluation case by its ID."""

    mapped: dict[str, dict[str, Any]] = {}

    for item in result["per_query"]:
        if not isinstance(item, dict):
            raise ValueError(
                "per_query chứa phần tử không hợp lệ."
            )

        case_id = item.get("id")

        if (
            not isinstance(case_id, str)
            or not case_id.strip()
        ):
            raise ValueError(
                "per_query item thiếu id."
            )

        mapped[case_id] = item

    return mapped


def normalize_rank(value: Any) -> float:
    """Convert a missing rank into positive infinity."""

    if isinstance(value, int) and value > 0:
        return float(value)

    return float("inf")


def format_rank(value: Any) -> str:
    """Format a rank for Markdown output."""

    if isinstance(value, int):
        return str(value)

    return "Not found"


def best_metric_pipeline(
    metric_name: str,
    values: dict[str, float],
) -> str:
    """Find the best pipeline for one metric."""

    if metric_name == "latency_seconds":
        best_value = min(values.values())
    else:
        best_value = max(values.values())

    winners = [
        pipeline
        for pipeline, value in values.items()
        if abs(value - best_value) < 1e-12
    ]

    return ", ".join(winners)


def main() -> int:
    dense = load_json(DENSE_RESULT_PATH)
    sparse = load_json(SPARSE_RESULT_PATH)
    hybrid = load_json(HYBRID_RESULT_PATH)

    dense_summary = dense["summary"]
    sparse_summary = sparse["summary"]
    hybrid_summary = hybrid["summary"]

    metric_comparison: dict[
        str,
        dict[str, Any],
    ] = {}

    for metric_name in METRIC_NAMES:
        values = {
            "dense": float(
                dense_summary[metric_name]
            ),
            "bm25": float(
                sparse_summary[metric_name]
            ),
            "hybrid": float(
                hybrid_summary[metric_name]
            ),
        }

        metric_comparison[metric_name] = {
            **values,
            "best_pipeline": best_metric_pipeline(
                metric_name,
                values,
            ),
            "hybrid_minus_dense": (
                values["hybrid"]
                - values["dense"]
            ),
            "hybrid_minus_bm25": (
                values["hybrid"]
                - values["bm25"]
            ),
        }

    dense_queries = map_queries(dense)
    sparse_queries = map_queries(sparse)
    hybrid_queries = map_queries(hybrid)

    common_case_ids = sorted(
        set(dense_queries)
        & set(sparse_queries)
        & set(hybrid_queries)
    )

    rank_win_counts = {
        "dense": 0,
        "bm25": 0,
        "hybrid": 0,
        "tie": 0,
    }

    per_query_comparison: list[
        dict[str, Any]
    ] = []

    for case_id in common_case_ids:
        dense_case = dense_queries[case_id]
        sparse_case = sparse_queries[case_id]
        hybrid_case = hybrid_queries[case_id]

        original_ranks = {
            "dense": dense_case.get(
                "first_relevant_rank"
            ),
            "bm25": sparse_case.get(
                "first_relevant_rank"
            ),
            "hybrid": hybrid_case.get(
                "first_relevant_rank"
            ),
        }

        comparable_ranks = {
            pipeline: normalize_rank(rank)
            for pipeline, rank
            in original_ranks.items()
        }

        best_rank = min(
            comparable_ranks.values()
        )

        winners = [
            pipeline
            for pipeline, rank
            in comparable_ranks.items()
            if rank == best_rank
        ]

        if len(winners) == 1:
            winner = winners[0]
            rank_win_counts[winner] += 1
        else:
            winner = "tie"
            rank_win_counts["tie"] += 1

        per_query_comparison.append(
            {
                "id": case_id,
                "query": dense_case.get("query"),
                "relevant_chunk_ids": (
                    dense_case.get(
                        "relevant_chunk_ids"
                    )
                ),
                "dense_first_relevant_rank": (
                    original_ranks["dense"]
                ),
                "bm25_first_relevant_rank": (
                    original_ranks["bm25"]
                ),
                "hybrid_first_relevant_rank": (
                    original_ranks["hybrid"]
                ),
                "winner": winner,
                "tied_winners": (
                    winners
                    if winner == "tie"
                    else []
                ),
            }
        )

    output = {
        "pipelines": {
            "dense": dense.get("pipeline"),
            "bm25": sparse.get("pipeline"),
            "hybrid": hybrid.get("pipeline"),
        },
        "case_count": len(common_case_ids),
        "metrics": metric_comparison,
        "first_relevant_rank_wins": (
            rank_win_counts
        ),
        "per_query": per_query_comparison,
    }

    OUTPUT_JSON_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_JSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    markdown_lines = [
        "# Retrieval Pipeline Comparison",
        "",
        "## Summary metrics",
        "",
        (
            "| Metric | Dense | BM25 | Hybrid "
            "| Best pipeline |"
        ),
        "|---|---:|---:|---:|---|",
    ]

    for metric_name in METRIC_NAMES:
        values = metric_comparison[metric_name]

        markdown_lines.append(
            f"| {metric_name} "
            f"| {values['dense']:.4f} "
            f"| {values['bm25']:.4f} "
            f"| {values['hybrid']:.4f} "
            f"| {values['best_pipeline']} |"
        )

    markdown_lines.extend(
        [
            "",
            "## First relevant rank wins",
            "",
            (
                f"- Dense: "
                f"{rank_win_counts['dense']}"
            ),
            (
                f"- BM25: "
                f"{rank_win_counts['bm25']}"
            ),
            (
                f"- Hybrid: "
                f"{rank_win_counts['hybrid']}"
            ),
            (
                f"- Tie: "
                f"{rank_win_counts['tie']}"
            ),
            "",
            "## Important cases",
            "",
            (
                "| Case | Dense rank | BM25 rank "
                "| Hybrid rank | Winner |"
            ),
            "|---|---:|---:|---:|---|",
        ]
    )

    important_case_ids = {
        "eval_001",
        "eval_004",
        "eval_008",
        "eval_013",
        "eval_015",
        "eval_029",
        "eval_033",
    }

    for item in per_query_comparison:
        if item["id"] not in important_case_ids:
            continue

        markdown_lines.append(
            f"| {item['id']} "
            f"| {format_rank(item['dense_first_relevant_rank'])} "
            f"| {format_rank(item['bm25_first_relevant_rank'])} "
            f"| {format_rank(item['hybrid_first_relevant_rank'])} "
            f"| {item['winner']} |"
        )

    with OUTPUT_MARKDOWN_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "\n".join(markdown_lines) + "\n"
        )

    print("=" * 78)
    print("DENSE VS BM25 VS HYBRID COMPARISON")
    print("=" * 78)

    for metric_name in METRIC_NAMES:
        values = metric_comparison[metric_name]

        print(
            f"{metric_name:<18} "
            f"Dense={values['dense']:.4f} | "
            f"BM25={values['bm25']:.4f} | "
            f"Hybrid={values['hybrid']:.4f} | "
            f"Best={values['best_pipeline']}"
        )

    print()
    print(
        "Dense rank wins:",
        rank_win_counts["dense"],
    )
    print(
        "BM25 rank wins:",
        rank_win_counts["bm25"],
    )
    print(
        "Hybrid rank wins:",
        rank_win_counts["hybrid"],
    )
    print(
        "Ties:",
        rank_win_counts["tie"],
    )

    print()
    print("Saved JSON:", OUTPUT_JSON_PATH)
    print(
        "Saved Markdown:",
        OUTPUT_MARKDOWN_PATH,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())