"""Create the Qdrant collection for legal retrieval."""

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
from app.infrastructure.qdrant.collections import create_legal_collection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the legal Qdrant collection.",
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the collection if it already exists.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    qdrant_url = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333",
    )
    api_key = os.getenv("QDRANT_API_KEY") or None
    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "legal_units_bge_m3_finetuned",
    )
    vector_size = int(
        os.getenv("EMBEDDING_DIMENSION", "1024")
    )

    client = create_qdrant_client(
        url=qdrant_url,
        api_key=api_key,
    )

    try:
        create_legal_collection(
            client,
            collection_name=collection_name,
            vector_size=vector_size,
            recreate=args.recreate,
        )

        info = client.get_collection(
            collection_name=collection_name,
        )
    except Exception as exc:
        print(f"Không thể tạo collection: {exc}")
        return 1

    print("Qdrant collection created successfully")
    print("Collection:", collection_name)
    print("Vector dimension:", vector_size)
    print("Distance: Cosine")
    print("Points:", info.points_count)
    print("Indexed payload fields:")

    for field_name in info.payload_schema:
        print(f"  - {field_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())