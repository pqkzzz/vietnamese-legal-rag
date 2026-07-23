"""Qdrant client factory."""

from __future__ import annotations

from qdrant_client import QdrantClient


def create_qdrant_client(
    url: str = "http://localhost:6333",
    api_key: str | None = None,
) -> QdrantClient:
    """Create a Qdrant client connected to a local or remote server."""

    return QdrantClient(
        url=url,
        api_key=api_key,
        timeout=30,
    )