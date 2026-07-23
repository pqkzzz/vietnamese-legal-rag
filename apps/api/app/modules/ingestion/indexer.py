"""Build and upsert legal retrieval points into Qdrant."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from qdrant_client import QdrantClient, models


def create_point_id(chunk_id: str) -> str:
    """Create a deterministic UUID from a legal chunk ID."""

    cleaned_chunk_id = chunk_id.strip()

    if not cleaned_chunk_id:
        raise ValueError("chunk_id không được rỗng.")

    return str(
        uuid5(
            NAMESPACE_URL,
            f"vietnamese-legal-rag:{cleaned_chunk_id}",
        )
    )


def build_qdrant_payload(
    chunk: dict[str, Any],
) -> dict[str, Any]:
    """Flatten one retrieval chunk into a Qdrant payload."""

    chunk_id = chunk.get("chunk_id")
    source_unit_id = chunk.get("source_unit_id")
    unit_type = chunk.get("unit_type")
    embedding_text = chunk.get("embedding_text")
    raw_payload = chunk.get("payload")

    if not isinstance(chunk_id, str) or not chunk_id.strip():
        raise ValueError("Retrieval chunk thiếu chunk_id hợp lệ.")

    if not isinstance(source_unit_id, str) or not source_unit_id.strip():
        raise ValueError(
            f"Chunk {chunk_id} thiếu source_unit_id hợp lệ."
        )

    if not isinstance(unit_type, str) or not unit_type.strip():
        raise ValueError(
            f"Chunk {chunk_id} thiếu unit_type hợp lệ."
        )

    if not isinstance(embedding_text, str) or not embedding_text.strip():
        raise ValueError(
            f"Chunk {chunk_id} thiếu embedding_text hợp lệ."
        )

    if not isinstance(raw_payload, dict):
        raise ValueError(
            f"Chunk {chunk_id} có payload không hợp lệ."
        )

    # Các metadata trong JSONL được đưa lên cấp cao nhất.
    # Điều này giúp payload indexes hoạt động đúng.
    payload = dict(raw_payload)

    payload.update(
        {
            "chunk_id": chunk_id.strip(),
            "source_unit_id": source_unit_id.strip(),
            "unit_type": unit_type.strip(),
            "embedding_text": embedding_text.strip(),
        }
    )

    return payload


def build_points(
    chunks: Sequence[dict[str, Any]],
    vectors: np.ndarray,
) -> list[models.PointStruct]:
    """Build Qdrant PointStruct objects from chunks and vectors."""

    if vectors.ndim != 2:
        raise ValueError(
            f"Vectors phải là ma trận hai chiều: {vectors.shape}"
        )

    if len(chunks) != vectors.shape[0]:
        raise ValueError(
            "Số retrieval chunks không khớp số vectors: "
            f"chunks={len(chunks)}, vectors={vectors.shape[0]}"
        )

    points: list[models.PointStruct] = []

    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk_id = chunk["chunk_id"]

        if not np.isfinite(vector).all():
            raise ValueError(
                f"Vector của chunk {chunk_id} chứa NaN hoặc Infinity."
            )

        points.append(
            models.PointStruct(
                id=create_point_id(chunk_id),
                vector=vector.astype(np.float32).tolist(),
                payload=build_qdrant_payload(chunk),
            )
        )

    return points


def upsert_points(
    client: QdrantClient,
    *,
    collection_name: str,
    points: Sequence[models.PointStruct],
) -> None:
    """Upsert one batch of points and wait for completion."""

    if not points:
        return

    client.upsert(
        collection_name=collection_name,
        points=list(points),
        wait=True,
    )