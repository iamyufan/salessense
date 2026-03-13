"""LangChain RAG chain: hybrid retrieve -> Cohere rerank -> Gemini generate."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from salessense.config import settings
from salessense.retrieval.hybrid_search import SearchResult, hybrid_search
from salessense.retrieval.reranker import rerank
from salessense.retrieval.weaviate_client import get_client

_SYSTEM_PROMPT = """You are SalesSense, an AI assistant for sales teams.
Answer questions using only the provided context from sales call transcripts, deal notes, and playbooks.
Be specific, cite patterns you observe, and give actionable advice.
If the context does not contain enough information, say so clearly."""

_HUMAN_PROMPT = """Context:
{context}

Question: {question}

Answer:"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", _HUMAN_PROMPT),
])

_llm = ChatGoogleGenerativeAI(
    model=settings.llm_model,
    google_api_key=settings.google_api_key,
    temperature=0.2,
)

_chain = _prompt | _llm | StrOutputParser()


def format_context(results: list[SearchResult]) -> str:
    parts = []
    for i, r in enumerate(results, 1):
        meta = f"[{r.doc_type} | {r.industry} | {r.icp}]" if r.industry else f"[{r.doc_type}]"
        parts.append(f"--- Source {i} {meta} ---\n{r.content}")
    return "\n\n".join(parts)


def rag_query(question: str) -> dict:
    """
    Full RAG pipeline: retrieve -> rerank -> generate.

    Returns:
        {
            "answer": str,
            "sources": list[dict],
            "num_retrieved": int,
        }
    """
    client = get_client()
    try:
        candidates = hybrid_search(client, question)
        reranked = rerank(question, candidates)
    finally:
        client.close()

    context = format_context(reranked)
    answer = _chain.invoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": [
            {
                "source_id": r.source_id,
                "doc_type": r.doc_type,
                "industry": r.industry,
                "icp": r.icp,
                "score": r.score,
                "snippet": r.content[:200],
            }
            for r in reranked
        ],
        "num_retrieved": len(candidates),
    }
