import pytest
from unittest.mock import patch, AsyncMock
from backend.services.github_service import GitHubService, GitHubAPIError

@pytest.fixture
def github_service():
    return GitHubService(token="fake_token")

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_file_tree_success(mock_get, github_service):
    # Mocking the HTTP response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tree": [
            {"path": "backend/main.py", "type": "blob", "size": 1500},
            {"path": "backend", "type": "tree"} # Should be filtered out
        ]
    }
    mock_get.return_value = mock_response

    result = await github_service.get_file_tree("test_owner", "test_repo")
    
    assert len(result) == 1
    assert result[0].path == "backend/main.py"
    assert result[0].type == "blob"

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_file_tree_not_found(mock_get, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    with pytest.raises(GitHubAPIError) as exc_info:
        await github_service.get_file_tree("test_owner", "test_repo")
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message.lower()

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_pr_diff_success(mock_get, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "diff --git a/main.py b/main.py\n+new line"
    mock_get.return_value = mock_response

    result = await github_service.get_pr_diff("test_owner", "test_repo", 10)
    
    assert result.pr_number == 10
    assert "diff --git" in result.diff

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_rate_limit_exceeded(mock_get, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.headers = {"X-RateLimit-Remaining": "0"}
    mock_get.return_value = mock_response

    with pytest.raises(GitHubAPIError) as exc_info:
         await github_service.get_file_tree("test_owner", "test_repo")
         
    assert exc_info.value.status_code == 403
    assert "rate limit" in exc_info.value.message.lower()
