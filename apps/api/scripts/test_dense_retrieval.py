"""Run a manual dense retrieval test against Qdrant."""

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
from app.infrastructure.qdrant.client import (
    create_qdrant_client,
)
from app.modules.retrieval.dense_retriever import (
    DenseLegalRetriever,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test dense legal retrieval.",
    )

    parser.add_argument(
        "query",
        type=str,
        help="Câu hỏi pháp luật cần tìm.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Số kết quả cần trả về.",
    )

    parser.add_argument(
        "--law-id",
        type=str,
        default=None,
        help="Chỉ tìm trong một luật cụ thể.",
    )

    parser.add_argument(
        "--include-repealed",
        action="store_true",
        help="Cho phép tìm điều khoản đã bị bãi bỏ.",
    )

    return parser.parse_args()


def format_legal_position(payload: dict[str, Any]) -> str:
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


def shorten(text: Any, max_length: int = 500) -> str:
    if not isinstance(text, str):
        return ""

    normalized = " ".join(text.split())

    if len(normalized) <= max_length:
        return normalized

    return normalized[:max_length].rstrip() + "..."


def main() -> int:
    args = parse_args()

    model_path = Path(
        os.getenv(
            "EMBEDDING_MODEL_PATH",
            "models/bge-m3-finetuned",
        )
    )

    if not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path

    embedding_model = BGEM3EmbeddingModel(
        model_path=model_path,
        device=os.getenv("EMBEDDING_DEVICE", "cpu"),
        batch_size=int(
            os.getenv("EMBEDDING_BATCH_SIZE", "2")
        ),
        max_length=int(
            os.getenv("EMBEDDING_MAX_LENGTH", "512")
        ),
    )

    qdrant_client = create_qdrant_client(
        url=os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        ),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )

    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "legal_units_bge_m3_finetuned",
    )

    retriever = DenseLegalRetriever(
        embedding_model=embedding_model,
        qdrant_client=qdrant_client,
        collection_name=collection_name,
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
    print("QUERY:", args.query)
    print("COLLECTION:", collection_name)
    print("RESULTS:", len(results))
    print(f"LATENCY: {elapsed_seconds:.3f} giây")
    print("=" * 90)

    for rank, result in enumerate(results, start=1):
        payload = result.payload

        print()
        print(f"[{rank}] Score: {result.score:.6f}")
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