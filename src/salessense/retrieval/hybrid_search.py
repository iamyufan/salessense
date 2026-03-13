"""Weaviate hybrid search: BM25 + vector + Relative Score Fusion."""
from dataclasses import dataclass

import weaviate.classes as wvc
from weaviate.client import WeaviateClient

from salessense.config import settings
from salessense.ingestion.embedder import embed_query


@dataclass
class SearchResult:
    content: str
    source_id: str
    doc_type: str
    industry: str
    icp: str
    chunk_index: int
    score: float


def hybrid_search(
    client: WeaviateClient,
    query: str,
    top_k: int = settings.hybrid_top_k,
    alpha: float = settings.hybrid_alpha,
    filters: wvc.query.Filter | None = None,
) -> list[SearchResult]:
    """
    Run hybrid search (BM25 + vector) with Relative Score Fusion.

    Args:
        alpha: 0.0 = pure BM25, 1.0 = pure vector. Default 0.75 (vector-heavy).
    """
    query_vector = embed_query(query)
    collection = client.collections.get(settings.weaviate_collection)

    response = collection.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=top_k,
        fusion_type=wvc.query.HybridFusion.RELATIVE_SCORE,
        return_metadata=wvc.query.MetadataQuery(score=True),
        filters=filters,
        return_properties=["content", "source_id", "doc_type", "industry", "icp", "chunk_index"],
    )

    return [
        SearchResult(
            content=obj.properties["content"],
            source_id=obj.properties["source_id"],
            doc_type=obj.properties["doc_type"],
            industry=obj.properties.get("industry", ""),
            icp=obj.properties.get("icp", ""),
            chunk_index=obj.properties.get("chunk_index", 0),
            score=obj.metadata.score if obj.metadata else 0.0,
        )
        for obj in response.objects
    ]
