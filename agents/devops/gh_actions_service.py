import httpx
import os
from typing import Dict, Any, List

class GitHubActionsService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get_recent_workflow_runs(self, owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches the most recent workflow runs to detect flaky or failing pipelines."""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs?per_page={limit}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return [{"error": f"Failed to fetch runs. Status: {response.status_code}"}]
                
            data = response.json()
            runs = data.get("workflow_runs", [])
            
            results = []
            for run in runs:
                results.append({
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "created_at": run["created_at"]
                })
            return results
