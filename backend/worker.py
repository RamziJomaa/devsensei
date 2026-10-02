import uuid
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import AsyncSessionLocal
from backend.models import Analysis, AnalysisStatus, Report
from agents.graph import create_devsensei_graph
from agents.report_generator import ReportGenerator

async def run_analysis_background(analysis_id: uuid.UUID, repo_url: str):
    """Background worker task that drives the full multi-agent workflow."""
    async with AsyncSessionLocal() as db:
        # Update status
        analysis = await db.get(Analysis, analysis_id)
        if analysis:
            analysis.status = AnalysisStatus.RUNNING
            await db.commit()

        app = create_devsensei_graph()
        
        # Initialize graph state
        initial_state = {
            "analysis_id": str(analysis_id),
            "repo_url": repo_url,
            "repo_id": repo_url.replace("https://github.com/", ""),
            "file_tree": [],
            "messages": [],
            "findings": [],
            "report_draft": "",
            "eval_scores": {},
            "status": "running",
            "error": None
        }
        
        try:
            # Execute LangGraph Pipeline
            final_state = await app.ainvoke(initial_state)
            
            # Generate Final Report
            generator = ReportGenerator()
            report_data = generator.generate(final_state)
            eval_scores = final_state.get("eval_scores", {})
            
            # Persist to Database
            report = Report(
                analysis_id=analysis_id,
                markdown_content=report_data["markdown_content"],
                severity_counts=report_data["severity_counts"],
                faithfulness_score=eval_scores.get("faithfulness_score", 0.0),
                avg_finding_relevance=eval_scores.get("avg_finding_relevance", 0.0),
                avg_actionability=eval_scores.get("avg_actionability", 0.0)
            )
            db.add(report)
            
            analysis.status = AnalysisStatus.DONE
            analysis.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            print(f"Graph execution failed: {e}")
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.completed_at = datetime.utcnow()
                await db.commit()
