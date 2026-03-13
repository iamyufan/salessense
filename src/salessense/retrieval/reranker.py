"""Cohere Rerank wrapper: takes top-K hybrid results, returns top-N reranked."""
import cohere

from salessense.config import settings
from salessense.retrieval.hybrid_search import SearchResult

_client: cohere.Client | None = None


def _get_cohere() -> cohere.Client:
    global _client
    if _client is None:
        _client = cohere.Client(api_key=settings.cohere_api_key)
    return _client


def rerank(
    query: str,
    candidates: list[SearchResult],
    top_n: int = settings.rerank_top_n,
) -> list[SearchResult]:
    """
    Rerank candidates using Cohere Rerank API.

    Returns top_n results sorted by relevance score (highest first).
    """
    if not candidates:
        return []

    co = _get_cohere()
    documents = [c.content for c in candidates]

    response = co.rerank(
        model=settings.rerank_model,
        query=query,
        documents=documents,
        top_n=top_n,
        return_documents=False,
    )

    reranked = []
    for result in response.results:
        candidate = candidates[result.index]
        candidate.score = result.relevance_score
        reranked.append(candidate)

    return reranked
