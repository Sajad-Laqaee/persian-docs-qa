import logging
from functools import lru_cache
from langchain_openai import ChatOpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm():
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        temperature=0.1,
        timeout=60,
    )