"""Utilities for managing the golden QA evaluation set."""
import json
from pathlib import Path


GOLDEN_SET_PATH = Path("data/eval/golden_set.json")


def load_golden_set(path: str | Path = GOLDEN_SET_PATH) -> list[dict]:
    """Load golden QA set. Expected: [{"question": str, "ground_truth": str}]"""
    return json.loads(Path(path).read_text())


def save_golden_set(items: list[dict], path: str | Path = GOLDEN_SET_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(items, indent=2))
