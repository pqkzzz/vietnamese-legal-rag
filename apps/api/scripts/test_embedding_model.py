"""Test the local fine-tuned BGE-M3 embedding model."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.infrastructure.embeddings.bge_m3 import BGEM3EmbeddingModel


MODEL_PATH = PROJECT_ROOT / "models" / "bge-m3-finetuned"


def main() -> int:
    embedding_model = BGEM3EmbeddingModel(
        model_path=MODEL_PATH,
        device="cpu",
        batch_size=2,
        max_length=512,
    )

    texts = [
        "Bồi thường về đất là gì?",
        "Điều kiện chuyển nhượng quyền sử dụng đất.",
    ]

    document_vectors = embedding_model.encode_documents(
        texts,
        show_progress=True,
    )

    query_vector = embedding_model.encode_query(
        "Người sử dụng đất có quyền gì?"
    )

    print("Model:", MODEL_PATH)
    print("Device:", embedding_model.device)
    print("Dimension:", embedding_model.dimension)
    print("Document shape:", document_vectors.shape)
    print("Query shape:", query_vector.shape)
    print("Có NaN:", bool(np.isnan(document_vectors).any()))
    print(
        "Document norm:",
        float(np.linalg.norm(document_vectors[0])),
    )
    print(
        "Query norm:",
        float(np.linalg.norm(query_vector)),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())