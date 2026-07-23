"""Manually test BM25 sparse legal retrieval."""

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

from app.infrastructure.embeddings.bm25 import (
    BM25SparseEmbeddingModel,
)
from app.infrastructure.qdrant.client import (
    create_qdrant_client,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test BM25 sparse legal retrieval.",
    )

    parser.add_argument(
        "query",
        type=str,
        help="Câu hỏi pháp luật cần tìm.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Số kết quả trả về.",
    )

    parser.add_argument(
        "--law-id",
        type=str,
        default=None,
        help="Chỉ tìm trong một bộ luật.",
    )

    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Ghi đè tên sparse collection.",
    )

    parser.add_argument(
        "--include-repealed",
        action="store_true",
        help="Cho phép trả về quy định đã bị bãi bỏ.",
    )

    return parser.parse_args()


def resolve_project_path(value: str) -> Path:
    path = Path(value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def format_legal_position(
    payload: dict[str, Any],
) -> str:
    parts: list[str] = []

    article_number = payload.get("article_number")
    clause_number = payload.get("clause_number")
    point_number = payload.get("point_number")

    if article_number:
        parts.append(f"Điều {article_number}")

    if clause_number:
        parts.append(f"Khoản {clause_number}")

    if point_number:
        parts.append(f"Điểm {point_number}")

    return " - ".join(parts) or "Không rõ vị trí"


def shorten(
    value: Any,
    max_length: int = 500,
) -> str:
    if not isinstance(value, str):
        return ""

    normalized = " ".join(value.split())

    if len(normalized) <= max_length:
        return normalized

    return normalized[:max_length].rstrip() + "..."


def main() -> int:
    args = parse_args()

    collection_name = (
        args.collection
        or os.getenv(
            "QDRANT_SPARSE_COLLECTION",
            "legal_units_bm25",
        )
    )

    cache_path = resolve_project_path(
        os.getenv(
            "FASTEMBED_CACHE_PATH",
            ".cache/fastembed",
        )
    )

    sparse_model = BM25SparseEmbeddingModel(
        model_name=os.getenv(
            "SPARSE_MODEL_NAME",
            "Qdrant/bm25",
        ),
        cache_dir=cache_path,
        language=os.getenv(
            "SPARSE_LANGUAGE",
            "english",
        ),
        disable_stemmer=parse_bool(
            os.getenv("SPARSE_DISABLE_STEMMER"),
            default=True,
        ),
        batch_size=int(
            os.getenv("SPARSE_BATCH_SIZE", "128")
        ),
    )

    qdrant_client = create_qdrant_client(
        url=os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        ),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )

    retriever = SparseLegalRetriever(
        embedding_model=sparse_model,
        qdrant_client=qdrant_client,
        collection_name=collection_name,
        sparse_vector_name=os.getenv(
            "QDRANT_SPARSE_VECTOR_NAME",
            "bm25",
        ),
    )

    started_at = time.perf_counter()

    results = retriever.search(
        args.query,
        limit=args.limit,
        law_id=args.law_id,
        include_repealed=args.include_repealed,
    )

    elapsed_seconds = time.perf_counter() - started_at

    print()
    print("=" * 90)
    print("PIPELINE: BM25 sparse")
    print("QUERY:", args.query)
    print("COLLECTION:", collection_name)
    print("RESULTS:", len(results))
    print(f"LATENCY: {elapsed_seconds:.4f} giây")
    print("=" * 90)

    for rank, result in enumerate(results, start=1):
        payload = result.payload

        print()
        print(f"[{rank}] BM25 score: {result.score:.6f}")
        print("Chunk ID:", payload.get("chunk_id"))
        print("Luật:", payload.get("law_name"))
        print(
            "Vị trí:",
            format_legal_position(payload),
        )
        print(
            "Tiêu đề điều:",
            payload.get("article_title"),
        )
        print(
            "Loại chunk:",
            payload.get("unit_type"),
        )
        print(
            "Nội dung:",
            shorten(payload.get("content_clean")),
        )
        print("-" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())