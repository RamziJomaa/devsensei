from typing import Dict, Any
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.state import GraphState

class AggregatorAgent:
    def __init__(self):
        pass

    async def run(self, state: GraphState) -> GraphState:
        """Aggregates findings from all specialized agents into a unified markdown report draft."""
        findings = state.get("findings", [])
        if not findings:
            state["report_draft"] = "No structural issues or vulnerabilities were found in this repository."
            return state
            
        report = "# 📊 DevSensei Automated Analysis Report\n\n"
        report += "The following insights were generated autonomously across multiple agentic passes:\n\n"
        
        for idx, f in enumerate(findings):
            report += f"### {idx+1}. {f.get('title', 'Finding')}\n"
            report += f"**Severity:** {f.get('severity', 'Unknown')}\n"
            report += f"{f.get('description', '')}\n\n"
            if 'suggestion' in f:
                report += f"**Suggestion:** {f['suggestion']}\n\n"
            
        state["report_draft"] = report
        return state
