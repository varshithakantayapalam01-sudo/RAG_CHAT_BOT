from __future__ import annotations

"""
End-to-End API Integration Tests

Validates the FastAPI REST endpoint structures, including RAG pipeline
passthrough and guardrail intercept routing.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test the GET /api/health endpoint returns 200 and status metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vectorstore" in data
    assert data["vectorstore"]["document_count"] > 0
    assert "last_ingestion" in data
    assert "last_collected" in data


def test_chat_factual_success() -> None:
    """Test POST /api/chat for a valid factual query."""
    payload = {
        "query": "What is the expense ratio of HDFC Mid-Cap Fund?",
        "session_id": "test_session_1",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["type"] == "factual"
    assert "0.75%" in data["answer"]
    assert "groww.in" in data["citation"]
    assert "Last updated from sources" in data["footer"]


def test_chat_advisory_refused() -> None:
    """Test POST /api/chat intercept and refuse advisory intent."""
    payload = {
        "query": "Should I invest in HDFC Mid-Cap Fund?",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refused"
    assert data["type"] == "advisory"
    assert "cannot provide investment advice" in data["answer"]
    assert data["educational_link"] == "https://www.amfiindia.com/investor-corner/knowledge-center"


def test_chat_pii_refused() -> None:
    """Test POST /api/chat intercept and refuse PII inputs."""
    payload = {
        "query": "My PAN is ABCDE1234F",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refused"
    assert data["type"] == "pii"
    assert "personally identifiable information" in data["answer"]


def test_chat_off_topic_refused() -> None:
    """Test POST /api/chat intercept and refuse off-topic prompts."""
    payload = {
        "query": "What is the capital of Japan?",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refused"
    assert data["type"] == "off_topic"
    assert "factual queries regarding the 5 supported HDFC" in data["answer"]


def test_chat_empty_query_validation() -> None:
    """Test POST /api/chat with an empty query triggers Pydantic validation error."""
    payload = {
        "query": "",
    }
    response = client.post("/api/chat", json=payload)
    # Pydantic string validation fails on min_length or FastAPI APIRouter on value
    assert response.status_code in (400, 422)
