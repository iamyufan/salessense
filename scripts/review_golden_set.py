"""Phase 2: Interactive CLI to review a sample of generated golden Q&A pairs."""
import argparse
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from salessense.config import settings
from salessense.eval.golden_set import GoldenItem, load_golden_set, save_golden_set
from salessense.retrieval.weaviate_client import get_client

_SEPARATOR = "=" * 70


def _fetch_chunk_content(weaviate_client, uuid: str) -> str:
    collection = weaviate_client.collections.get(settings.weaviate_collection)
    obj = collection.query.fetch_object_by_id(uuid, return_properties=["content"])
    if obj is None:
        return "[chunk not found in Weaviate]"
    return obj.properties.get("content", "[no content]")


def _open_editor(initial: str) -> str:
    """Open $EDITOR (or nano) for inline editing; return edited text."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write(initial)
        fname = f.name
    subprocess.call([editor, fname])
    result = Path(fname).read_text().strip()
    Path(fname).unlink(missing_ok=True)
    return result


def _prompt_inline(label: str, initial: str) -> str:
    """Fallback: prompt for new value inline if editor not preferred."""
    print(f"Current {label}: {initial}")
    new_val = input(f"New {label} (blank to keep): ").strip()
    return new_val if new_val else initial


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactively review golden QA set")
    parser.add_argument("--golden-set", default="data/eval/golden_set.json")
    parser.add_argument("--sample", type=int, default=80, help="Number of items to review")
    args = parser.parse_args()

    path = Path(args.golden_set)
    if not path.exists():
        print(f"Golden set not found: {path}")
        print("Run generate_golden_set.py first.")
        sys.exit(1)

    items = load_golden_set(path)

    unreviewed_indices = [
        i for i, item in enumerate(items) if not item.reviewed and not item.flagged
    ]

    random.seed(42)
    if len(unreviewed_indices) > args.sample:
        review_indices = random.sample(unreviewed_indices, args.sample)
        review_indices.sort()  # process in order for predictability
    else:
        review_indices = unreviewed_indices

    print(f"Golden set: {len(items)} total, {len(unreviewed_indices)} unreviewed")
    print(f"Reviewing {len(review_indices)} items")
    print("Options per item: [a]pprove  [e]dit question  [g]edit ground truth  [f]lag  [s]kip\n")

    weaviate_client = get_client()
    counts = {"approved": 0, "edited": 0, "flagged": 0, "skipped": 0}

    try:
        for step, idx in enumerate(review_indices):
            item = items[idx]

            print(f"\n{_SEPARATOR}")
            print(f"Item {step + 1}/{len(review_indices)}  (index {idx})")
            print(f"Chunk ID: {item.source_chunk_id}")

            content = _fetch_chunk_content(weaviate_client, item.source_chunk_id)
            print(f"\n--- SOURCE CHUNK ---\n{content}\n")
            print(f"Q: {item.question}")
            print(f"A: {item.ground_truth}")
            print()

            while True:
                choice = input("[a]pprove / [e]dit question / [g]edit ground truth / [f]lag / [s]kip: ").strip().lower()
                if choice in ("a", "e", "g", "f", "s"):
                    break
                print("  Invalid choice, try again.")

            if choice == "a":
                items[idx].reviewed = True
                counts["approved"] += 1

            elif choice == "e":
                new_q = _open_editor(item.question)
                if new_q != item.question:
                    items[idx].question = new_q
                items[idx].reviewed = True
                counts["edited"] += 1

            elif choice == "g":
                new_gt = _open_editor(item.ground_truth)
                if new_gt != item.ground_truth:
                    items[idx].ground_truth = new_gt
                items[idx].reviewed = True
                counts["edited"] += 1

            elif choice == "f":
                items[idx].flagged = True
                counts["flagged"] += 1
                print("  Flagged for removal.")

            else:  # s
                counts["skipped"] += 1
                print("  Skipped.")

            # Crash-safe: persist after every decision
            save_golden_set(items, path)

    except KeyboardInterrupt:
        print("\n\nInterrupted — progress saved.")
    finally:
        weaviate_client.close()

    active = sum(1 for item in items if not item.flagged)
    reviewed = sum(1 for item in items if item.reviewed)

    print(f"\n{_SEPARATOR}")
    print("Review session complete!")
    print(f"  Approved : {counts['approved']}")
    print(f"  Edited   : {counts['edited']}")
    print(f"  Flagged  : {counts['flagged']}")
    print(f"  Skipped  : {counts['skipped']}")
    print(f"\nTotal reviewed in set : {reviewed}/{len(items)}")
    print(f"Active (not flagged)  : {active}/{len(items)}")


if __name__ == "__main__":
    main()
