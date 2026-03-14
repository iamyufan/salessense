"""Load CallHome English transcripts from HuggingFace."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawDocument:
    text: str
    source_id: str
    doc_type: str
    metadata: dict


def load_callhome(cache_dir: str | Path | None = None) -> list[RawDocument]:
    """
    Download and yield CallHome English transcripts from HuggingFace.

    Dataset: talkbank/callhome (English subset)
    ~1,500 telephone conversation transcripts.
    """
    from datasets import load_dataset

    ds = load_dataset("talkbank/callhome", "eng", split="data", cache_dir=str(cache_dir) if cache_dir else None)
    ds = ds.remove_columns([col for col in ds.column_names if col not in ("text", "transcript", "id", "file")])
    docs: list[RawDocument] = []
    for i, row in enumerate(ds):
        # CallHome rows have a 'text' field with the full transcript
        text = row.get("text") or row.get("transcript") or ""
        if not text.strip():
            continue
        docs.append(
            RawDocument(
                text=text,
                source_id=f"callhome_{i:05d}",
                doc_type="transcript",
                metadata={"dataset": "callhome", "row_index": i},
            )
        )
    return docs
