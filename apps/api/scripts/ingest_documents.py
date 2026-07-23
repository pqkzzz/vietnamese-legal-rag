"""Embed legal retrieval chunks and ingest them into Qdrant."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from qdrant_client import models


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.infrastructure.embeddings.bge_m3 import BGEM3EmbeddingModel
from app.infrastructure.qdrant.client import create_qdrant_client
from app.modules.ingestion.indexer import build_points, upsert_points


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Embed retrieval JSONL chunks and ingest them into Qdrant."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "retrieval",
        help="Directory containing *_chunks.jsonl files.",
    )

    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Only ingest one JSONL file.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after ingesting this many chunks.",
    )

    parser.add_argument(
        "--log-every",
        type=int,
        default=100,
        help="Log progress after this many chunks.",
    )

    return parser.parse_args()


def discover_input_files(
    input_dir: Path,
    selected_file: Path | None,
) -> list[Path]:
    """Return retrieval JSONL files in deterministic order."""

    if selected_file is not None:
        file_path = (
            selected_file
            if selected_file.is_absolute()
            else input_dir / selected_file
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy JSONL file: {file_path}"
            )

        return [file_path.resolve()]

    if not input_dir.exists():
        raise FileNotFoundError(
            f"Không tìm thấy input directory: {input_dir}"
        )

    files = sorted(input_dir.glob("*_chunks.jsonl"))

    if not files:
        raise FileNotFoundError(
            f"Không có file *_chunks.jsonl trong {input_dir}"
        )

    return files


def iter_chunks(
    files: list[Path],
) -> Iterator[tuple[dict[str, Any], Path, int]]:
    """Read retrieval chunks line by line."""

    for file_path in files:
        LOGGER.info("Reading %s", file_path.name)

        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(file, start=1):
                stripped_line = line.strip()

                if not stripped_line:
                    continue

                try:
                    chunk = json.loads(stripped_line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"JSON lỗi tại {file_path}:{line_number}: {exc}"
                    ) from exc

                if not isinstance(chunk, dict):
                    raise ValueError(
                        f"Chunk không phải JSON object tại "
                        f"{file_path}:{line_number}"
                    )

                yield chunk, file_path, line_number


def flush_embedding_batch(
    *,
    embedding_model: BGEM3EmbeddingModel,
    chunks: list[dict[str, Any]],
    pending_points: list[models.PointStruct],
) -> None:
    """Embed one text batch and append Qdrant points."""

    if not chunks:
        return

    texts = [
        chunk["embedding_text"]
        for chunk in chunks
    ]

    vectors = embedding_model.encode_documents(
        texts,
        show_progress=False,
    )

    pending_points.extend(
        build_points(
            chunks=chunks,
            vectors=vectors,
        )
    )

    chunks.clear()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    args = parse_args()

    model_path_value = os.getenv(
        "EMBEDDING_MODEL_PATH",
        "models/bge-m3-finetuned",
    )

    model_path = Path(model_path_value)

    if not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path

    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    embedding_batch_size = int(
        os.getenv("EMBEDDING_BATCH_SIZE", "2")
    )
    max_length = int(
        os.getenv("EMBEDDING_MAX_LENGTH", "512")
    )

    qdrant_url = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333",
    )
    qdrant_api_key = os.getenv("QDRANT_API_KEY") or None
    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "legal_units_bge_m3_finetuned",
    )
    upsert_batch_size = int(
        os.getenv("QDRANT_UPSERT_BATCH_SIZE", "64")
    )

    if embedding_batch_size <= 0:
        LOGGER.error("EMBEDDING_BATCH_SIZE phải lớn hơn 0.")
        return 1

    if upsert_batch_size <= 0:
        LOGGER.error("QDRANT_UPSERT_BATCH_SIZE phải lớn hơn 0.")
        return 1

    try:
        input_files = discover_input_files(
            input_dir=args.input_dir.resolve(),
            selected_file=args.file,
        )
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Loading embedding model from %s", model_path)

    try:
        embedding_model = BGEM3EmbeddingModel(
            model_path=model_path,
            device=device,
            batch_size=embedding_batch_size,
            max_length=max_length,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        LOGGER.error("Không thể load embedding model: %s", exc)
        return 1

    client = create_qdrant_client(
        url=qdrant_url,
        api_key=qdrant_api_key,
    )

    try:
        if not client.collection_exists(
            collection_name=collection_name
        ):
            LOGGER.error(
                "Collection chưa tồn tại: %s",
                collection_name,
            )
            return 1
    except Exception as exc:
        LOGGER.error("Không thể kết nối Qdrant: %s", exc)
        return 1

    embedding_chunks: list[dict[str, Any]] = []
    pending_points: list[models.PointStruct] = []

    processed_count = 0
    upserted_count = 0

    try:
        for chunk, file_path, line_number in iter_chunks(input_files):
            if args.limit is not None and processed_count >= args.limit:
                break

            embedding_text = chunk.get("embedding_text")

            if not isinstance(embedding_text, str):
                raise ValueError(
                    f"Thiếu embedding_text tại "
                    f"{file_path}:{line_number}"
                )

            embedding_chunks.append(chunk)
            processed_count += 1

            if len(embedding_chunks) >= embedding_batch_size:
                flush_embedding_batch(
                    embedding_model=embedding_model,
                    chunks=embedding_chunks,
                    pending_points=pending_points,
                )

            if len(pending_points) >= upsert_batch_size:
                batch_count = len(pending_points)

                upsert_points(
                    client,
                    collection_name=collection_name,
                    points=pending_points,
                )

                upserted_count += batch_count
                pending_points.clear()

            if (
                args.log_every > 0
                and processed_count % args.log_every == 0
            ):
                LOGGER.info(
                    "Processed=%d | Upserted=%d",
                    processed_count,
                    upserted_count,
                )

        flush_embedding_batch(
            embedding_model=embedding_model,
            chunks=embedding_chunks,
            pending_points=pending_points,
        )

        if pending_points:
            batch_count = len(pending_points)

            upsert_points(
                client,
                collection_name=collection_name,
                points=pending_points,
            )

            upserted_count += batch_count
            pending_points.clear()

        total_in_collection = client.count(
            collection_name=collection_name,
            exact=True,
        ).count

    except KeyboardInterrupt:
        LOGGER.warning(
            "Đã dừng bằng bàn phím. Các batch đã upsert vẫn được giữ."
        )
        return 130
    except Exception:
        LOGGER.exception("Ingestion thất bại.")
        return 1

    LOGGER.info("Ingestion completed")
    LOGGER.info("Input files: %d", len(input_files))
    LOGGER.info("Processed chunks: %d", processed_count)
    LOGGER.info("Upserted points: %d", upserted_count)
    LOGGER.info(
        "Exact points in collection: %d",
        total_in_collection,
    )
    LOGGER.info("Collection: %s", collection_name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())