"""Ingestion pipeline: load -> chunk -> embed -> upsert into Weaviate."""
import logging
from typing import Literal

from tqdm import tqdm

from salessense.config import settings
from salessense.ingestion.chunker import Chunk, chunk_document
from salessense.ingestion.embedder import embed_texts
from salessense.retrieval.weaviate_client import get_client, init_schema

logger = logging.getLogger(__name__)

SourceType = Literal["callhome", "synthetic", "battlecards", "playbooks"]


def run_ingestion(source: SourceType, dry_run: bool = False) -> int:
    """
    Full ingestion pipeline for a given source type.
    Returns the number of chunks upserted.
    """
    raw_docs = _load_source(source)
    logger.info(f"Loaded {len(raw_docs)} raw documents from source='{source}'")

    all_chunks: list[Chunk] = []
    for doc in raw_docs:
        chunks = chunk_document(
            text=doc.text,
            source_id=doc.source_id,
            doc_type=doc.doc_type,
            metadata=doc.metadata,
        )
        all_chunks.extend(chunks)

    logger.info(f"Produced {len(all_chunks)} chunks")

    if dry_run:
        logger.info("Dry run — skipping embed + upsert")
        return len(all_chunks)

    client = get_client()
    init_schema(client)

    collection = client.collections.get(settings.weaviate_collection)
    batch_size = settings.batch_size

    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Upserting"):
        batch = all_chunks[i : i + batch_size]
        texts = [c.content for c in batch]
        vectors = embed_texts(texts)

        with collection.batch.fixed_size(batch_size=batch_size) as wb:
            for chunk, vector in zip(batch, vectors):
                wb.add_object(
                    properties={
                        "content": chunk.content,
                        "doc_type": chunk.doc_type,
                        "source_id": chunk.source_id,
                        "chunk_index": chunk.chunk_index,
                        "industry": chunk.metadata.get("industry", ""),
                        "icp": chunk.metadata.get("icp", ""),
                    },
                    vector=vector,
                )

    client.close()
    logger.info(f"Upserted {len(all_chunks)} chunks into Weaviate")
    return len(all_chunks)


def _load_source(source: SourceType):
    if source == "callhome":
        from salessense.ingestion.loaders.callhome import load_callhome
        return load_callhome()
    elif source == "synthetic":
        from salessense.ingestion.loaders.synthetic import load_synthetic
        return load_synthetic()
    elif source == "battlecards":
        from salessense.ingestion.loaders.pdf import load_battlecards
        return load_battlecards()
    elif source == "playbooks":
        from salessense.ingestion.loaders.pdf import load_pdfs
        return load_pdfs()
    else:
        raise ValueError(f"Unknown source: {source}")
