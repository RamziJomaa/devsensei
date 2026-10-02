import re
from typing import List, Dict, Any

class DockerfileAnalyser:
    def analyze(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        lines = content.split('\n')
        
        has_user = False
        from_count = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip().upper()
            
            # 1. Root User Check
            if line_stripped.startswith("USER"):
                has_user = True
                
            # 2. Base Image Pinning Check
            if line_stripped.startswith("FROM"):
                from_count += 1
                if "LATEST" in line_stripped:
                    findings.append({
                        "title": "Unpinned Docker Base Image",
                        "severity": "medium",
                        "file": file_path,
                        "line": i + 1,
                        "description": "Using the 'latest' tag can result in unpredictable builds when the base image updates.",
                        "suggestion": "Pin to a specific slim/alpine version (e.g., FROM python:3.11-slim)."
                    })
                    
            # 3. Secrets in ENV/ARG Check
            if line_stripped.startswith("ENV") or line_stripped.startswith("ARG"):
                if "SECRET" in line_stripped or "PASSWORD" in line_stripped or "TOKEN" in line_stripped:
                    findings.append({
                        "title": "Secret in Dockerfile ENV/ARG",
                        "severity": "critical",
                        "file": file_path,
                        "line": i + 1,
                        "description": "Secrets injected via ENV or ARG are permanently visible in docker history and image layers.",
                        "suggestion": "Use runtime environment variables or secure Docker build secrets (--mount=type=secret) instead."
                    })
                    
            # 4. Broad COPY Check
            if line_stripped.startswith("COPY . .") or line_stripped.startswith("COPY . /"):
                findings.append({
                    "title": "Broad COPY instruction",
                    "severity": "low",
                    "file": file_path,
                    "line": i + 1,
                    "description": "COPY . . copies everything, which might include local secrets, .git folder, or venv if .dockerignore is missing.",
                    "suggestion": "Ensure a robust .dockerignore is present, or copy specific required directories explicitly."
                })
                
        # Root User Conclusion
        if not has_user:
            findings.append({
                "title": "Running as Root Container",
                "severity": "high",
                "file": file_path,
                "line": 0,
                "description": "No USER instruction found. The container will run as root, posing a severe security risk if broken out of.",
                "suggestion": "Create a non-root user and switch to it using the USER instruction before the CMD/ENTRYPOINT."
            })
            
        # 5. Multi-stage Build Check
        if from_count == 1:
            findings.append({
                "title": "Missing Multi-stage Build",
                "severity": "low",
                "file": file_path,
                "line": 0,
                "description": "Only one FROM instruction found. The final image may contain unnecessary build dependencies and compilers.",
                "suggestion": "Use multi-stage builds to compile in one stage and copy artifacts to a minimal runtime stage."
            })
            
        return findings
