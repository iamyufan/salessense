# SalesSense

A production-grade RAG system for sales intelligence. Query across call transcripts, deal notes, battlecards, and playbooks to get grounded answers backed by your sales corpus.

## Corpus (~22,000 documents)

| Source | Docs | Chunks | Type |
|---|---|---|---|
| [DialogSum](https://huggingface.co/datasets/knkarthick/dialogsum) | ~14,500 | | Multi-turn dialogues |
| [E-Commerce Support Conversations](https://huggingface.co/datasets/NebulaByte/E-Commerce_Customer_Support_Conversations) | ~1,000 | 16,016 (transcripts total) | Agent/Customer transcripts |
| Synthetic Deal Notes (Gemini 2.5 Flash) | ~6,500 | 20,774 | Deal notes across 5 industries × 3 ICPs |
| Battlecards | 7 files | 19 | Competitor + ICP markdown docs |
| Playbooks | 2 PDFs | 21 | MEDDIC, Challenger Sale |
| **Total** | | **36,830 chunks** | |

## Architecture

```
User Query
  → Weaviate Hybrid Search (BM25 + vector + RSF, top-20)
  → Cohere Rerank (top-5)
  → Gemini 2.5 Flash
  → Grounded Answer
```

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 2.5 Flash |
| Embeddings | gemini-embedding-001 (3072-dim) |
| Vector Store | Weaviate (self-hosted) |
| Retrieval | Hybrid BM25 + vector + Relative Score Fusion |
| Re-ranking | Cohere Rerank (`rerank-english-v3.0`) |
| Evaluation | Ragas |
| Backend | FastAPI + Redis |
| Frontend | Next.js 14 + shadcn/ui |

## Quickstart

```bash
# Start infrastructure
docker compose up -d

# Install dependencies
uv sync

# Ingest all sources
uv run python scripts/ingest.py --source dialogsum
uv run python scripts/ingest.py --source conversations
uv run python scripts/ingest.py --source synthetic
uv run python scripts/ingest.py --source battlecards
uv run python scripts/ingest.py --source playbooks

# Start API
uv run uvicorn src.salessense.api.app:app --reload --port 8000

# Run evaluation
uv run python scripts/evaluate.py
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
GOOGLE_API_KEY=       # Gemini LLM + embeddings
COHERE_API_KEY=       # Cohere Rerank
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
```

## Demo

```python
from salessense.generation.chain import rag_query

result = rag_query("What are the key pain points for SaaS enterprise deals?")
print(result["answer"])
```

**Output:**
```
Based on the provided deal notes, the key pain points for SaaS enterprise deals consistently revolve around:

1. Fragmented Data and Disparate Systems: Enterprises struggle with data silos and legacy
   systems (ERP, CRM, project management tools) that do not communicate effectively,
   necessitating manual data entry and reconciliation.

2. Lack of Real-time, Unified Visibility: Inability to gain a holistic, real-time view of
   operations hinders executive decision-making and strategic initiatives.

3. Operational Inefficiency and High Costs: Manual processes lead to significant time waste,
   delays, bottlenecks, and high operational costs.

4. High Error Rates and Compliance Risk: Manual processes are prone to errors, impacting
   reporting accuracy and increasing compliance risk.

5. Poor Client Experience: Slow client onboarding directly impacts satisfaction and loyalty.

6. Hindered Growth and Strategic Goals: These challenges impact project delivery timelines,
   growth targets, accurate forecasting, and digital transformation goals.
```

Retrieved 20 candidates via hybrid search → reranked to top 5 via Cohere (scores: 0.990–0.996).

## API Usage

**Health check:**
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

**Query:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "What objections do SMB buyers raise?"}'
```

**Response:**
```json
{
  "answer": "SMB buyers frequently raise the following objections:\n\n1. Cost: They often state that the cost is too high for an SMB. Budget is consistently highlighted as a factor.\n2. Implementation Complexity/Disruption: Concerns about implementation being too complex, causing downtime, or disrupting production.\n3. Resistance to Change/User Adoption: Buyers express that their team is resistant to change or that previous systems were too complicated.\n4. Existing Systems/Status Quo: They may cite existing tools (e.g., QuickBooks, spreadsheets) as sufficient.",
  "sources": [
    {
      "source_id": "synthetic_813df5576e8a",
      "doc_type": "deal_note",
      "industry": "Manufacturing",
      "icp": "SMB",
      "score": 0.9099,
      "snippet": "**Potential Objections & How to Handle Them:** Cost is too high for an SMB..."
    }
  ],
  "num_retrieved": 20,
  "cached": false
}
```

Repeated queries are served from Redis cache (`"cached": true`) with no LLM or embedding calls.

## Evaluation

Ragas metrics evaluated against a 200-question golden set:
- `answer_relevancy` ≥ 0.75
- `faithfulness` ≥ 0.75
- `context_precision` ≥ 0.75
- `context_recall` ≥ 0.75

CI gate enforced via GitHub Actions on every push.
