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

    exists = client.collection_exists(
        collection_name=collection_name,
    )

    if exists and recreate:
        client.delete_collection(
            collection_name=collection_name,
        )
        exists = False

    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    for field_name, field_schema in PAYLOAD_INDEXES.items():
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
            wait=True,
        )