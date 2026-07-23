"""Create and configure Qdrant collections for legal retrieval."""

from __future__ import annotations

from qdrant_client import QdrantClient, models


PAYLOAD_INDEXES: dict[str, models.PayloadSchemaType] = {
    # Exact identifiers
    "chunk_id": models.PayloadSchemaType.KEYWORD,
    "source_unit_id": models.PayloadSchemaType.KEYWORD,
    "law_id": models.PayloadSchemaType.KEYWORD,
    "article_id": models.PayloadSchemaType.KEYWORD,
    "parent_id": models.PayloadSchemaType.KEYWORD,

    # Legal hierarchy
    "unit_type": models.PayloadSchemaType.KEYWORD,
    "article_number": models.PayloadSchemaType.KEYWORD,
    "clause_number": models.PayloadSchemaType.KEYWORD,
    "point_number": models.PayloadSchemaType.KEYWORD,

    # Legal status and retrieval filter
    "document_status": models.PayloadSchemaType.KEYWORD,
    "provision_status": models.PayloadSchemaType.KEYWORD,
    "is_retrievable": models.PayloadSchemaType.BOOL,
}


def create_legal_collection(
    client: QdrantClient,
    *,
    collection_name: str,
    vector_size: int,
    recreate: bool = False,
) -> None:
    """Create the legal vector collection and payload indexes."""

    if vector_size <= 0:
        raise ValueError("vector_size must be greater than 0.")

    cleaned_collection_name = collection_name.strip()
    if not cleaned_collection_name:
        raise ValueError("collection_name must not be empty.")

    exists = client.collection_exists(
        collection_name=cleaned_collection_name,
    )

    if exists and recreate:
        client.delete_collection(
            collection_name=cleaned_collection_name,
        )
        exists = False

    if not exists:
        client.create_collection(
            collection_name=cleaned_collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    _create_payload_indexes(client, cleaned_collection_name)

def create_sparse_legal_collection(
    client: QdrantClient,
    *,
    collection_name: str,
    sparse_vector_name: str = "bm25",
    recreate: bool = False,
) -> None:
    """Create a sparse-only Qdrant collection for BM25 retrieval."""

    cleaned_collection_name = collection_name.strip()
    cleaned_vector_name = sparse_vector_name.strip()

    if not cleaned_collection_name:
        raise ValueError("collection_name must not be empty.")
    if not cleaned_vector_name:
        raise ValueError("sparse_vector_name must not be empty.")

    exists = client.collection_exists(
        collection_name=cleaned_collection_name,
    )

    if exists and recreate:
        client.delete_collection(
            collection_name=cleaned_collection_name,
        )
        exists = False

    if not exists:
        client.create_collection(
            collection_name=cleaned_collection_name,
            vectors_config={},
            sparse_vectors_config={
                cleaned_vector_name: models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
        )

    _create_payload_indexes(client, cleaned_collection_name)


def _create_payload_indexes(
    client: QdrantClient,
    collection_name: str,
) -> None:
    """Create configured payload indexes for a Qdrant collection."""

    for field_name, field_schema in PAYLOAD_INDEXES.items():
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
            wait=True,
        )
