import httpx
from typing import List, Optional
from pydantic import BaseModel
import base64

class GitHubFile(BaseModel):
    path: str
    type: str  # 'blob' for files, 'tree' for folders
    size: Optional[int] = None

class GitHubFileContent(BaseModel):
    path: str
    content: str
    encoding: str

class GitHubPRDiff(BaseModel):
    pr_number: int
    diff: str

class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API Error {status_code}: {message}")

class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _handle_error(self, response: httpx.Response):
        if response.status_code == 200:
            return
        
        status = response.status_code
        if status == 401:
            raise GitHubAPIError(status, "Invalid GitHub token. Authentication failed.")
        elif status == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                raise GitHubAPIError(status, "GitHub API rate limit exceeded.")
            raise GitHubAPIError(status, "Forbidden: Ensure the token has access to this repository.")
        elif status == 404:
            raise GitHubAPIError(status, "Repository, file, or PR not found (or it is private and token lacks access).")
        else:
            raise GitHubAPIError(status, f"Unexpected GitHub API error: {response.text}")

    async def get_file_tree(self, owner: str, repo: str, branch: str = "main") -> List[GitHubFile]:
        """Fetches the flat file structure of a repository recursively."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            self._handle_error(response)
            
            data = response.json()
            return [
                GitHubFile(path=item["path"], type=item["type"], size=item.get("size")) 
                for item in data.get("tree", []) if item["type"] == "blob"
            ]

    async def get_file_content(self, owner: str, repo: str, path: str) -> GitHubFileContent:
        """Fetches the raw content of a specific file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            self._handle_error(response)
            
            data = response.json()
            content_b64 = data.get("content", "")
            
            # GitHub returns base64 encoded content
            if content_b64:
                # Remove newlines before decoding
                clean_b64 = content_b64.replace("\n", "")
                content = base64.b64decode(clean_b64).decode("utf-8", errors="replace")
            else:
                content = ""
                
            return GitHubFileContent(
                path=data["path"],
                content=content,
                encoding="utf-8"
            )

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> GitHubPRDiff:
        """Fetches the raw diff string for a Pull Request."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        headers = self.headers.copy()
        # Diff endpoints require a specific Accept header
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            self._handle_error(response)
            
            return GitHubPRDiff(
                pr_number=pr_number,
                diff=response.text
            )
