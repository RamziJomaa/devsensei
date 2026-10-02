import pytest

def test_trigger_analysis_success(client):
    payload = {
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "github_token": "fake-token"
    }
    
    response = client.post("/api/v1/analyse", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert "analysis_id" in data
    assert data["status"] == "pending"
    assert "Poll status endpoint" in data["message"]

def test_trigger_analysis_invalid_url(client):
    payload = {
        "repo_url": "not-a-valid-url"
    }
    
    response = client.post("/api/v1/analyse", json=payload)
    # Pydantic HttpUrl validation should fail
    assert response.status_code == 422
