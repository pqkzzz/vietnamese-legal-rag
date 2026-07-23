"""Test connection to the local Qdrant instance."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.infrastructure.qdrant.client import create_qdrant_client


def main() -> int:
    client = create_qdrant_client(
        url="http://localhost:6333",
    )

    try:
        collections = client.get_collections()
    except Exception as exc:
        print(f"Không thể kết nối Qdrant: {exc}")
        return 1

    print("Qdrant connection: OK")
    print(
        "Collections:",
        [collection.name for collection in collections.collections],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())