import logging
from functools import lru_cache
from sentence_transformers import CrossEncoder
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_reranker():
    model_name = getattr(
        settings, "RERANKER_MODEL",
        "BAAI/bge-reranker-v2-m3",
    )
    logger.info(f"Loading reranker model: {model_name}")
    # activation_fn for converting logits into scores
    return CrossEncoder(model_name, max_length=512)


def rerank(query: str, points, top_k: int = 5):
    if not points:
        return []

    model = get_reranker()
    pairs = [(query, p.payload.get("content", "")) for p in points]

    # apply_softmax=False because we want independent score per pair
    scores = model.predict(pairs, show_progress_bar=False)

    scored = list(zip(points, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    result = []
    for point, score in scored[:top_k]:
        point.payload["rerank_score"] = float(score)
        result.append(point)
    return result