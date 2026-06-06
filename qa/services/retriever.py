import logging
from qdrant_client.models import Prefetch, FusionQuery, Fusion, SparseVector, Filter, FieldCondition, MatchValue

from core.embeddings import get_embeddings
from core.vectorstore import get_qdrant_client, get_bm25_encoder
from django.conf import settings

logger = logging.getLogger(__name__)


def hybrid_search(query: str, limit: int = 5, fetch_k: int = 20, document_id=None):
    """
    fetch_k: number of candidates to retrieve for reranking (larger set)
    limit: final number of results (after reranking)
    """
    client = get_qdrant_client()
    embeddings = get_embeddings()
    bm25 = get_bm25_encoder()

    dense_vec = embeddings.embed_query(f"query: {query}")
    sparse = bm25.encode_query(query)

    prefetch = [
        Prefetch(query=dense_vec, using="dense", limit=fetch_k),
    ]
    if sparse:
        prefetch.append(
            Prefetch(
                query=SparseVector(
                    indices=list(sparse.keys()),
                    values=list(sparse.values()),
                ),
                using="sparse",
                limit=fetch_k,
            )
        )

    query_filter = None
    if document_id:
        query_filter = Filter(
            must=[FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            )]
        )

    result = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        prefetch=prefetch,
        query=FusionQuery(fusion=Fusion.RRF),
        query_filter=query_filter, # filter
        limit=fetch_k,   # large candidate set for reranking
    )

    # dedup
    seen = set()
    unique = []
    for p in result.points:
        key = p.payload.get("content", "")[:100]
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique  # returning all candidates; reranking is handled in the chain

def dense_search(query: str, limit: int = 5):
    """Dense-only search (fallback / simple mode)."""
    client = get_qdrant_client()
    embeddings = get_embeddings()

    dense_vec = embeddings.embed_query(f"query: {query}")

    result = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=dense_vec,
        using="dense",
        limit=limit,
    )
    return result.points