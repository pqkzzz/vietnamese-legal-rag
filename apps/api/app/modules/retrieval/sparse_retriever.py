"""BM25 sparse retrieval for Vietnamese legal documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from app.infrastructure.embeddings.bm25 import (
    BM25SparseEmbeddingModel,
)


@dataclass(frozen=True)
class SparseSearchResult:
    """One BM25 sparse retrieval result."""

    point_id: str
    score: float
    payload: dict[str, Any]


class SparseLegalRetriever:
    """Retrieve legal chunks using BM25 sparse vectors."""

    def __init__(
        self,
        *,
        embedding_model: BM25SparseEmbeddingModel,
        qdrant_client: QdrantClient,
        collection_name: str,
        sparse_vector_name: str = "bm25",
    ) -> None:
        if not collection_name.strip():
            raise ValueError("collection_name không được rỗng.")

        if not sparse_vector_name.strip():
            raise ValueError("sparse_vector_name không được rỗng.")

        self.embedding_model = embedding_model
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name.strip()
        self.sparse_vector_name = sparse_vector_name.strip()

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        law_id: str | None = None,
        include_repealed: bool = False,
    ) -> list[SparseSearchResult]:
        """Search legal chunks using a BM25 query vector."""

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query không được rỗng.")

        if limit <= 0:
            raise ValueError("limit phải lớn hơn 0.")

        sparse_embedding = self.embedding_model.encode_query(
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
                        match=models.MatchValue(
                            value="effective"
                        ),
                    ),
                    models.FieldCondition(
                        key="provision_status",
                        match=models.MatchValue(
                            value="effective"
                        ),
                    ),
                ]
            )

        if law_id is not None:
            cleaned_law_id = law_id.strip()

            if not cleaned_law_id:
                raise ValueError(
                    "law_id không được là chuỗi rỗng."
                )

            must_conditions.append(
                models.FieldCondition(
                    key="law_id",
                    match=models.MatchValue(
                        value=cleaned_law_id
                    ),
                )
            )

        response = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=models.SparseVector(
                indices=sparse_embedding.indices,
                values=sparse_embedding.values,
            ),
            using=self.sparse_vector_name,
            query_filter=models.Filter(
                must=must_conditions,
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            SparseSearchResult(
                point_id=str(point.id),
                score=float(point.score),
                payload=dict(point.payload or {}),
            )
            for point in response.points
        ]