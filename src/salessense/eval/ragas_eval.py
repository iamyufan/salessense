"""Ragas evaluation runner for the SalesSense RAG pipeline."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from salessense.config import settings
from salessense.generation.chain import format_context, rag_query
from salessense.retrieval.hybrid_search import hybrid_search
from salessense.retrieval.reranker import rerank
from salessense.retrieval.weaviate_client import get_client

logger = logging.getLogger(__name__)

METRICS = [faithfulness, answer_relevancy, context_precision, context_recall]


@dataclass
class EvalResult:
    scores: dict[str, float]
    passed: bool
    num_questions: int


def run_eval(golden_set_path: str | Path) -> EvalResult:
    """
    Run Ragas evaluation over a golden QA set.

    Golden set format (JSON array):
      [{"question": str, "ground_truth": str}, ...]
    """
    golden = json.loads(Path(golden_set_path).read_text())
    logger.info(f"Running eval on {len(golden)} questions")

    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    client = get_client()
    try:
        for item in golden:
            question = item["question"]
            candidates = hybrid_search(client, question)
            reranked = rerank(question, candidates)
            context_texts = [r.content for r in reranked]
            result = rag_query(question)

            rows["question"].append(question)
            rows["answer"].append(result["answer"])
            rows["contexts"].append(context_texts)
            rows["ground_truth"].append(item["ground_truth"])
    finally:
        client.close()

    dataset = Dataset.from_dict(rows)

    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model=f"models/{settings.embedding_model}",
        google_api_key=settings.google_api_key,
    )

    ragas_result = evaluate(dataset=dataset, metrics=METRICS, llm=llm, embeddings=embeddings)
    scores = {metric.name: float(ragas_result[metric.name]) for metric in METRICS}

    passed = all(v >= settings.eval_pass_threshold for v in scores.values())

    logger.info(f"Eval scores: {scores}")
    logger.info(f"Pass: {passed}")

    return EvalResult(scores=scores, passed=passed, num_questions=len(golden))
