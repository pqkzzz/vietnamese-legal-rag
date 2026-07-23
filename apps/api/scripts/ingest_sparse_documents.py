"""Create BM25 vectors from dense-collection payloads and ingest into Qdrant."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from qdrant_client import models


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.embeddings.bm25 import (
    BM25SparseEmbeddingModel,
    SparseEmbeddingVector,
)
from app.infrastructure.qdrant.client import create_qdrant_client


LOGGER = logging.getLogger(__name__)


def parse_bool(value: str | None, default: bool = False) -> bool:
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
        description=(
            "Read embedding_text from the dense collection, "
            "create BM25 vectors and ingest into a sparse collection."
        )
    )

    parser.add_argument(
        "--source-collection",
        default=None,
        help="Dense source collection. Default: QDRANT_COLLECTION.",
    )

    parser.add_argument(
        "--target-collection",
        default=None,
        help=(
            "Sparse target collection. "
            "Default: QDRANT_SPARSE_COLLECTION."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of points processed per batch.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only ingest the first N points for smoke testing.",
    )

    parser.add_argument(
        "--log-every",
        type=int,
        default=500,
        help="Print progress after every N points.",
    )

    return parser.parse_args()


def resolve_cache_path(value: str) -> Path:
    cache_path = Path(value)

    if not cache_path.is_absolute():
        cache_path = PROJECT_ROOT / cache_path

    cache_path.mkdir(parents=True, exist_ok=True)

    return cache_path.resolve()


def validate_payload(
    *,
    point_id: Any,
    payload: dict[str, Any],
) -> str:
    chunk_id = payload.get("chunk_id")
    embedding_text = payload.get("embedding_text")

    if not isinstance(chunk_id, str) or not chunk_id.strip():
        raise ValueError(
            f"Point {point_id} thiếu chunk_id hợp lệ."
        )

    if not isinstance(embedding_text, str):
        raise ValueError(
            f"Chunk {chunk_id} thiếu embedding_text."
        )

    embedding_text = embedding_text.strip()

    if not embedding_text:
        raise ValueError(
            f"Chunk {chunk_id} có embedding_text rỗng."
        )

    # Chỉ kiểm tra các chuỗi mojibake đặc trưng.
# Không dùng "Ã" đơn lẻ vì đây là ký tự hợp lệ trong tiếng Việt,
# ví dụ: "ĐÃ", "MÃ", "XÃ".
    # mojibake_markers = (
    #     "Ã¡",
    #     "Ã ",
    #     "Ã¢",
    #     "Ã£",
    #     "Ã¨",
    #     "Ã©",
    #     "Ãª",
    #     "Ã¬",
    #     "Ã ­",
    #     "Ã²",
    #     "Ã³",
    #     "Ã´",
    #     "Ãµ",
    #     "Ã¹",
    #     "Ãº",
    #     "Ã½",
    #     "Ä‘",
    #     "Ä",
    #     "Æ°",
    #     "Æ¡",
    #     "áº",
    #     "á»",
    #     "Â",
    # )

    # matched_marker = next(
    #     (
    #         marker
    #         for marker in mojibake_markers
    #         if marker in embedding_text
    #     ),
    #     None,
    # )

    # if matched_marker is not None:
    #     raise ValueError(
    #         f"Chunk {chunk_id} có dấu hiệu lỗi encoding: "
    #         f"marker={matched_marker!r}"
    #     )

    return embedding_text


def build_point(
    *,
    point_id: Any,
    payload: dict[str, Any],
    vector: SparseEmbeddingVector,
    sparse_vector_name: str,
) -> models.PointStruct:
    return models.PointStruct(
        id=point_id,
        vector={
            sparse_vector_name: models.SparseVector(
                indices=vector.indices,
                values=vector.values,
            )
        },
        payload=payload,
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    args = parse_args()

    source_collection = (
        args.source_collection
        or os.getenv(
            "QDRANT_COLLECTION",
            "legal_units_bge_m3_finetuned",
        )
    )

    target_collection = (
        args.target_collection
        or os.getenv(
            "QDRANT_SPARSE_COLLECTION",
            "legal_units_bm25",
        )
    )

    sparse_vector_name = os.getenv(
        "QDRANT_SPARSE_VECTOR_NAME",
        "bm25",
    )

    batch_size = (
        args.batch_size
        or int(os.getenv("SPARSE_BATCH_SIZE", "128"))
    )

    if batch_size <= 0:
        LOGGER.error("batch-size phải lớn hơn 0.")
        return 1

    if args.limit is not None and args.limit <= 0:
        LOGGER.error("--limit phải lớn hơn 0.")
        return 1

    cache_path = resolve_cache_path(
        os.getenv(
            "FASTEMBED_CACHE_PATH",
            ".cache/fastembed",
        )
    )

    client = create_qdrant_client(
        url=os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        ),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )

    try:
        if not client.collection_exists(
            collection_name=source_collection,
        ):
            LOGGER.error(
                "Source collection không tồn tại: %s",
                source_collection,
            )
            return 1

        if not client.collection_exists(
            collection_name=target_collection,
        ):
            LOGGER.error(
                "Target collection không tồn tại: %s",
                target_collection,
            )
            return 1

        source_count = client.count(
            collection_name=source_collection,
            exact=True,
        ).count

        target_count_before = client.count(
            collection_name=target_collection,
            exact=True,
        ).count

    except Exception as exc:
        LOGGER.error("Không thể kiểm tra Qdrant: %s", exc)
        return 1

    LOGGER.info("Source collection: %s", source_collection)
    LOGGER.info("Target collection: %s", target_collection)
    LOGGER.info("Source points: %d", source_count)
    LOGGER.info(
        "Target points before ingestion: %d",
        target_count_before,
    )

    LOGGER.info("Loading BM25 model from cache: %s", cache_path)

    try:
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
            batch_size=batch_size,
        )
    except Exception as exc:
        LOGGER.error("Không thể load BM25 model: %s", exc)
        return 1

    offset: Any | None = None
    processed_count = 0
    upserted_count = 0

    try:
        while True:
            if args.limit is not None:
                remaining = args.limit - processed_count

                if remaining <= 0:
                    break

                current_batch_size = min(
                    batch_size,
                    remaining,
                )
            else:
                current_batch_size = batch_size

            records, next_offset = client.scroll(
                collection_name=source_collection,
                limit=current_batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not records:
                break

            payloads: list[dict[str, Any]] = []
            texts: list[str] = []

            for record in records:
                payload = dict(record.payload or {})

                embedding_text = validate_payload(
                    point_id=record.id,
                    payload=payload,
                )

                payloads.append(payload)
                texts.append(embedding_text)

            sparse_vectors = sparse_model.encode_documents(
                texts
            )

            if len(sparse_vectors) != len(records):
                raise RuntimeError(
                    "Số sparse vectors không khớp số records: "
                    f"records={len(records)}, "
                    f"vectors={len(sparse_vectors)}"
                )

            points = [
                build_point(
                    point_id=record.id,
                    payload=payload,
                    vector=sparse_vector,
                    sparse_vector_name=sparse_vector_name,
                )
                for record, payload, sparse_vector in zip(
                    records,
                    payloads,
                    sparse_vectors,
                    strict=True,
                )
            ]

            client.upsert(
                collection_name=target_collection,
                points=points,
                wait=True,
            )

            batch_count = len(points)

            processed_count += batch_count
            upserted_count += batch_count

            if (
                args.log_every > 0
                and (
                    processed_count % args.log_every == 0
                    or batch_count < current_batch_size
                )
            ):
                LOGGER.info(
                    "Processed=%d | Upserted=%d",
                    processed_count,
                    upserted_count,
                )

            if args.limit is not None and processed_count >= args.limit:
                break

            if next_offset is None:
                break

            offset = next_offset

        target_count_after = client.count(
            collection_name=target_collection,
            exact=True,
        ).count

    except KeyboardInterrupt:
        LOGGER.warning(
            "Đã dừng bằng bàn phím. "
            "Các batch upsert thành công vẫn được giữ."
        )
        return 130
    except Exception:
        LOGGER.exception("BM25 ingestion thất bại.")
        return 1

    LOGGER.info("BM25 ingestion completed")
    LOGGER.info("Processed points: %d", processed_count)
    LOGGER.info("Upserted points: %d", upserted_count)
    LOGGER.info(
        "Target points after ingestion: %d",
        target_count_after,
    )
    LOGGER.info(
        "Source collection remains: %d points",
        source_count,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())