"""Smoke test for Vietnamese BM25 sparse embeddings."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.infrastructure.embeddings.bm25 import (
    BM25SparseEmbeddingModel,
)


def main() -> int:
    cache_dir = PROJECT_ROOT / ".cache" / "fastembed"

    model = BM25SparseEmbeddingModel(
        model_name="Qdrant/bm25",
        cache_dir=cache_dir,
        language="english",
        disable_stemmer=True,
        batch_size=16,
    )

    document = (
        "Công chứng viên không được công chứng giao dịch "
        "liên quan đến tài sản của bản thân mình."
    )

    query = "công chứng tài sản của bản thân"

    normalized_document = model.normalize_text(document)
    normalized_query = model.normalize_text(query)

    document_vector = model.encode_documents(
        [document]
    )[0]

    query_vector = model.encode_query(query)

    document_values = np.asarray(
        document_vector.values,
        dtype=np.float32,
    )

    query_values = np.asarray(
        query_vector.values,
        dtype=np.float32,
    )

    print("Model:", model.model_name)
    print("Language:", model.language)
    print("Disable stemmer:", model.disable_stemmer)
    print("Cache:", cache_dir)
    print()

    print("Normalized document:")
    print(normalized_document)
    print()

    print("Normalized query:")
    print(normalized_query)
    print()

    print(
        "Document sparse indices:",
        len(document_vector.indices),
    )
    print(
        "Document sparse values:",
        len(document_vector.values),
    )
    print(
        "Document finite:",
        bool(np.isfinite(document_values).all()),
    )

    print(
        "Query sparse indices:",
        len(query_vector.indices),
    )
    print(
        "Query sparse values:",
        len(query_vector.values),
    )
    print(
        "Query finite:",
        bool(np.isfinite(query_values).all()),
    )

    print(
        "Document/query shared token IDs:",
        len(
            set(document_vector.indices)
            & set(query_vector.indices)
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())