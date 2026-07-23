"""BM25 sparse embedding adapter for Vietnamese legal retrieval."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from fastembed import SparseTextEmbedding


_WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class SparseEmbeddingVector:
    """Framework-independent sparse embedding representation."""

    indices: list[int]
    values: list[float]

    def __post_init__(self) -> None:
        if len(self.indices) != len(self.values):
            raise ValueError(
                "Số sparse indices không khớp số sparse values."
            )

        if not self.indices:
            raise ValueError("Sparse vector không được rỗng.")

        if any(index < 0 for index in self.indices):
            raise ValueError("Sparse index không được âm.")

        values_array = np.asarray(
            self.values,
            dtype=np.float32,
        )

        if not np.isfinite(values_array).all():
            raise ValueError(
                "Sparse vector chứa NaN hoặc Infinity."
            )


class BM25SparseEmbeddingModel:
    """Generate BM25 sparse vectors with FastEmbed."""

    def __init__(
        self,
        *,
        model_name: str = "Qdrant/bm25",
        cache_dir: str | Path | None = None,
        language: str = "english",
        disable_stemmer: bool = True,
        batch_size: int = 128,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size phải lớn hơn 0.")

        self.model_name = model_name
        self.language = language
        self.disable_stemmer = disable_stemmer
        self.batch_size = batch_size

        resolved_cache_dir: str | None = None

        if cache_dir is not None:
            cache_path = Path(cache_dir).resolve()
            cache_path.mkdir(parents=True, exist_ok=True)
            resolved_cache_dir = str(cache_path)

        self.model = SparseTextEmbedding(
            model_name=self.model_name,
            cache_dir=resolved_cache_dir,
            language=self.language,
            disable_stemmer=self.disable_stemmer,
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode while preserving Vietnamese diacritics."""

        if not isinstance(text, str):
            raise TypeError("Text phải có kiểu string.")

        normalized = unicodedata.normalize("NFC", text)
        normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()

        if not normalized:
            raise ValueError("Text không được rỗng.")

        return normalized

    @staticmethod
    def _convert_embedding(
        embedding: Any,
    ) -> SparseEmbeddingVector:
        indices_array = np.asarray(
            embedding.indices,
            dtype=np.int64,
        )

        values_array = np.asarray(
            embedding.values,
            dtype=np.float32,
        )

        if indices_array.ndim != 1:
            raise ValueError(
                "Sparse indices phải là mảng một chiều."
            )

        if values_array.ndim != 1:
            raise ValueError(
                "Sparse values phải là mảng một chiều."
            )

        return SparseEmbeddingVector(
            indices=indices_array.tolist(),
            values=values_array.tolist(),
        )

    def encode_documents(
        self,
        texts: Sequence[str],
    ) -> list[SparseEmbeddingVector]:
        """Encode documents using BM25 document weighting."""

        if not texts:
            return []

        normalized_texts = [
            self.normalize_text(text)
            for text in texts
        ]

        embeddings = self.model.embed(
            normalized_texts,
            batch_size=self.batch_size,
        )

        vectors = [
            self._convert_embedding(embedding)
            for embedding in embeddings
        ]

        if len(vectors) != len(normalized_texts):
            raise RuntimeError(
                "Số sparse vectors không khớp số document texts: "
                f"texts={len(normalized_texts)}, "
                f"vectors={len(vectors)}"
            )

        return vectors

    def encode_query(
        self,
        query: str,
    ) -> SparseEmbeddingVector:
        """Encode one search query using BM25 query weighting."""

        normalized_query = self.normalize_text(query)

        embeddings = list(
            self.model.query_embed(normalized_query)
        )

        if len(embeddings) != 1:
            raise RuntimeError(
                "BM25 query phải sinh đúng một sparse vector."
            )

        return self._convert_embedding(embeddings[0])