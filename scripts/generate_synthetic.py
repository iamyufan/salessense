#!/usr/bin/env python
"""CLI: generate synthetic deal notes using Gemini 2.5 Flash (async, concurrent)."""
import argparse
import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm.asyncio import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

INDUSTRIES = ["SaaS", "FinTech", "Healthcare", "Manufacturing", "Logistics"]
ICPS = ["SMB", "Mid-Market", "Enterprise"]

# Conservative default — Gemini free tier is 10 RPM, paid is 1000+ RPM.
# Raise --concurrency if you're on a paid tier.
DEFAULT_CONCURRENCY = 15

PROMPT_TEMPLATE = """Generate a realistic sales deal note for a {icp} company in the {industry} industry.

The deal note should include:
- Company background (2-3 sentences)
- Deal stage and current status
- Key stakeholders and their roles
- Pain points and business challenges
- Proposed solution and value proposition
- Next steps and timeline
- Potential objections and how to handle them
- Competitive landscape (mention 1-2 competitors if relevant)

Write in a natural, first-person sales rep style. Length: 300-500 words."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def _generate_one(client: genai.AsyncClient, model_name: str, industry: str, icp: str) -> str:
    prompt = PROMPT_TEMPLATE.format(industry=industry, icp=icp)
    try:
        response = await client.aio.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        logging.error(f"API error ({industry}/{icp}): {type(e).__name__}: {e}")
        raise


async def _worker(
    client: genai.AsyncClient,
    model_name: str,
    queue: asyncio.Queue,
    results: list[dict],
    semaphore: asyncio.Semaphore,
    pbar: tqdm,
) -> None:
    while True:
        try:
            industry, icp = queue.get_nowait()
        except asyncio.QueueEmpty:
            return

        async with semaphore:
            try:
                text = await _generate_one(client, model_name, industry, icp)
                results.append({
                    "id": f"synthetic_{uuid.uuid4().hex[:12]}",
                    "text": text,
                    "industry": industry,
                    "icp": icp,
                })
            except Exception as e:
                logging.warning(f"Failed ({industry}/{icp}): {e}")
            finally:
                queue.task_done()
                pbar.update(1)


async def run(args) -> None:
    from salessense.config import settings

    client = genai.Client(api_key=settings.google_api_key)
    model_name = settings.llm_model

    # Build a flat list of (industry, icp) tasks
    combos = [(ind, icp) for ind in INDUSTRIES for icp in ICPS]
    per_combo = args.count // len(combos)
    remainder = args.count % len(combos)

    queue: asyncio.Queue = asyncio.Queue()
    for i, (industry, icp) in enumerate(combos):
        n = per_combo + (1 if i < remainder else 0)
        for _ in range(n):
            await queue.put((industry, icp))

    total_tasks = queue.qsize()
    logging.info(f"Generating {total_tasks} docs with concurrency={args.concurrency}")

    semaphore = asyncio.Semaphore(args.concurrency)
    results: list[dict] = []

    with tqdm(total=total_tasks, desc="Generating") as pbar:
        workers = [
            asyncio.create_task(
                _worker(client, model_name, queue, results, semaphore, pbar)
            )
            for _ in range(args.concurrency)
        ]
        await asyncio.gather(*workers)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.batch_file

    with open(output_path, "w") as f:
        for record in results:
            f.write(json.dumps(record) + "\n")

    logging.info(f"Generated {len(results)} docs -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic deal notes with Gemini")
    parser.add_argument("--count", type=int, default=6500, help="Total documents to generate")
    parser.add_argument("--output-dir", default="data/raw/synthetic", help="Output directory")
    parser.add_argument("--batch-file", default="synthetic_deals.jsonl", help="Output filename")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Number of concurrent Gemini requests (default: 15, raise for paid tier)",
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
