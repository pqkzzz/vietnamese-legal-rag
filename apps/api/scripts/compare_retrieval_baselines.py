"""Compare dense and BM25 retrieval evaluation results."""

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

DENSE_RESULT_PATH = RESULTS_DIR / "dense_eval_results.json"
SPARSE_RESULT_PATH = RESULTS_DIR / "sparse_eval_results.json"

OUTPUT_JSON_PATH = (
    RESULTS_DIR / "retrieval_baseline_comparison.json"
)

OUTPUT_MARKDOWN_PATH = (
    RESULTS_DIR / "retrieval_baseline_comparison.md"
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy result file: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"File không chứa JSON object: {path}")

    return data


def map_queries(
    result: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    per_query = result.get("per_query")

    if not isinstance(per_query, list):
        raise ValueError("Result thiếu per_query.")

    mapped: dict[str, dict[str, Any]] = {}

    for item in per_query:
        if not isinstance(item, dict):
            raise ValueError("per_query chứa phần tử không hợp lệ.")

        case_id = item.get("id")

        if not isinstance(case_id, str) or not case_id:
            raise ValueError("per_query item thiếu id.")

        mapped[case_id] = item

    return mapped


def format_rank(rank: Any) -> str:
    return str(rank) if isinstance(rank, int) else "Not found"


def main() -> int:
    dense = load_json(DENSE_RESULT_PATH)
    sparse = load_json(SPARSE_RESULT_PATH)

    dense_summary = dense["summary"]
    sparse_summary = sparse["summary"]

    metric_names = [
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

    metric_comparison: dict[str, dict[str, float]] = {}

    for metric_name in metric_names:
        dense_value = float(dense_summary[metric_name])
        sparse_value = float(sparse_summary[metric_name])

        metric_comparison[metric_name] = {
            "dense": dense_value,
            "sparse": sparse_value,
            "sparse_minus_dense": sparse_value - dense_value,
        }

    dense_queries = map_queries(dense)
    sparse_queries = map_queries(sparse)

    common_case_ids = sorted(
        set(dense_queries).intersection(sparse_queries)
    )

    per_query_comparison: list[dict[str, Any]] = []

    dense_better = 0
    sparse_better = 0
    tied = 0

    for case_id in common_case_ids:
        dense_case = dense_queries[case_id]
        sparse_case = sparse_queries[case_id]

        dense_rank = dense_case.get("first_relevant_rank")
        sparse_rank = sparse_case.get("first_relevant_rank")

        dense_rank_value = (
            dense_rank
            if isinstance(dense_rank, int)
            else float("inf")
        )

        sparse_rank_value = (
            sparse_rank
            if isinstance(sparse_rank, int)
            else float("inf")
        )

        if dense_rank_value < sparse_rank_value:
            winner = "dense"
            dense_better += 1
        elif sparse_rank_value < dense_rank_value:
            winner = "sparse"
            sparse_better += 1
        else:
            winner = "tie"
            tied += 1

        per_query_comparison.append(
            {
                "id": case_id,
                "query": dense_case.get("query"),
                "relevant_chunk_ids": dense_case.get(
                    "relevant_chunk_ids"
                ),
                "dense_first_relevant_rank": dense_rank,
                "sparse_first_relevant_rank": sparse_rank,
                "winner": winner,
                "dense_retrieved_chunk_ids": dense_case.get(
                    "retrieved_chunk_ids"
                ),
                "sparse_retrieved_chunk_ids": sparse_case.get(
                    "retrieved_chunk_ids"
                ),
            }
        )

    comparison = {
        "dense_pipeline": dense.get("pipeline"),
        "sparse_pipeline": sparse.get("pipeline"),
        "case_count": len(common_case_ids),
        "metrics": metric_comparison,
        "rank_wins": {
            "dense": dense_better,
            "sparse": sparse_better,
            "tie": tied,
        },
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
            comparison,
            file,
            ensure_ascii=False,
            indent=2,
        )

    markdown_lines = [
        "# Dense vs BM25 Retrieval Baselines",
        "",
        "## Summary metrics",
        "",
        "| Metric | Dense | BM25 | BM25 - Dense |",
        "|---|---:|---:|---:|",
    ]

    for metric_name in metric_names:
        values = metric_comparison[metric_name]

        markdown_lines.append(
            f"| {metric_name} "
            f"| {values['dense']:.4f} "
            f"| {values['sparse']:.4f} "
            f"| {values['sparse_minus_dense']:+.4f} |"
        )

    markdown_lines.extend(
        [
            "",
            "## First relevant rank wins",
            "",
            f"- Dense better: {dense_better}",
            f"- BM25 better: {sparse_better}",
            f"- Tie: {tied}",
            "",
            "## Important cases",
            "",
            "| Case | Dense rank | BM25 rank | Winner |",
            "|---|---:|---:|---|",
        ]
    )

    important_case_ids = {
        "eval_004",
        "eval_015",
        "eval_029",
        "eval_001",
        "eval_008",
        "eval_013",
        "eval_033",
    }

    for item in per_query_comparison:
        if item["id"] not in important_case_ids:
            continue

        markdown_lines.append(
            f"| {item['id']} "
            f"| {format_rank(item['dense_first_relevant_rank'])} "
            f"| {format_rank(item['sparse_first_relevant_rank'])} "
            f"| {item['winner']} |"
        )

    with OUTPUT_MARKDOWN_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(markdown_lines) + "\n")

    print("=" * 70)
    print("DENSE VS BM25 BASELINE COMPARISON")
    print("=" * 70)

    for metric_name in metric_names:
        values = metric_comparison[metric_name]

        print(
            f"{metric_name:<18} "
            f"Dense={values['dense']:.4f} | "
            f"BM25={values['sparse']:.4f} | "
            f"Delta={values['sparse_minus_dense']:+.4f}"
        )

    print()
    print("Dense rank wins:", dense_better)
    print("BM25 rank wins:", sparse_better)
    print("Ties:", tied)
    print("Saved JSON:", OUTPUT_JSON_PATH)
    print("Saved Markdown:", OUTPUT_MARKDOWN_PATH)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())