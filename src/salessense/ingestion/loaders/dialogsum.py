"""Load DialogSum multi-turn dialogues from HuggingFace."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawDocument:
    text: str
    source_id: str
    doc_type: str
    metadata: dict


def load_dialogsum(cache_dir: str | Path | None = None) -> list[RawDocument]:
    """
    Download and return DialogSum dialogues from HuggingFace.

    Dataset: knkarthick/dialogsum
    ~14,000 multi-turn dialogues across everyday and customer-facing topics.
    Each row: {'id', 'dialogue', 'summary', 'topic'}
    """
    from datasets import load_dataset

    splits = ["train", "validation", "test"]
    docs: list[RawDocument] = []

    for split in splits:
        ds = load_dataset(
            "knkarthick/dialogsum",
            split=split,
            cache_dir=str(cache_dir) if cache_dir else None,
        )
        for row in ds:
            text = (row.get("dialogue") or "").strip()
            if not text:
                continue
            docs.append(
                RawDocument(
                    text=text,
                    source_id=row.get("id", f"dialogsum_{len(docs):05d}"),
                    doc_type="transcript",
                    metadata={
                        "dataset": "dialogsum",
                        "topic": row.get("topic", ""),
                        "split": split,
                    },
                )
            )

    return docs
