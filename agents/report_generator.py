from typing import Dict, Any, List
import json
from .state import GraphState

class ReportGenerator:
    def generate(self, state: GraphState) -> Dict[str, Any]:
        """
        Takes raw GraphState findings and evaluations, deduplicates them,
        calculates analytics, and produces the final structured Markdown report.
        """
        findings = state.get("findings", [])
        eval_scores = state.get("eval_scores", {})
        
        # 1. Deduplicate findings by file + line + type
        unique_findings = {}
        for f in findings:
            key = f"{f.get('file', 'unknown')}:{f.get('line', 0)}:{f.get('title', '')}"
            if key not in unique_findings:
                unique_findings[key] = f
        
        deduped = list(unique_findings.values())
        
        # 2. Calculate severity counts
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in deduped:
            sev = f.get('severity', 'low').lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
                
        # 3. Overall health score (100 - penalties)
        health_score = 100 - (severity_counts["critical"] * 20 + severity_counts["high"] * 10 + severity_counts["medium"] * 3 + severity_counts["low"] * 1)
        health_score = max(0, health_score)

        # 4. Markdown Generation
        md = "# 🛡️ DevSensei Analysis Report\n\n"
        md += "## Executive Summary\n"
        md += f"**Overall Health Score:** {health_score}/100\n\n"
        md += "| Critical | High | Medium | Low |\n"
        md += "|---|---|---|---|\n"
        md += f"| {severity_counts['critical']} | {severity_counts['high']} | {severity_counts['medium']} | {severity_counts['low']} |\n\n"

        critical_issues = [f for f in deduped if f.get('severity', '').lower() == 'critical']
        if critical_issues:
            md += "## 🚨 Critical Issues\n"
            for idx, f in enumerate(critical_issues):
                md += f"### {idx+1}. {f.get('title')}\n"
                md += f"**File:** `{f.get('file', 'unknown')}` (Line {f.get('line', 0)})\n"
                md += f"{f.get('description', '')}\n"
                md += f"**Fix:** {f.get('suggestion', '')}\n\n"

        other_issues = [f for f in deduped if f.get('severity', '').lower() != 'critical']
        if other_issues:
            md += "## 🛠️ Code & DevOps Findings\n"
            for idx, f in enumerate(other_issues):
                md += f"### {idx+1}. {f.get('title')} ({f.get('severity', 'LOW').upper()})\n"
                md += f"**File:** `{f.get('file', 'unknown')}` (Line {f.get('line', 0)})\n"
                md += f"{f.get('description', '')}\n"
                md += f"**Fix:** {f.get('suggestion', '')}\n\n"

        md += "## 🤖 Evaluation Scores\n"
        md += f"- **Faithfulness:** {eval_scores.get('faithfulness_score', 0.0):.2f}\n"
        md += f"- **Finding Relevance:** {eval_scores.get('avg_finding_relevance', 0.0):.2f}\n"
        md += f"- **Actionability:** {eval_scores.get('avg_actionability', 0.0):.2f}\n"

        return {
            "markdown_content": md,
            "severity_counts": severity_counts,
            "health_score": health_score
        }
