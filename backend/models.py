from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime
from .database import Base

class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    triggered_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"))
    agent_name = Column(String)
    input_summary = Column(Text)
    output_summary = Column(Text)
    tokens_used = Column(Integer)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), unique=True)
    markdown_content = Column(Text)
    severity_counts = Column(JSON)
    faithfulness_score = Column(Float)
    avg_finding_relevance = Column(Float, nullable=True)
    avg_actionability = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
