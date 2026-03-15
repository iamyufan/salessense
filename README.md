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

---

## Setup

### Prerequisites

| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Weaviate vector store + Redis cache |
| Python 3.11+ | Backend |
| [uv](https://docs.astral.sh/uv/) | Python package manager |
| Node.js 18+ | Frontend |
| Google API key | Gemini LLM + embeddings |
| Cohere API key | Reranking |

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd salessense
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
GOOGLE_API_KEY=<your-google-api-key>
COHERE_API_KEY=<your-cohere-api-key>
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
```

### 2. Start infrastructure

```bash
docker compose up -d
```

This starts:
- **Weaviate** on `localhost:8080` (vector store, persisted via Docker volume)
- **Redis** on `localhost:6379` (query cache, TTL: 1 hour)

### 3. Install backend dependencies

```bash
uv sync
```

### 4. Ingest the corpus

Run each source in order. Ingestion downloads datasets from HuggingFace, chunks them, embeds via Gemini, and upserts into Weaviate.

```bash
uv run python scripts/ingest.py --source dialogsum       # ~14,500 dialogues
uv run python scripts/ingest.py --source conversations   # ~1,000 support transcripts
uv run python scripts/ingest.py --source synthetic       # ~6,500 deal notes
uv run python scripts/ingest.py --source battlecards     # markdown files in data/raw/battlecards/
uv run python scripts/ingest.py --source playbooks       # PDFs in data/raw/playbooks/
```

> **Note:** Ingestion calls the Gemini embedding API in batches. The free tier allows ~100 req/min — ingestion of the full corpus takes ~10–15 minutes. Rate limits are handled automatically with exponential backoff.

Once ingested, data is persisted in the Weaviate Docker volume and does not need to be re-ingested unless you delete the volume.

### 5. Start the backend API

```bash
uv run uvicorn src.salessense.api.app:app --reload --port 8000
```

API is now available at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is available at `http://localhost:3000`.

To point the frontend at a different backend URL, edit `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Using the Frontend

Open `http://localhost:3000` in your browser.

- Type a question in the input box at the bottom and press **Enter** (or **Shift+Enter** for a new line)
- The answer appears in the chat thread with citations from the corpus
- Click **Sources** under any answer to expand the retrieved documents — each source shows the doc type, industry, ICP, relevance score, and a text snippet
- Repeated queries are served instantly from cache (indicated by a **Cached** badge)

**Example questions to try:**
- *What are the key pain points for SaaS enterprise deals?*
- *What objections do SMB buyers raise and how should I handle them?*
- *How does the MEDDIC framework apply to mid-market deals?*
- *What differentiates us from Gong in a competitive deal?*

---

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
  "answer": "SMB buyers frequently raise the following objections:\n\n1. Cost: Budget is consistently highlighted as a factor.\n2. Implementation Complexity: Concerns about downtime and disrupting production.\n3. Resistance to Change: Teams resistant to change or burned by past failed rollouts.\n4. Existing Systems: May cite QuickBooks or spreadsheets as sufficient.",
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

**Optional filter by doc type:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "MEDDIC qualification steps", "filters": {"doc_type": "playbook"}}'
```

---

## Demo (Python)

```python
from salessense.generation.chain import rag_query

result = rag_query("What are the key pain points for SaaS enterprise deals?")
print(result["answer"])
```

**Output:**
```
Based on the provided deal notes, the key pain points for SaaS enterprise deals consistently revolve around:

1. Fragmented Data and Disparate Systems: Enterprises struggle with data silos and legacy
   systems (ERP, CRM, project management tools) that do not communicate effectively.

2. Lack of Real-time, Unified Visibility: Inability to gain a holistic, real-time view of
   operations hinders executive decision-making.

3. Operational Inefficiency and High Costs: Manual processes lead to significant time waste,
   delays, bottlenecks, and high operational costs.

4. High Error Rates and Compliance Risk: Manual processes are prone to errors, impacting
   reporting accuracy and increasing compliance risk.

5. Hindered Growth and Strategic Goals: These challenges impact project delivery timelines,
   growth targets, and digital transformation goals.
```

Retrieved 20 candidates via hybrid search → reranked to top 5 via Cohere (scores: 0.990–0.996).

---

## Evaluation

Ragas metrics evaluated against a 200-question golden set (pass threshold: ≥ 0.75 on all metrics).

### Experiment 1

Scores:

| Metric | Score | Status |
|---|---|---|
| faithfulness | 0.9277 | PASS |
| answer_relevancy | 0.7690 | PASS |
| context_precision | 0.6900 | FAIL |
| context_recall | 0.7233 | FAIL |

Configurations:

```# Model configuration (overridable)
LLM_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIM=3072
RERANK_MODEL=rerank-english-v3.0

# Retrieval parameters
HYBRID_TOP_K=20
RERANK_TOP_N=5
HYBRID_ALPHA=0.75  # 0=pure BM25, 1=pure vector

# Cache
REDIS_CACHE_TTL=3600  # seconds

# Ingestion
CHUNK_SIZE=512
CHUNK_OVERLAP=64
BATCH_SIZE=100

# Eval
EVAL_PASS_THRESHOLD=0.75
```


### Golden set construction

The golden set is generated from the live corpus and optionally reviewed before eval:

```bash
# Phase 1 — generate 200 Q&A pairs from sampled Weaviate chunks
uv run python scripts/generate_golden_set.py --count 200 --output data/eval/golden_set.json

# Phase 2 — interactively review a sample (approve / edit / flag items)
uv run python scripts/review_golden_set.py --golden-set data/eval/golden_set.json --sample 80
```

`generate_golden_set.py` uses cursor-based Weaviate pagination, calls Gemini 2.5 Flash to produce grounded Q&A pairs, and saves incrementally (crash-safe, resumable). `review_golden_set.py` deterministically samples 40% of unreviewed items, fetches the source chunk for context, and persists each decision immediately.

### Running eval

```bash
uv run python scripts/evaluate.py

# Save scores to a file
uv run python scripts/evaluate.py --output data/eval/scores.json
```

Flagged items are automatically excluded. Exits 0 on pass, 1 on fail.
