"""Load e-commerce customer support conversations from HuggingFace."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawDocument:
    text: str
    source_id: str
    doc_type: str
    metadata: dict


def load_conversations(cache_dir: str | Path | None = None) -> list[RawDocument]:
    """
    Download and return customer support conversations from HuggingFace.

    Dataset: NebulaByte/E-Commerce_Customer_Support_Conversations
    ~1,000 Agent/Customer transcripts across e-commerce support topics.
    Each row: {'conversation', 'issue_area', 'issue_category', 'customer_sentiment', ...}
    """
    from datasets import load_dataset

    ds = load_dataset(
        "NebulaByte/E-Commerce_Customer_Support_Conversations",
        split="train",
        cache_dir=str(cache_dir) if cache_dir else None,
    )
    docs: list[RawDocument] = []

    for i, row in enumerate(ds):
        text = (row.get("conversation") or "").strip()
        if not text:
            continue
        docs.append(
            RawDocument(
                text=text,
                source_id=f"conversations_{i:05d}",
                doc_type="transcript",
                metadata={
                    "dataset": "ecommerce_support",
                    "issue_area": row.get("issue_area", ""),
                    "issue_category": row.get("issue_category", ""),
                    "customer_sentiment": row.get("customer_sentiment", ""),
                },
            )
        )

    return docs
