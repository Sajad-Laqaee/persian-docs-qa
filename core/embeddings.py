import logging
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embeddings():
    """
    Singleton for embedding model.
    Model is downloaded on first use (multilingual-e5-base).
    """
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},  # for cosine similarity
    )