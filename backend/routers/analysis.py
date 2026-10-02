from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ..database import get_db
from ..models import Analysis, Repository, Report, AnalysisStatus, AgentLog
from ..schemas import AnalyseRequest, AnalyseResponse, AnalysisStatusResponse, ReportResponse

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

@router.post("/analyse", response_model=AnalyseResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(request: AnalyseRequest, db: AsyncSession = Depends(get_db)):
    # 1. Get or create repository
    repo_url_str = str(request.repo_url)
    result = await db.execute(select(Repository).where(Repository.url == repo_url_str))
    repo = result.scalars().first()
    
    if not repo:
        repo = Repository(url=repo_url_str, name=repo_url_str.split("/")[-1])
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

    # 2. Create Analysis record
    analysis = Analysis(repo_id=repo.id, status=AnalysisStatus.PENDING, triggered_by="api_user")
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # 3. (Placeholder) Trigger background AI task here...
    # e.g., send analysis_id to Celery, Redis queue, or directly start background LangGraph execution

    return AnalyseResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        message="Analysis triggered successfully. Poll status endpoint for updates."
    )

@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = result.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return AnalysisStatusResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at
    )

@router.get("/report/{analysis_id}", response_model=ReportResponse)
async def get_report(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.analysis_id == analysis_id))
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not ready yet")
        
    # Fetch execution timings
    logs_result = await db.execute(select(AgentLog).where(AgentLog.analysis_id == analysis_id))
    logs = logs_result.scalars().all()
    
    timings = {}
    for log in logs:
        timings[log.agent_name] = timings.get(log.agent_name, 0) + log.duration_ms
        
    return ReportResponse(
        report_id=report.id,
        analysis_id=report.analysis_id,
        markdown_content=report.markdown_content,
        severity_counts=report.severity_counts,
        faithfulness_score=report.faithfulness_score,
        avg_finding_relevance=report.avg_finding_relevance,
        avg_actionability=report.avg_actionability,
        created_at=report.created_at,
        agent_timings=timings
    )
