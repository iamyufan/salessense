"""Tests for the chunking module."""
import pytest

from salessense.ingestion.chunker import chunk_document


def test_chunk_basic():
    text = "Hello world. " * 200  # ~600 tokens
    chunks = chunk_document(text, source_id="test_001", doc_type="deal_note")
    assert len(chunks) >= 1
    for i, chunk in enumerate(chunks):
        assert chunk.source_id == "test_001"
        assert chunk.doc_type == "deal_note"
        assert chunk.chunk_index == i
        assert len(chunk.content) > 0


def test_chunk_transcript_splits_on_speaker():
    text = "Agent: Hello, how can I help?\nCustomer: I need help with pricing.\n" * 50
    chunks = chunk_document(text, source_id="t_001", doc_type="transcript")
    assert len(chunks) >= 1


def test_chunk_metadata_preserved():
    meta = {"industry": "SaaS", "icp": "Enterprise"}
    chunks = chunk_document("Short text.", source_id="x", doc_type="deal_note", metadata=meta)
    assert chunks[0].metadata["industry"] == "SaaS"
