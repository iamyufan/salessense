#!/usr/bin/env python
"""CLI: run Ragas evaluation and print leaderboard."""
import argparse
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Run SalesSense Ragas evaluation")
    parser.add_argument(
        "--golden-set",
        default="data/eval/golden_set.json",
        help="Path to golden QA set JSON",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save scores JSON",
    )
    args = parser.parse_args()

    from salessense.config import settings
    from salessense.eval.ragas_eval import run_eval

    result = run_eval(args.golden_set)

    print("\n=== SalesSense Eval Results ===")
    print(f"Questions evaluated: {result.num_questions}")
    print(f"Pass threshold:      {settings.eval_pass_threshold}")
    print()
    for metric, score in sorted(result.scores.items()):
        status = "PASS" if score >= settings.eval_pass_threshold else "FAIL"
        print(f"  {metric:<25} {score:.4f}  [{status}]")
    print()
    print(f"Overall: {'PASS' if result.passed else 'FAIL'}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump({"scores": result.scores, "passed": result.passed}, f, indent=2)
        print(f"Scores saved to {args.output}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
