from langchain_core.tools import tool
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.github_service import GitHubService
from agents.rag.retriever import CodeRetriever

def _get_github_service() -> GitHubService:
    token = os.getenv("GITHUB_TOKEN")
    return GitHubService(token=token)

@tool
async def read_file(owner: str, repo: str, path: str) -> str:
    """
    Fetches the raw text content of a specific file from a GitHub repository.
    Use this tool to read the actual code inside a file when you need to review it or answer a question about its implementation.
    """
    try:
        svc = _get_github_service()
        file_content = await svc.get_file_content(owner, repo, path)
        return f"--- Content of {path} ---\n{file_content.content}"
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"

@tool
async def search_codebase(query: str, repo_id: str) -> str:
    """
    Performs a semantic search over the entire codebase to find code snippets related to a natural language query.
    Use this tool when you don't know which file contains the logic you are looking for.
    It returns the most mathematically relevant code chunks based on the query.
    """
    try:
        retriever = CodeRetriever()
        chunks = await retriever.retrieve(query=query, repo_id=repo_id)
        if not chunks:
            return "No relevant code found for your query."
        
        formatted = []
        for i, chunk in enumerate(chunks):
            path = chunk.get("file_path", "unknown")
            content = chunk.get("content", "")
            formatted.append(f"--- Result [{i+1}] File: {path} ---\n{content}\n")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error searching codebase: {str(e)}"

@tool
async def get_file_list(owner: str, repo: str) -> str:
    """
    Fetches the flat file tree of the entire repository.
    Use this tool FIRST when analyzing a repository to understand the project structure 
    and identify which specific files exist before you try to read them.
    """
    try:
        svc = _get_github_service()
        files = await svc.get_file_tree(owner, repo)
        paths = [f.path for f in files]
        return f"Repository tree ({len(paths)} files):\n" + "\n".join(paths)
    except Exception as e:
        return f"Error fetching file list: {str(e)}"

# A registry list we can easily import in our agents
ALL_TOOLS = [read_file, search_codebase, get_file_list]
