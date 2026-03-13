"""POST /query endpoint with Redis caching."""
import hashlib
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from salessense.config import settings
from salessense.generation.chain import rag_query

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    filters: dict[str, str] | None = None  # e.g. {"doc_type": "transcript"}


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    num_retrieved: int
    cached: bool = False


@router.post("/query", response_model=QueryResponse)
async def query(request: Request, body: QueryRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    cache_key = _cache_key(body.question, body.filters)
    redis = request.app.state.redis

    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        return QueryResponse(**data)

    try:
        result = rag_query(body.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    await redis.setex(cache_key, settings.redis_cache_ttl, json.dumps(result))
    return QueryResponse(**result)


def _cache_key(question: str, filters: dict | None) -> str:
    payload = question + json.dumps(filters or {}, sort_keys=True)
    return "salessense:query:" + hashlib.sha256(payload.encode()).hexdigest()
