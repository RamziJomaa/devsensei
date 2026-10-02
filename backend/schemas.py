from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID
from .models import AnalysisStatus

class AnalyseRequest(BaseModel):
    repo_url: HttpUrl
    github_token: Optional[str] = None

class AnalyseResponse(BaseModel):
    analysis_id: UUID
    status: AnalysisStatus
    message: str

class AnalysisStatusResponse(BaseModel):
    analysis_id: UUID
    status: AnalysisStatus
    repo_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ReportResponse(BaseModel):
    report_id: UUID
    analysis_id: UUID
    markdown_content: str
    severity_counts: Dict[str, int]
    faithfulness_score: Optional[float] = None
    avg_finding_relevance: Optional[float] = None
    avg_actionability: Optional[float] = None
    created_at: datetime
    agent_timings: Dict[str, int] = Field(default_factory=dict, description="Milliseconds spent executing each agent")
