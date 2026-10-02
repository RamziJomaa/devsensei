from langchain_core.tools import tool
import os
import sys

# Add backend to path for module importing since agents/ is a separate folder at root level
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.github_service import GitHubService

def _get_github_service() -> GitHubService:
    # In a full LangGraph setup, tokens are usually passed via state or context.
    # We fall back to the env var for simplicity in this checkpoint.
    token = os.getenv("GITHUB_TOKEN")
    return GitHubService(token=token)

@tool
async def fetch_repo_tree(owner: str, repo: str, branch: str = "main") -> str:
    """
    Fetches the flat file tree of a GitHub repository.
    Use this tool FIRST when analyzing a repository to understand the project structure 
    and identify which specific files you need to read.
    """
    try:
        svc = _get_github_service()
        files = await svc.get_file_tree(owner, repo, branch)
        paths = [f.path for f in files]
        return f"Repository tree for {owner}/{repo} ({len(paths)} files):\n" + "\n".join(paths)
    except Exception as e:
        return f"Error fetching repo tree: {str(e)}"

@tool
async def fetch_file_content(owner: str, repo: str, path: str) -> str:
    """
    Fetches the raw text content of a specific file from a GitHub repository.
    Use this to read code files, documentation, or configurations after you know their paths.
    """
    try:
        svc = _get_github_service()
        file_content = await svc.get_file_content(owner, repo, path)
        return f"--- Content of {path} ---\n{file_content.content}"
    except Exception as e:
        return f"Error fetching file content for {path}: {str(e)}"

@tool
async def fetch_pull_request_diff(owner: str, repo: str, pr_number: int) -> str:
    """
    Fetches the git diff of a specific pull request.
    Use this when you are asked to review a PR to see exactly what lines of code were added or removed.
    """
    try:
        svc = _get_github_service()
        pr_diff = await svc.get_pr_diff(owner, repo, pr_number)
        return f"--- Diff for PR #{pr_number} ---\n{pr_diff.diff}"
    except Exception as e:
        return f"Error fetching PR diff: {str(e)}"

# Expose a curated list of tools to bind to our agent later
github_tools = [fetch_repo_tree, fetch_file_content, fetch_pull_request_diff]
