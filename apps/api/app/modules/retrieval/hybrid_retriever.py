"""Hybrid dense and BM25 retrieval using Reciprocal Rank Fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.retrieval.dense_retriever import (
    DenseLegalRetriever,
)
from app.modules.retrieval.sparse_retriever import (
    SparseLegalRetriever,
)


@dataclass(frozen=True)
class HybridSearchResult:
    """One result returned after Dense + BM25 RRF fusion."""

    point_id: str
    score: float
    payload: dict[str, Any]

    dense_rank: int | None
    sparse_rank: int | None

    dense_score: float | None
    sparse_score: float | None


class HybridLegalRetriever:
    """Combine Dense and BM25 results using RRF."""

    def __init__(
        self,
        *,
        dense_retriever: DenseLegalRetriever,
        sparse_retriever: SparseLegalRetriever,
        candidate_limit: int = 50,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
    ) -> None:
        if candidate_limit <= 0:
            raise ValueError(
                "candidate_limit phải lớn hơn 0."
            )

        if rrf_k < 0:
            raise ValueError("rrf_k không được âm.")

        if dense_weight < 0:
            raise ValueError(
                "dense_weight không được âm."
            )

        if sparse_weight < 0:
            raise ValueError(
                "sparse_weight không được âm."
            )

        if dense_weight == 0 and sparse_weight == 0:
            raise ValueError(
                "Ít nhất một trọng số phải lớn hơn 0."
            )

        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

        self.candidate_limit = candidate_limit
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

    @staticmethod
    def _get_result_key(
        point_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Prefer chunk_id as the identity of one legal unit."""

        chunk_id = payload.get("chunk_id")

        if isinstance(chunk_id, str) and chunk_id.strip():
            return chunk_id.strip()

        return point_id

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        law_id: str | None = None,
    ) -> list[HybridSearchResult]:
        """Retrieve candidates and fuse their ranks using RRF."""

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query không được rỗng.")

        if limit <= 0:
            raise ValueError("limit phải lớn hơn 0.")

        candidate_limit = max(
            limit,
            self.candidate_limit,
        )

        dense_results = self.dense_retriever.search(
            cleaned_query,
            limit=candidate_limit,
            law_id=law_id,
        )

        sparse_results = self.sparse_retriever.search(
            cleaned_query,
            limit=candidate_limit,
            law_id=law_id,
        )

        merged: dict[str, dict[str, Any]] = {}

        for rank, result in enumerate(
            dense_results,
            start=1,
        ):
            point_id = str(result.point_id)
            payload = dict(result.payload or {})

            result_key = self._get_result_key(
                point_id,
                payload,
            )

            item = merged.setdefault(
                result_key,
                {
                    "point_id": point_id,
                    "payload": payload,
                    "rrf_score": 0.0,
                    "dense_rank": None,
                    "sparse_rank": None,
                    "dense_score": None,
                    "sparse_score": None,
                },
            )

            item["rrf_score"] += (
                self.dense_weight
                / (self.rrf_k + rank)
            )

            item["dense_rank"] = rank
            item["dense_score"] = float(result.score)

        for rank, result in enumerate(
            sparse_results,
            start=1,
        ):
            point_id = str(result.point_id)
            payload = dict(result.payload or {})

            result_key = self._get_result_key(
                point_id,
                payload,
            )

            item = merged.setdefault(
                result_key,
                {
                    "point_id": point_id,
                    "payload": payload,
                    "rrf_score": 0.0,
                    "dense_rank": None,
                    "sparse_rank": None,
                    "dense_score": None,
                    "sparse_score": None,
                },
            )

            item["rrf_score"] += (
                self.sparse_weight
                / (self.rrf_k + rank)
            )

            item["sparse_rank"] = rank
            item["sparse_score"] = float(result.score)

            # Trường hợp payload phía Dense rỗng hoặc thiếu.
            if not item["payload"]:
                item["payload"] = payload

        ranked_items = sorted(
            merged.values(),
            key=lambda item: (
                -float(item["rrf_score"]),
                -int(item["dense_rank"] is not None),
                -int(item["sparse_rank"] is not None),
                min(
                    item["dense_rank"]
                    if item["dense_rank"] is not None
                    else candidate_limit + 1,
                    item["sparse_rank"]
                    if item["sparse_rank"] is not None
                    else candidate_limit + 1,
                ),
                str(
                    item["payload"].get(
                        "chunk_id",
                        item["point_id"],
                    )
                ),
            ),
        )

        return [
            HybridSearchResult(
                point_id=str(item["point_id"]),
                score=float(item["rrf_score"]),
                payload=dict(item["payload"]),
                dense_rank=item["dense_rank"],
                sparse_rank=item["sparse_rank"],
                dense_score=item["dense_score"],
                sparse_score=item["sparse_score"],
            )
            for item in ranked_items[:limit]
        ]