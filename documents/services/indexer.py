import logging
import uuid
from qdrant_client.models import PointStruct, SparseVector

from core.embeddings import get_embeddings
from core.vectorstore import (
    get_qdrant_client, ensure_collection,
    get_bm25_encoder, rebuild_bm25_vocab,
)
from django.conf import settings

logger = logging.getLogger(__name__)


def index_document(document, rebuild_vocab=True):
    """
    Index all document chunks into Qdrant (dense + sparse).
    """
    # Rebuild BM25 vocabulary first so tokens from the new document are recognized
    if rebuild_vocab:
        rebuild_bm25_vocab()

    ensure_collection()
    client = get_qdrant_client()
    embeddings = get_embeddings()
    bm25 = get_bm25_encoder()

    chunks = list(document.chunks.all())
    if not chunks:
        logger.warning(f"Document '{document.title}' has no chunks.")
        return 0

    texts = [f"passage: {c.content}" for c in chunks]
    dense_vectors = embeddings.embed_documents(texts)

    points = []
    for chunk, dense_vec in zip(chunks, dense_vectors):
        point_id = str(uuid.uuid4())
        chunk.vector_id = point_id

        # sparse vector from BM25
        sparse = bm25.encode_document(chunk.content)

        points.append(
            PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vec,
                    "sparse": SparseVector(
                        indices=list(sparse.keys()),
                        values=list(sparse.values()),
                    ),
                },
                payload={
                    "document_id": document.id,
                    "document_title": document.title,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                },
            )
        )

    from documents.models import DocumentChunk
    DocumentChunk.objects.bulk_update(chunks, ["vector_id"])

    client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=points,
    )

    document.is_indexed = True
    document.save(update_fields=["is_indexed"])

    logger.info(f"Document '{document.title}': {len(points)} chunks indexed (hybrid).")
    return len(points)


def delete_document_from_index(document):
    client = get_qdrant_client()
    vector_ids = [c.vector_id for c in document.chunks.all() if c.vector_id]
    if vector_ids:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=vector_ids,
        )
        logger.info(f"Document '{document.title}': {len(vector_ids)} points deleted.")