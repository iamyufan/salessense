"""Basic API smoke tests using TestClient."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from salessense.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    # Inject a mock Redis
    app.state.redis = AsyncMock()
    app.state.redis.get = AsyncMock(return_value=None)
    app.state.redis.setex = AsyncMock()
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_query_empty_question(client):
    resp = client.post("/api/v1/query", json={"question": ""})
    assert resp.status_code == 400


@patch("salessense.api.routes.query.rag_query")
def test_query_success(mock_rag, client):
    mock_rag.return_value = {
        "answer": "Test answer",
        "sources": [],
        "num_retrieved": 5,
    }
    resp = client.post("/api/v1/query", json={"question": "How do I handle pricing objections?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Test answer"
    assert data["cached"] is False
