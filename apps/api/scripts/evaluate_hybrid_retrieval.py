"""Evaluate Dense + BM25 hybrid retrieval using RRF."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.embeddings.bge_m3 import (
    BGEM3EmbeddingModel,
)
from app.infrastructure.embeddings.bm25 import (
    BM25SparseEmbeddingModel,
)
from app.infrastructure.qdrant.client import (
    create_qdrant_client,
)
from app.modules.retrieval.dense_retriever import (
    DenseLegalRetriever,
)
from app.modules.retrieval.hybrid_retriever import (
    HybridLegalRetriever,
)
from app.modules.retrieval.sparse_retriever import (
    SparseLegalRetriever,
)


DEFAULT_DATASET = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "dense_eval.jsonl"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "results"
    / "hybrid_eval_results.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Dense + BM25 RRF retrieval.",
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--ks",
        type=str,
        default="1,3,5,10",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Chỉ đánh giá N case đầu tiên.",
    )

    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=50,
        help="Số candidate lấy từ mỗi nhánh.",
    )

    parser.add_argument(
        "--rrf-k",
        type=int,
        default=60,
        help="Hằng số RRF.",
    )

    parser.add_argument(
        "--dense-weight",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--sparse-weight",
        type=float,
        default=1.0,
    )

    return parser.parse_args()


def parse_bool(
    value: str | None,
    *,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def resolve_project_path(value: str) -> Path:
    path = Path(value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def parse_ks(value: str) -> list[int]:
    ks: list[int] = []

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        k = int(item)

        if k <= 0:
            raise ValueError(
                "Mọi giá trị k phải lớn hơn 0."
            )

        ks.append(k)

    if not ks:
        raise ValueError(
            "Danh sách k không được rỗng."
        )

    return sorted(set(ks))


def load_dataset(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy evaluation dataset: {path}"
        )

    cases: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                case = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"JSON lỗi tại {path}:{line_number}: {exc}"
                ) from exc

            if not isinstance(case, dict):
                raise ValueError(
                    f"Case dòng {line_number} "
                    "không phải object."
                )

            case_id = case.get("id")
            query = case.get("query")
            relevant = case.get(
                "relevant_chunk_ids"
            )

            if (
                not isinstance(case_id, str)
                or not case_id.strip()
            ):
                raise ValueError(
                    f"Case dòng {line_number} thiếu id."
                )

            if (
                not isinstance(query, str)
                or not query.strip()
            ):
                raise ValueError(
                    f"Case {case_id} thiếu query."
                )

            if (
                not isinstance(relevant, list)
                or not relevant
                or not all(
                    isinstance(chunk_id, str)
                    and chunk_id.strip()
                    for chunk_id in relevant
                )
            ):
                raise ValueError(
                    f"Case {case_id} có "
                    "relevant_chunk_ids không hợp lệ."
                )

            cases.append(case)

    if not cases:
        raise ValueError(
            "Evaluation dataset không có case nào."
        )

    return cases


def first_relevant_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> int | None:
    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant_ids:
            return rank

    return None


def main() -> int:
    args = parse_args()

    try:
        ks = parse_ks(args.ks)
        cases = load_dataset(
            args.dataset.resolve()
        )
    except (
        ValueError,
        FileNotFoundError,
    ) as exc:
        print(f"Dataset error: {exc}")
        return 1

    if args.limit is not None:
        if args.limit <= 0:
            print("--limit phải lớn hơn 0.")
            return 1

        cases = cases[: args.limit]

    if args.candidate_limit <= 0:
        print("--candidate-limit phải lớn hơn 0.")
        return 1

    if args.rrf_k < 0:
        print("--rrf-k không được âm.")
        return 1

    max_k = max(ks)

    dense_model = BGEM3EmbeddingModel(
        model_path=resolve_project_path(
            os.getenv(
                "EMBEDDING_MODEL_PATH",
                "models/bge-m3-finetuned",
            )
        ),
        device=os.getenv(
            "EMBEDDING_DEVICE",
            "cpu",
        ),
        batch_size=int(
            os.getenv(
                "EMBEDDING_BATCH_SIZE",
                "2",
            )
        ),
        max_length=int(
            os.getenv(
                "EMBEDDING_MAX_LENGTH",
                "512",
            )
        ),
    )

    sparse_model = BM25SparseEmbeddingModel(
        model_name=os.getenv(
            "SPARSE_MODEL_NAME",
            "Qdrant/bm25",
        ),
        cache_dir=resolve_project_path(
            os.getenv(
                "FASTEMBED_CACHE_PATH",
                ".cache/fastembed",
            )
        ),
        language=os.getenv(
            "SPARSE_LANGUAGE",
            "english",
        ),
        disable_stemmer=parse_bool(
            os.getenv(
                "SPARSE_DISABLE_STEMMER"
            ),
            default=True,
        ),
        batch_size=int(
            os.getenv(
                "SPARSE_BATCH_SIZE",
                "128",
            )
        ),
    )

    client = create_qdrant_client(
        url=os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        ),
        api_key=os.getenv(
            "QDRANT_API_KEY"
        ) or None,
    )

    dense_collection = os.getenv(
        "QDRANT_COLLECTION",
        "legal_units_bge_m3_finetuned",
    )

    sparse_collection = os.getenv(
        "QDRANT_SPARSE_COLLECTION",
        "legal_units_bm25",
    )

    sparse_vector_name = os.getenv(
        "QDRANT_SPARSE_VECTOR_NAME",
        "bm25",
    )

    dense_retriever = DenseLegalRetriever(
        embedding_model=dense_model,
        qdrant_client=client,
        collection_name=dense_collection,
    )

    sparse_retriever = SparseLegalRetriever(
        embedding_model=sparse_model,
        qdrant_client=client,
        collection_name=sparse_collection,
        sparse_vector_name=sparse_vector_name,
    )

    hybrid_retriever = HybridLegalRetriever(
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        candidate_limit=args.candidate_limit,
        rrf_k=args.rrf_k,
        dense_weight=args.dense_weight,
        sparse_weight=args.sparse_weight,
    )

    totals: dict[str, float] = {
        **{
            f"hit@{k}": 0.0
            for k in ks
        },
        **{
            f"recall@{k}": 0.0
            for k in ks
        },
        f"mrr@{max_k}": 0.0,
        "latency_seconds": 0.0,
    }

    per_query: list[dict[str, Any]] = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        case_id = case["id"]
        query = case["query"]

        relevant_ids = set(
            case["relevant_chunk_ids"]
        )

        search_law_id = case.get(
            "search_law_id"
        )

        if search_law_id is not None:
            if not isinstance(
                search_law_id,
                str,
            ):
                raise ValueError(
                    f"search_law_id của "
                    f"{case_id} không hợp lệ."
                )

            search_law_id = (
                search_law_id.strip()
                or None
            )

        started_at = time.perf_counter()

        results = hybrid_retriever.search(
            query,
            limit=max_k,
            law_id=search_law_id,
        )

        latency = (
            time.perf_counter()
            - started_at
        )

        retrieved_ids = [
            str(
                result.payload.get(
                    "chunk_id",
                    "",
                )
            )
            for result in results
        ]

        rank = first_relevant_rank(
            retrieved_ids,
            relevant_ids,
        )

        query_metrics: dict[str, float] = {}

        for k in ks:
            top_k_ids = set(
                retrieved_ids[:k]
            )

            matched = top_k_ids.intersection(
                relevant_ids
            )

            hit = (
                1.0
                if matched
                else 0.0
            )

            recall = (
                len(matched)
                / len(relevant_ids)
            )

            query_metrics[f"hit@{k}"] = hit
            query_metrics[f"recall@{k}"] = (
                recall
            )

            totals[f"hit@{k}"] += hit
            totals[f"recall@{k}"] += recall

        reciprocal_rank = (
            1.0 / rank
            if rank is not None
            and rank <= max_k
            else 0.0
        )

        query_metrics[
            f"mrr@{max_k}"
        ] = reciprocal_rank

        totals[
            f"mrr@{max_k}"
        ] += reciprocal_rank

        totals[
            "latency_seconds"
        ] += latency

        per_query.append(
            {
                "id": case_id,
                "query": query,
                "search_law_id": (
                    search_law_id
                ),
                "relevant_chunk_ids": sorted(
                    relevant_ids
                ),
                "retrieved_chunk_ids": (
                    retrieved_ids
                ),
                "first_relevant_rank": rank,
                "latency_seconds": latency,
                "metrics": query_metrics,
                "results": [
                    {
                        "rank": result_rank,
                        "chunk_id": (
                            result.payload.get(
                                "chunk_id"
                            )
                        ),
                        "rrf_score": result.score,
                        "dense_rank": (
                            result.dense_rank
                        ),
                        "sparse_rank": (
                            result.sparse_rank
                        ),
                        "dense_score": (
                            result.dense_score
                        ),
                        "sparse_score": (
                            result.sparse_score
                        ),
                        "law_id": (
                            result.payload.get(
                                "law_id"
                            )
                        ),
                        "article_number": (
                            result.payload.get(
                                "article_number"
                            )
                        ),
                        "clause_number": (
                            result.payload.get(
                                "clause_number"
                            )
                        ),
                        "point_number": (
                            result.payload.get(
                                "point_number"
                            )
                        ),
                    }
                    for result_rank, result
                    in enumerate(
                        results,
                        start=1,
                    )
                ],
            }
        )

        print(
            f"[{index}/{len(cases)}] "
            f"{case_id} | "
            f"rank={rank} | "
            f"latency={latency:.3f}s"
        )

    case_count = len(cases)

    summary = {
        metric: value / case_count
        for metric, value
        in totals.items()
    }

    output = {
        "pipeline": (
            "hybrid_dense_bm25_rrf"
        ),
        "dense_collection": (
            dense_collection
        ),
        "sparse_collection": (
            sparse_collection
        ),
        "sparse_vector_name": (
            sparse_vector_name
        ),
        "candidate_limit": (
            args.candidate_limit
        ),
        "rrf_k": args.rrf_k,
        "dense_weight": (
            args.dense_weight
        ),
        "sparse_weight": (
            args.sparse_weight
        ),
        "dataset": str(
            args.dataset.resolve()
        ),
        "case_count": case_count,
        "ks": ks,
        "summary": summary,
        "per_query": per_query,
    }

    output_path = args.output.resolve()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print("HYBRID DENSE + BM25 RRF EVALUATION")
    print("=" * 70)
    print("Cases:", case_count)
    print(
        "Candidate limit:",
        args.candidate_limit,
    )
    print("RRF k:", args.rrf_k)
    print(
        "Dense weight:",
        args.dense_weight,
    )
    print(
        "Sparse weight:",
        args.sparse_weight,
    )

    for k in ks:
        print(
            f"Hit@{k}: "
            f"{summary[f'hit@{k}']:.4f}"
        )
        print(
            f"Recall@{k}: "
            f"{summary[f'recall@{k}']:.4f}"
        )

    print(
        f"MRR@{max_k}: "
        f"{summary[f'mrr@{max_k}']:.4f}"
    )

    print(
        "Average latency:",
        f"{summary['latency_seconds']:.3f} "
        "giây/query",
    )

    print("Saved:", output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())