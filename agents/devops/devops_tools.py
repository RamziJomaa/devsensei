from langchain_core.tools import tool
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.devops.cicd_analyser import CICDAnalyser
from agents.devops.dockerfile_analyser import DockerfileAnalyser
from agents.devops.gh_actions_service import GitHubActionsService

@tool
def analyze_github_actions_yaml(file_content: str, file_path: str) -> str:
    """Analyzes a GitHub Actions YAML file for security risks and anti-patterns."""
    analyser = CICDAnalyser()
    findings = analyser.analyze_github_actions(file_content, file_path)
    return json.dumps(findings)

@tool
def analyze_dockerfile(file_content: str, file_path: str) -> str:
    """Analyzes a Dockerfile for security risks and best practices."""
    analyser = DockerfileAnalyser()
    findings = analyser.analyze(file_content, file_path)
    return json.dumps(findings)

@tool
async def fetch_workflow_runs(owner: str, repo: str) -> str:
    """Fetches the last 5 GitHub Actions workflow runs to check for pipeline failures."""
    svc = GitHubActionsService()
    runs = await svc.get_recent_workflow_runs(owner, repo)
    return json.dumps(runs)
