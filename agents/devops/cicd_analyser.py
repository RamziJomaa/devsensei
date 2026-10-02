import re
from typing import List, Dict, Any

class CICDAnalyser:
    def analyze_github_actions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        lines = content.split('\n')
        
        has_cache = False
        has_sonar = False
        has_test = False
        has_deploy = False
        
        # Regex for hardcoded secrets (ignoring ${{ secrets.SOMETHING }})
        secret_pattern = re.compile(r'(?i)(api_key|password|token|secret)\s*[:=]\s*(?!.*\$\{\{\s*secrets\.)["\']?[a-zA-Z0-9_\-]+["\']?')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 1. Hardcoded Secrets
            if secret_pattern.search(line):
                findings.append({
                    "title": "Hardcoded Secret in CI/CD",
                    "severity": "critical",
                    "file": file_path,
                    "line": i + 1,
                    "description": "Found a potential hardcoded secret. Secrets must reference ${{ secrets.X }}",
                    "suggestion": "Move this value to GitHub Repository Secrets."
                })
                
            # 2. Unpinned Versions
            if "uses:" in line_lower and ("@main" in line_lower or "@master" in line_lower):
                findings.append({
                    "title": "Unpinned GitHub Action Version",
                    "severity": "medium",
                    "file": file_path,
                    "line": i + 1,
                    "description": "Using @main or @master for actions can introduce breaking changes unexpectedly.",
                    "suggestion": "Pin the action to a specific release tag or commit SHA (e.g., uses: actions/checkout@v4)."
                })
                
            # Tracking features
            if "actions/cache" in line_lower or "cache:" in line_lower:
                has_cache = True
            if "sonar" in line_lower:
                has_sonar = True
            if "test" in line_lower or "pytest" in line_lower or "npm test" in line_lower:
                has_test = True
            if "deploy" in line_lower or "push" in line_lower:
                has_deploy = True

        # 3. Dependency Caching
        if not has_cache:
            findings.append({
                "title": "Missing Dependency Caching",
                "severity": "low",
                "file": file_path,
                "line": 0,
                "description": "No caching mechanism detected. This slows down pipeline execution and increases costs.",
                "suggestion": "Implement actions/cache for your package manager (e.g., pip, npm)."
            })
            
        # 4. Quality Gate
        if not has_sonar:
            findings.append({
                "title": "Missing Quality Gate",
                "severity": "medium",
                "file": file_path,
                "line": 0,
                "description": "No SonarQube or code quality gate found in the workflow.",
                "suggestion": "Integrate SonarCloud or another static analysis tool to enforce quality before merging."
            })
            
        # 5. Testing before deployment
        if has_deploy and not has_test:
            findings.append({
                "title": "Deployment Without Testing",
                "severity": "high",
                "file": file_path,
                "line": 0,
                "description": "A deployment step was found, but no test steps were detected before it.",
                "suggestion": "Ensure unit and integration tests are run and required before any deployment steps."
            })
            
        return findings
