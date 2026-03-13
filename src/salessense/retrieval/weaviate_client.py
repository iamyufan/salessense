"""Weaviate v4 client factory and schema initialization."""
import weaviate
import weaviate.classes as wvc
from weaviate.client import WeaviateClient

from salessense.config import settings


def get_client() -> WeaviateClient:
    """Return a connected Weaviate v4 client."""
    return weaviate.connect_to_local(
        host=settings.weaviate_url.replace("http://", "").split(":")[0],
        port=int(settings.weaviate_url.split(":")[-1]),
        grpc_port=50051,
    )


def init_schema(client: WeaviateClient) -> None:
    """Create the SalesDocument collection if it does not exist."""
    collection_name = settings.weaviate_collection

    if client.collections.exists(collection_name):
        return

    client.collections.create(
        name=collection_name,
        description="Sales call transcripts, deal notes, battlecards, and playbooks",
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
            distance_metric=wvc.config.VectorDistances.COSINE,
        ),
        properties=[
            wvc.config.Property(
                name="content",
                data_type=wvc.config.DataType.TEXT,
                description="Chunk text content",
                index_filterable=True,
                index_searchable=True,  # BM25
            ),
            wvc.config.Property(
                name="doc_type",
                data_type=wvc.config.DataType.TEXT,
                description="transcript | deal_note | battlecard | playbook",
                index_filterable=True,
                index_searchable=False,
            ),
            wvc.config.Property(
                name="industry",
                data_type=wvc.config.DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
            ),
            wvc.config.Property(
                name="icp",
                data_type=wvc.config.DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
            ),
            wvc.config.Property(
                name="source_id",
                data_type=wvc.config.DataType.TEXT,
                index_filterable=True,
                index_searchable=False,
            ),
            wvc.config.Property(
                name="chunk_index",
                data_type=wvc.config.DataType.INT,
                index_filterable=True,
            ),
        ],
    )
