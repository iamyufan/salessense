"""Gemini embedding wrapper with batching and retry."""
import time

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from salessense.config import settings

_client = genai.Client(api_key=settings.google_api_key)

# Gemini embedding API rate limit: 100 req/min for gemini-embedding-001
_BATCH_DELAY = 0.6  # seconds between batches


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _embed_batch(texts: list[str], task_type: str) -> list[list[float]]:
    response = _client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in response.embeddings]


def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Embed a list of texts, returning a list of 3072-dim vectors."""
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(_embed_batch(batch, task_type="RETRIEVAL_DOCUMENT"))
        if i + batch_size < len(texts):
            time.sleep(_BATCH_DELAY)
    return all_embeddings


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def embed_query(query: str) -> list[float]:
    """Embed a single query string for retrieval."""
    response = _client.models.embed_content(
        model=settings.embedding_model,
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return response.embeddings[0].values
