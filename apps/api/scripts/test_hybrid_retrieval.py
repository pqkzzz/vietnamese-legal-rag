"""Manually test Dense + BM25 hybrid legal retrieval."""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test Dense + BM25 RRF retrieval.",
    )

    parser.add_argument(
        "query",
        type=str,
        help="Câu hỏi pháp luật.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Số kết quả Hybrid trả về.",
    )

    parser.add_argument(
        "--law-id",
        type=str,
        default=None,
        help="Chỉ tìm trong một luật.",
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
        help="Hằng số làm mượt RRF.",
    )

    parser.add_argument(
        "--dense-weight",
        type=float,
        default=1.0,
        help="Trọng số Dense.",
    )

    parser.add_argument(
        "--sparse-weight",
        type=float,
        default=1.0,
        help="Trọng số BM25.",
    )

    return parser.parse_args()


def format_position(
    payload: dict[str, Any],
) -> str:
    parts: list[str] = []

    article = payload.get("article_number")
    clause = payload.get("clause_number")
    point = payload.get("point_number")

    if article:
        parts.append(f"Điều {article}")

    if clause:
        parts.append(f"Khoản {clause}")

    if point:
        parts.append(f"Điểm {point}")

    return " - ".join(parts) or "Không rõ vị trí"


def shorten(
    value: Any,
    max_length: int = 400,
) -> str:
    if not isinstance(value, str):
        return ""

    text = " ".join(value.split())

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "..."


def main() -> int:
    args = parse_args()

    dense_model_path = resolve_project_path(
        os.getenv(
            "EMBEDDING_MODEL_PATH",
            "models/bge-m3-finetuned",
        )
    )

    dense_model = BGEM3EmbeddingModel(
        model_path=dense_model_path,
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

    dense_retriever = DenseLegalRetriever(
        embedding_model=dense_model,
        qdrant_client=client,
        collection_name=os.getenv(
            "QDRANT_COLLECTION",
            "legal_units_bge_m3_finetuned",
        ),
    )

    sparse_retriever = SparseLegalRetriever(
        embedding_model=sparse_model,
        qdrant_client=client,
        collection_name=os.getenv(
            "QDRANT_SPARSE_COLLECTION",
            "legal_units_bm25",
        ),
        sparse_vector_name=os.getenv(
            "QDRANT_SPARSE_VECTOR_NAME",
            "bm25",
        ),
    )

    hybrid_retriever = HybridLegalRetriever(
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        candidate_limit=args.candidate_limit,
        rrf_k=args.rrf_k,
        dense_weight=args.dense_weight,
        sparse_weight=args.sparse_weight,
    )

    started_at = time.perf_counter()

    results = hybrid_retriever.search(
        args.query,
        limit=args.limit,
        law_id=args.law_id,
    )

    latency = time.perf_counter() - started_at

    print()
    print("=" * 100)
    print("PIPELINE: Hybrid Dense + BM25 RRF")
    print("QUERY:", args.query)
    print("LAW ID:", args.law_id)
    print("CANDIDATES PER BRANCH:", args.candidate_limit)
    print("RRF K:", args.rrf_k)
    print("DENSE WEIGHT:", args.dense_weight)
    print("SPARSE WEIGHT:", args.sparse_weight)
    print("RESULTS:", len(results))
    print(f"LATENCY: {latency:.4f} giây")
    print("=" * 100)

    for rank, result in enumerate(
        results,
        start=1,
    ):
        payload = result.payload

        print()
        print(
            f"[{rank}] Hybrid RRF score: "
            f"{result.score:.8f}"
        )
        print(
            "Chunk ID:",
            payload.get("chunk_id"),
        )
        print(
            "Luật:",
            payload.get("law_name"),
        )
        print(
            "Vị trí:",
            format_position(payload),
        )
        print(
            "Dense rank:",
            result.dense_rank,
        )
        print(
            "Dense score:",
            result.dense_score,
        )
        print(
            "BM25 rank:",
            result.sparse_rank,
        )
        print(
            "BM25 score:",
            result.sparse_score,
        )
        print(
            "Nội dung:",
            shorten(
                payload.get("content_clean")
            ),
        )
        print("-" * 100)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())