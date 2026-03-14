"""Utilities for managing the golden QA evaluation set."""
import json
from dataclasses import asdict, dataclass
from pathlib import Path


GOLDEN_SET_PATH = Path("data/eval/golden_set.json")


@dataclass
class GoldenItem:
    question: str
    ground_truth: str
    source_chunk_id: str
    reviewed: bool = False
    flagged: bool = False


def load_golden_set(path: str | Path = GOLDEN_SET_PATH) -> list[GoldenItem]:
    """Load golden QA set from JSON, returning typed GoldenItem list."""
    raw = json.loads(Path(path).read_text())
    return [
        GoldenItem(
            question=item["question"],
            ground_truth=item["ground_truth"],
            source_chunk_id=item.get("source_chunk_id", ""),
            reviewed=item.get("reviewed", False),
            flagged=item.get("flagged", False),
        )
        for item in raw
    ]


def save_golden_set(items: list[GoldenItem], path: str | Path = GOLDEN_SET_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps([asdict(item) for item in items], indent=2))
