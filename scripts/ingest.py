#!/usr/bin/env python
"""CLI: run ingestion pipeline for a given source."""
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Run SalesSense ingestion pipeline")
    parser.add_argument(
        "--source",
        required=True,
        choices=["callhome", "synthetic", "battlecards", "playbooks"],
        help="Data source to ingest",
    )
    parser.add_argument("--dry-run", action="store_true", help="Chunk only, skip embed+upsert")
    args = parser.parse_args()

    from salessense.ingestion.pipeline import run_ingestion

    count = run_ingestion(source=args.source, dry_run=args.dry_run)
    print(f"Done. {'Chunked' if args.dry_run else 'Upserted'} {count} chunks from '{args.source}'")


if __name__ == "__main__":
    sys.exit(main())
