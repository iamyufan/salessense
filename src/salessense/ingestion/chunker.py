"""Text chunking for the ingestion pipeline."""
from dataclasses import dataclass, field

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from salessense.config import settings


@dataclass
class Chunk:
    content: str
    source_id: str
    chunk_index: int
    doc_type: str
    metadata: dict = field(default_factory=dict)


def _token_len(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def _make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=_token_len,
        separators=["\n\n", "\n", " ", ""],
    )


def chunk_document(
    text: str,
    source_id: str,
    doc_type: str,
    metadata: dict | None = None,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> list[Chunk]:
    """Split a document into overlapping token-bounded chunks."""
    # For transcripts, split on speaker turns first
    if doc_type == "transcript":
        separators = ["\nAgent:", "\nCustomer:", "\nSpeaker", "\n\n", "\n", " ", ""]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=_token_len,
            separators=separators,
        )
    else:
        splitter = _make_splitter(chunk_size, chunk_overlap)

    texts = splitter.split_text(text)
    return [
        Chunk(
            content=t,
            source_id=source_id,
            chunk_index=i,
            doc_type=doc_type,
            metadata=metadata or {},
        )
        for i, t in enumerate(texts)
    ]
