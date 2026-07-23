"""Run query-aware retrieval from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.modules.retrieval.query_aware_retriever import QueryAwareRetriever  # noqa: E402


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        from app.infrastructure.embeddings.bge_m3 import BGEM3EmbeddingModel
        from app.infrastructure.embeddings.bm25 import BM25SparseEmbeddingModel
        from app.infrastructure.qdrant.client import create_qdrant_client
        from app.modules.retrieval.dense_retriever import DenseLegalRetriever
        from app.modules.retrieval.hybrid_retriever import HybridLegalRetriever
        from app.modules.retrieval.sparse_retriever import SparseLegalRetriever
    except Exception as exc:
        print(f"Cannot import retrieval dependencies: {exc}", file=sys.stderr)
        return 2

    dense_model_path = resolve_project_path(os.getenv("EMBEDDING_MODEL_PATH", "models/bge-m3-finetuned"))
    dense_model = BGEM3EmbeddingModel(
        model_path=dense_model_path,
        device=os.getenv("EMBEDDING_DEVICE", "cpu"),
        batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "2")),
        max_length=int(os.getenv("EMBEDDING_MAX_LENGTH", "512")),
    )
    sparse_model = BM25SparseEmbeddingModel(
        model_name=os.getenv("SPARSE_MODEL_NAME", "Qdrant/bm25"),
        cache_dir=resolve_project_path(os.getenv("FASTEMBED_CACHE_PATH", "models/fastembed")),
    )
    client = create_qdrant_client()
    dense_collection = os.getenv("QDRANT_COLLECTION", "legal_units_bge_m3_finetuned")
    sparse_collection = os.getenv("QDRANT_SPARSE_COLLECTION", "legal_units_bm25")

    dense = DenseLegalRetriever(
        embedding_model=dense_model,
        qdrant_client=client,
        collection_name=dense_collection,
    )
    sparse = SparseLegalRetriever(
        embedding_model=sparse_model,
        qdrant_client=client,
        collection_name=sparse_collection,
        sparse_vector_name=os.getenv("QDRANT_SPARSE_VECTOR_NAME", "bm25"),
    )
    hybrid = HybridLegalRetriever(dense_retriever=dense, sparse_retriever=sparse)
    retriever = QueryAwareRetriever(
        hybrid_retriever=hybrid,
        qdrant_client=client,
        collection_name=dense_collection,
    )
    response = retriever.search(args.query, limit=args.limit)
    print(json.dumps(_jsonable(response.to_dict()), ensure_ascii=False, indent=2))
    return 0


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())



