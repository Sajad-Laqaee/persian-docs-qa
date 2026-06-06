import os
import logging
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    SparseVectorParams, SparseIndexParams,
)
from django.conf import settings

from core.bm25 import PersianBM25Encoder

logger = logging.getLogger(__name__)

BM25_MODEL_PATH = os.path.join(settings.BASE_DIR, "bm25_model.pkl")


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection():
    """Hybrid collection: dense + sparse."""
    client = get_qdrant_client()
    name = settings.QDRANT_COLLECTION

    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config={
                "dense": VectorParams(
                    size=settings.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False),
                )
            },
        )
        logger.info(f"Hybrid collection '{name}' created.")
    else:
        logger.info(f"Collection '{name}' already exists.")


# ---------- BM25 Encoder Singleton ----------
_bm25_encoder = None


def get_bm25_encoder() -> PersianBM25Encoder:
    """Load encoder from file (or create an empty encoder)."""
    global _bm25_encoder
    if _bm25_encoder is None:
        _bm25_encoder = PersianBM25Encoder()
        if os.path.exists(BM25_MODEL_PATH):
            _bm25_encoder.load(BM25_MODEL_PATH)
            logger.info(f"BM25 encoder loaded from {BM25_MODEL_PATH}.")
        else:
            logger.warning("BM25 file not found. Encoder is empty (rebuild required).")
    return _bm25_encoder


def rebuild_bm25_vocab():
    """
    Rebuild vocabulary from all database chunks.
    Should be called after indexing new documents.
    """
    from documents.models import DocumentChunk

    texts = list(DocumentChunk.objects.values_list("content", flat=True))
    if not texts:
        logger.warning("No chunks available to build BM25 vocabulary.")
        return

    encoder = PersianBM25Encoder()
    encoder.build_vocab_from_texts(texts)
    encoder.save(BM25_MODEL_PATH)

    global _bm25_encoder
    _bm25_encoder = encoder  # refresh singleton

    logger.info(
        f"BM25 vocabulary rebuilt: {len(encoder.vocab)} tokens from {len(texts)} chunks."
    )