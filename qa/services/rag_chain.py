import time
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings

from core.llm import get_llm
from qa.prompts import SYSTEM_PROMPT, USER_PROMPT
from qa.services.retriever import hybrid_search, dense_search

logger = logging.getLogger(__name__)


def build_context(points) -> str:
    blocks = []
    for i, p in enumerate(points, start=1):
        payload = p.payload
        title = payload.get("document_title", "Unknown")
        content = payload.get("content", "")
        blocks.append(f"[Document {i} - {title}]\n{content}")
    return "\n\n".join(blocks)


def build_sources(points) -> list:
    sources = []
    for p in points:
        payload = p.payload
        sources.append({
            "score": round(float(p.score), 4),
            "rerank_score": round(float(payload.get("rerank_score", 0)), 4),
            "document_id": payload.get("document_id"),
            "document_title": payload.get("document_title"),
            "chunk_index": payload.get("chunk_index"),
            "preview": payload.get("content", "")[:200],
        })
    return sources


def generate_answer(query: str, limit: int = 5, use_hybrid: bool = True, document_id=None):
    timings = {}

    # 1) Retrieve (large candidate set)
    t0 = time.perf_counter()
    if use_hybrid:
        candidates = hybrid_search(query, limit=limit, fetch_k=20, document_id=document_id)
        search_mode = "hybrid"
    else:
        candidates = dense_search(query, limit=20)
        search_mode = "dense"
    timings["retrieval"] = round(time.perf_counter() - t0, 3)

    if not candidates:
        logger.info(f"No results | query='{query[:50]}'")
        return {
            "answer": "Not enough information available in the documents.",
            "sources": [], "retrieved_chunks": [], "search_mode": search_mode,
        }

    # 2) Rerank (select precise top-k)
    if settings.USE_RERANKER:
        from core.reranker import rerank
        t_r = time.perf_counter()
        points = rerank(query, candidates, top_k=limit)
        timings["rerank"] = round(time.perf_counter() - t_r, 3)
        search_mode += "+rerank"
    else:
        points = candidates[:limit]

    context = build_context(points)
    sources = build_sources(points)
    retrieved_chunks = [p.payload for p in points]

    # 3) LLM
    t1 = time.perf_counter()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])
    chain = prompt | get_llm() | StrOutputParser()
    answer = chain.invoke({"context": context, "query": query})
    timings["llm"] = round(time.perf_counter() - t1, 3)

    logger.info(
        f"Answer generated | query='{query[:40]}' | "
        f"retrieval={timings['retrieval']}s | "
        f"rerank={timings.get('rerank', 0)}s | "
        f"llm={timings['llm']}s | results={len(points)}"
    )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks,
        "search_mode": search_mode,
    }