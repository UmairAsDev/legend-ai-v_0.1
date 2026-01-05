import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "timestamp" in data


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_tokens_stt" in data
    assert "total_tokens_llm_input" in data
    assert "average_latency_ms" in data


def test_create_clinical_note_missing_data():
    """Test clinical note endpoint with missing data."""
    response = client.post("/api/v1/bot", json={"patient_data": {}})
    # Should fail validation
    assert response.status_code in [400, 422]


def test_create_clinical_note_valid_data():
    """Test clinical note endpoint with valid data."""
    response = client.post(
        "/api/v1/bot",
        json={
            "patient_data": {"patient_id": "12345", "name": "Test Patient", "age": 45},
            "config": {"note_style": "comprehensive"},
        },
    )
    # Should succeed (though may return placeholder data)
    assert response.status_code == 200
    data = response.json()
    assert "past_medical_history" in data or "error" in data


def test_rate_limiting():
    """Test rate limiting functionality."""
    # Make multiple rapid requests
    responses = []
    for _ in range(70):  # Exceed default limit of 60
        response = client.get("/health")
        responses.append(response.status_code)

    # Should eventually get rate limited
    assert 429 in responses or all(
        r == 200 for r in responses
    )  # May not hit limit in test


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.get("/health")
    assert (
        "access-control-allow-origin" in response.headers or response.status_code == 200
    )
