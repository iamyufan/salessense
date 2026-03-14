"""Phase 1: Sample chunks from Weaviate, generate Q&A pairs via Gemini, save to golden set."""
import argparse
import json
import random
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from salessense.config import settings
from salessense.eval.golden_set import GoldenItem, load_golden_set, save_golden_set
from salessense.retrieval.weaviate_client import get_client

_BATCH_DELAY = 2.0  # seconds between Gemini calls (free tier safety margin)

_PROMPT_TEMPLATE = """\
You are building an evaluation dataset for a sales AI assistant.

Given this sales context excerpt, generate a realistic question a sales rep might ask,
and the ground-truth answer that is directly derivable from this text only.
Be specific and grounded in the content.

Context:
{content}

Respond as JSON only, no markdown: {{"question": "...", "ground_truth": "..."}}"""


def _is_rate_limit(exc: BaseException) -> bool:
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


@retry(
    retry=retry_if_exception(_is_rate_limit),
    stop=stop_after_attempt(8),
    wait=wait_exponential(multiplier=2, min=10, max=60),
)
def _generate_qa(client: genai.Client, content: str) -> dict:
    prompt = _PROMPT_TEMPLATE.format(content=content)
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def _fetch_all_objects(weaviate_client) -> list[dict]:
    """Fetch all SalesDocument objects using cursor pagination, returning [{uuid, content}]."""
    collection = weaviate_client.collections.get(settings.weaviate_collection)
    all_objects: list[dict] = []
    limit = 1000
    after: str | None = None  # cursor: UUID of last seen object

    while True:
        response = collection.query.fetch_objects(
            limit=limit,
            after=after,
            return_properties=["content"],
        )
        if not response.objects:
            break

        for obj in response.objects:
            content = obj.properties.get("content", "").strip()
            if content:
                all_objects.append({"uuid": str(obj.uuid), "content": content})

        if len(response.objects) < limit:
            break

        after = str(response.objects[-1].uuid)
        print(f"  Fetched {len(all_objects)} objects so far...")

    return all_objects


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate golden QA set from Weaviate corpus")
    parser.add_argument("--count", type=int, default=200, help="Number of Q&A pairs to generate")
    parser.add_argument("--output", default="data/eval/golden_set.json", help="Output file path")
    args = parser.parse_args()

    output_path = Path(args.output)

    print(f"Connecting to Weaviate at {settings.weaviate_url}...")
    weaviate_client = get_client()
    try:
        print("Fetching all objects from Weaviate...")
        all_objects = _fetch_all_objects(weaviate_client)
        print(f"Total objects with content: {len(all_objects)}")
    finally:
        weaviate_client.close()

    if not all_objects:
        print("No objects found in Weaviate. Run ingestion first.")
        sys.exit(1)

    count = min(args.count, len(all_objects))
    if count < args.count:
        print(f"Warning: only {len(all_objects)} objects available, generating {count} items")

    random.seed(42)
    sampled = random.sample(all_objects, count)

    # Support resuming: skip already-generated chunk IDs
    existing_items: list[GoldenItem] = []
    if output_path.exists():
        existing_items = load_golden_set(output_path)
        existing_ids = {item.source_chunk_id for item in existing_items}
        sampled = [o for o in sampled if o["uuid"] not in existing_ids]
        print(f"Resuming: {len(existing_items)} existing, {len(sampled)} remaining")

    items = list(existing_items)
    gemini_client = genai.Client(api_key=settings.google_api_key)

    for i, obj in enumerate(sampled):
        print(f"[{i + 1}/{len(sampled)}] Generating Q&A for chunk {obj['uuid'][:8]}...")
        try:
            qa = _generate_qa(gemini_client, obj["content"])
            if not isinstance(qa, dict) or "question" not in qa or "ground_truth" not in qa:
                print("  Skipping: unexpected response format")
                continue

            item = GoldenItem(
                question=qa["question"],
                ground_truth=qa["ground_truth"],
                source_chunk_id=obj["uuid"],
                reviewed=False,
                flagged=False,
            )
            items.append(item)
            save_golden_set(items, output_path)
            print(f"  Q: {qa['question'][:80]}...")

        except Exception as e:
            print(f"  Error: {e} — skipping")

        if i < len(sampled) - 1:
            time.sleep(_BATCH_DELAY)

    print(f"\nDone. Saved {len(items)} items to {output_path}")


if __name__ == "__main__":
    main()
