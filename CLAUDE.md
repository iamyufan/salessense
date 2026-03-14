# SalesSense — Claude Context

## Project Overview
Production-grade RAG system over sales call transcripts, deal notes, and playbooks.
~8,000 document corpus. Query path returns grounded answers via hybrid retrieval + reranking.

## Tech Stack
| Layer | Technology |
|---|---|
| LLM | `gemini-2.5-flash` (Google Gemini) |
| Embeddings | `gemini-embedding-001` (3072-dim) |
| Orchestration | LangChain + `google-genai` Python SDK |
| Vector Store | Weaviate (self-hosted via Docker) |
| Sparse Retrieval | Weaviate native BM25 + vector + Relative Score Fusion (RSF) |
| Re-ranking | Cohere Rerank API (`rerank-english-v3.0`) |
| Evaluation | Ragas + DSPy |
| Backend | FastAPI + Redis |
| Frontend | Next.js 14 + shadcn/ui |
| CI/CD | GitHub Actions + Fly.io |
| Package Manager | uv |

## Data Pipeline

### Corpus (~22,000 docs)
- **DialogSum** (~14,500): Multi-turn dialogues from Hugging Face (`knkarthick/dialogsum`, all splits)
- **E-Commerce Support Conversations** (~1,000): Agent/Customer transcripts (`NebulaByte/E-Commerce_Customer_Support_Conversations`)
- **Synthetic Deal Notes** (~6,500): Gemini 2.5 Flash-generated across 5 industries x 3 ICP archetypes
  - Industries: SaaS, FinTech, Healthcare, Manufacturing, Logistics
  - ICPs: SMB, Mid-Market, Enterprise
- **Battlecards** (5-10 files): Manually written markdown in `data/raw/battlecards/`
- **Playbooks** (2-3 PDFs): MEDDIC, Challenger Sale -- in `data/raw/playbooks/`

### Ingestion Path
```
Raw Docs -> Chunker -> Embedder (gemini-embedding-001) -> Weaviate (vector + BM25 index)
```

### Query Path
```
User Query -> Weaviate Hybrid Search (BM25 + vector + RSF, top-20) -> Cohere Rerank (top-5) -> Gemini 2.5 Flash -> Answer
```

### Eval Path
```
Golden QA Set (200q) -> Ragas Scorer -> Leaderboard -> GitHub Actions Gate
```

## Directory Structure
```
salessense/
├── src/salessense/
│   ├── config.py               # Pydantic Settings -- all env vars
│   ├── ingestion/
│   │   ├── chunker.py          # RecursiveCharacterTextSplitter logic
│   │   ├── embedder.py         # Gemini embedding-001 wrapper
│   │   ├── pipeline.py         # Orchestrates load -> chunk -> embed -> upsert
│   │   └── loaders/
│   │       ├── dialogsum.py    # HuggingFace DialogSum loader
│   │       ├── conversations.py # HuggingFace e-commerce support conversations loader
│   │       ├── synthetic.py    # Gemini-generated doc loader
│   │       └── pdf.py          # PDF -> text (playbooks)
│   ├── retrieval/
│   │   ├── weaviate_client.py  # Weaviate v4 client + schema init
│   │   ├── hybrid_search.py    # BM25 + vector + RSF hybrid query
│   │   └── reranker.py         # Cohere Rerank wrapper
│   ├── generation/
│   │   └── chain.py            # LangChain RAG chain (retrieve -> rerank -> generate)
│   ├── api/
│   │   ├── app.py              # FastAPI app factory
│   │   └── routes/
│   │       ├── query.py        # POST /query
│   │       └── health.py       # GET /health
│   └── eval/
│       ├── ragas_eval.py       # Ragas metric runner
│       └── golden_set.py       # Golden QA set loader
├── data/
│   ├── raw/{synthetic,battlecards,playbooks}/  # HF datasets streamed at ingest time
│   └── processed/
├── scripts/
│   ├── ingest.py               # CLI: run full ingestion pipeline
│   ├── generate_synthetic.py   # CLI: generate synthetic deal notes via Gemini
│   └── evaluate.py             # CLI: run Ragas eval + print leaderboard
├── tests/
├── frontend/                   # Next.js 14 + shadcn/ui
├── docker-compose.yml          # Weaviate + Redis
└── .github/workflows/eval.yml  # CI eval gate
```

## Key Commands
```bash
# Start infrastructure
docker compose up -d

# Install dependencies
uv sync

# Run ingestion
uv run python scripts/ingest.py --source dialogsum
uv run python scripts/ingest.py --source conversations
uv run python scripts/ingest.py --source synthetic
uv run python scripts/ingest.py --source battlecards
uv run python scripts/ingest.py --source playbooks

# Generate synthetic docs
uv run python scripts/generate_synthetic.py --count 6500

# Start API
uv run uvicorn src.salessense.api.app:app --reload --port 8000

# Run eval
uv run python scripts/evaluate.py

# Run tests
uv run pytest tests/ -v
```

## Environment Variables
See `.env.example`. Required:
- `GOOGLE_API_KEY` -- for Gemini LLM + embeddings
- `COHERE_API_KEY` -- for Cohere Rerank
- `WEAVIATE_URL` -- default `http://localhost:8080`
- `REDIS_URL` -- default `redis://localhost:6379`

## Weaviate Schema
Collection name: `SalesDocument`
Properties:
- `content` (text) -- chunk text, BM25-indexed
- `doc_type` (text) -- transcript | deal_note | battlecard | playbook
- `industry` (text) -- SaaS | FinTech | Healthcare | Manufacturing | Logistics
- `icp` (text) -- SMB | Mid-Market | Enterprise
- `source_id` (text) -- original document identifier
- `chunk_index` (int)
- Vector: 3072-dim from `gemini-embedding-001`

## Chunking Strategy
- Chunk size: 512 tokens, overlap: 64 tokens
- Splitter: `RecursiveCharacterTextSplitter`
- For transcripts: split on speaker turns first, then token limit

## Eval Metrics (Ragas)
- `answer_relevancy`, `faithfulness`, `context_precision`, `context_recall`
- Pass threshold: all metrics >= 0.75 (enforced in GitHub Actions)

## Notes
- "Gemini 3 Flash" in spec refers to `gemini-2.5-flash` (configurable via `LLM_MODEL` env var)
- Weaviate runs on port 8080, gRPC on 50051
- Redis used for query-level caching (TTL: 1 hour)
- Cohere `rerank-english-v3.0` -- top-20 candidates in, top-5 out
