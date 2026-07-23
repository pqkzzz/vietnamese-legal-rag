"""BGE-M3 embedding adapter for CPU inference."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


class BGEM3EmbeddingModel:
    """Load and run a fine-tuned BGE-M3 SentenceTransformer model."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str = "cpu",
        batch_size: int = 2,
        max_length: int = 512,
    ) -> None:
        self.model_path = Path(model_path).resolve()
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy model tại: {self.model_path}"
            )

        if not self.model_path.is_dir():
            raise NotADirectoryError(
                f"Model path không phải thư mục: {self.model_path}"
            )

        self.model = SentenceTransformer(
            str(self.model_path),
            device=self.device,
            local_files_only=True,
        )

        self.model.max_seq_length = self.max_length

        dimension = self.model.get_embedding_dimension()

        if dimension is None:
            raise RuntimeError(
                "Không xác định được kích thước embedding của model."
            )

        self._dimension = int(dimension)

    @property
    def dimension(self) -> int:
        """Return embedding vector dimension."""

        return self._dimension

    def encode_documents(
        self,
        texts: Sequence[str],
        *,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode document texts into dense vectors."""

        cleaned_texts = [text.strip() for text in texts]

        if not cleaned_texts:
            return np.empty(
                shape=(0, self.dimension),
                dtype=np.float32,
            )

        if any(not text for text in cleaned_texts):
            raise ValueError(
                "Danh sách embedding text chứa phần tử rỗng."
            )

        vectors = self.model.encode(
            cleaned_texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )

        vectors = np.asarray(vectors, dtype=np.float32)

        expected_shape = (len(cleaned_texts), self.dimension)

        if vectors.shape != expected_shape:
            raise RuntimeError(
                "Embedding shape không hợp lệ. "
                f"Expected={expected_shape}, actual={vectors.shape}"
            )

        if not np.isfinite(vectors).all():
            raise RuntimeError(
                "Document embedding chứa NaN hoặc Infinity."
            )

        return vectors

    def encode_query(self, query: str) -> np.ndarray:
        """Encode one search query into a dense vector."""

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query không được rỗng.")

        vector = self.model.encode(
            cleaned_query,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vector = np.asarray(vector, dtype=np.float32)

        expected_shape = (self.dimension,)

        if vector.shape != expected_shape:
            raise RuntimeError(
                "Query embedding shape không hợp lệ. "
                f"Expected={expected_shape}, actual={vector.shape}"
            )

        if not np.isfinite(vector).all():
            raise RuntimeError(
                "Query embedding chứa NaN hoặc Infinity."
            )

        return vector