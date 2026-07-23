"""Dense legal retrieval using BGE-M3 and Qdrant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from app.infrastructure.embeddings.bge_m3 import BGEM3EmbeddingModel


@dataclass(frozen=True)
class DenseSearchResult:
    """One dense retrieval result."""

    point_id: str
    score: float
    payload: dict[str, Any]


class DenseLegalRetriever:
    """Retrieve legal chunks from Qdrant using dense embeddings."""

    def __init__(
        self,
        *,
        embedding_model: BGEM3EmbeddingModel,
        qdrant_client: QdrantClient,
        collection_name: str,
    ) -> None:
        self.embedding_model = embedding_model
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        law_id: str | None = None,
        include_repealed: bool = False,
    ) -> list[DenseSearchResult]:
        """Search for legal chunks relevant to a query."""

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query không được rỗng.")

        if limit <= 0:
            raise ValueError("limit phải lớn hơn 0.")

        query_vector = self.embedding_model.encode_query(
            cleaned_query
        )

        must_conditions: list[models.Condition] = [
            models.FieldCondition(
                key="is_retrievable",
                match=models.MatchValue(value=True),
            )
        ]

        if not include_repealed:
            must_conditions.extend(
                [
                    models.FieldCondition(
                        key="document_status",
                        match=models.MatchValue(value="effective"),
                    ),
                    models.FieldCondition(
                        key="provision_status",
                        match=models.MatchValue(value="effective"),
                    ),
                ]
            )

        if law_id:
            must_conditions.append(
                models.FieldCondition(
                    key="law_id",
                    match=models.MatchValue(
                        value=law_id.strip()
                    ),
                )
            )

        response = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            query_filter=models.Filter(
                must=must_conditions,
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        results: list[DenseSearchResult] = []

        for point in response.points:
            results.append(
                DenseSearchResult(
                    point_id=str(point.id),
                    score=float(point.score),
                    payload=dict(point.payload or {}),
                )
            )

        return results