import logging
import re
from hazm import Normalizer
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
_normalizer = Normalizer()

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,            # smaller = more precise
    chunk_overlap=150,         # higher overlap = better context preservation
    separators=["\n\n", "\n", ".", "؟", "!", "؛", " "],  # removed "،" to reduce noise splits
    length_function=len,
    keep_separator=True,       # keep separators in chunks
)


def normalize_text(text: str) -> str:
    text = _normalizer.normalize(text)
    # remove wiki-style citations like [22], [15]
    text = re.sub(r"\[\s*[\d۰-۹]+\s*\]", "", text)
    # normalize excessive whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    text = normalize_text(text)
    if not text.strip():
        return []

    chunks = _splitter.split_text(text)

    cleaned = []
    for c in chunks:
        c = c.strip().lstrip("،.؛ ").strip()
        if len(c) > 40:  # higher threshold for noise filtering
            cleaned.append(c)

    logger.info(f"Text split into {len(cleaned)} chunks.")
    return cleaned