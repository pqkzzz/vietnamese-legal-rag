"""Create a sparse-only Qdrant collection for BM25 retrieval."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.qdrant.client import create_qdrant_client
from app.infrastructure.qdrant.collections import (
    create_sparse_legal_collection,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the BM25 sparse Qdrant collection.",
    )

    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Override the sparse collection name from .env.",
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the sparse collection.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    collection_name = (
        args.collection
        or os.getenv(
            "QDRANT_SPARSE_COLLECTION",
            "legal_units_bm25",
        )
    )

    sparse_vector_name = os.getenv(
        "QDRANT_SPARSE_VECTOR_NAME",
        "bm25",
    )

    client = create_qdrant_client(
        url=os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        ),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )

    try:
        create_sparse_legal_collection(
            client,
            collection_name=collection_name,
            sparse_vector_name=sparse_vector_name,
            recreate=args.recreate,
        )

        info = client.get_collection(
            collection_name=collection_name,
        )

    except Exception as exc:
        print(f"Không thể tạo BM25 collection: {exc}")
        return 1

    print()
    print("BM25 sparse collection created successfully")
    print("Collection:", collection_name)
    print("Sparse vector:", sparse_vector_name)
    print("Sparse modifier: IDF")
    print("Points:", info.points_count)
    print("Status:", info.status)
    print("Payload indexes:")

    for field_name in sorted(info.payload_schema):
        print(f"  - {field_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())