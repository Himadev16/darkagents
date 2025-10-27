"""
DARKAGENTS Database Models
SQLAlchemy 2.0 models for all core tables
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, JSON, DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class ProjectStatus(str, enum.Enum):
    """Project lifecycle status"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectPhase(str, enum.Enum):
    """Project workflow phases (11 phases total)"""
    REQUIREMENTS = "requirements"  # PM Agent
    ARCHITECTURE = "architecture"  # System Architect
    BACKEND_DEV = "backend_dev"  # Backend Developer
    CODE_REVIEW = "code_review"  # 4 parallel reviewers
    UI_DESIGN = "ui_design"  # UI/UX Designer
    FRONTEND_DEV = "frontend_dev"  # Frontend Developer
    QA_TESTING = "qa_testing"  # QA Engineer
    DEVOPS = "devops"  # DevOps Engineer
    MARKETING = "marketing"  # Growth Marketer
    BUSINESS = "business"  # Business Strategist
    FINAL_INTEGRATION = "final_integration"  # Platform Orchestrator


class AgentStatus(str, enum.Enum):
    """Agent execution status"""
    IDLE = "idle"
    QUEUED = "queued"
    WORKING = "working"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"


class IssueSeverity(str, enum.Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(str, enum.Enum):
    """Issue resolution status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


# ============================================================================
# TABLE 1: USERS
# ============================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="user")


# ============================================================================
# TABLE 2: PROJECTS
# ============================================================================
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Project state
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.INITIALIZING)
    phase: Mapped[ProjectPhase] = mapped_column(Enum(ProjectPhase), default=ProjectPhase.REQUIREMENTS)

    # User input
    user_idea: Mapped[str] = mapped_column(Text, nullable=False)
    target_scale: Mapped[Optional[str]] = mapped_column(String(50))  # 10K, 100K, 10M+

    # Progress tracking
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100%

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    agent_executions: Mapped[list["AgentExecution"]] = relationship("AgentExecution", back_populates="project")
    agent_communications: Mapped[list["AgentCommunication"]] = relationship("AgentCommunication", back_populates="project")
    review_feedback: Mapped[list["ReviewFeedback"]] = relationship("ReviewFeedback", back_populates="project")
    checkpoints: Mapped[list["Checkpoint"]] = relationship("Checkpoint", back_populates="project")
    generated_artifacts: Mapped[list["GeneratedArtifact"]] = relationship("GeneratedArtifact", back_populates="project")
    usage_metrics: Mapped[list["UsageMetric"]] = relationship("UsageMetric", back_populates="project")


# ============================================================================
# TABLE 3: AGENT EXECUTIONS
# ============================================================================
class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Agent identification
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)  # product_manager, system_architect, etc.
    agent_display_name: Mapped[str] = mapped_column(String(100))  # "Product Manager", "System Architect"

    # Execution state
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.QUEUED)
    current_task: Mapped[Optional[str]] = mapped_column(String(500))  # "Writing API endpoints..."
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100%

    # Output
    output: Mapped[Optional[str]] = mapped_column(Text)  # JSON-serialized deliverables
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Metrics
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="agent_executions")


# ============================================================================
# TABLE 4: AGENT COMMUNICATIONS
# ============================================================================
class AgentCommunication(Base):
    __tablename__ = "agent_communications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Communication details
    from_agent: Mapped[str] = mapped_column(String(100), nullable=False)  # sender agent name
    to_agent: Mapped[str] = mapped_column(String(100), nullable=False)  # recipient agent name
    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), default="info")  # info, warning, error, success

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="agent_communications")


# ============================================================================
# TABLE 5: REVIEW FEEDBACK
# ============================================================================
class ReviewFeedback(Base):
    __tablename__ = "review_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Review details
    reviewer_agent: Mapped[str] = mapped_column(String(100), nullable=False)  # pm, architect, qa, security
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)  # usually backend_developer

    # Issue details
    issue_title: Mapped[str] = mapped_column(String(500), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IssueSeverity] = mapped_column(Enum(IssueSeverity), default=IssueSeverity.MEDIUM)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus), default=IssueStatus.OPEN)

    # Code location (optional)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)

    # Resolution
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="review_feedback")


# ============================================================================
# TABLE 6: CHECKPOINTS
# ============================================================================
class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Checkpoint details
    phase: Mapped[ProjectPhase] = mapped_column(Enum(ProjectPhase), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # "Review PRD", "Review Architecture"
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Approval state
    approved: Mapped[Optional[bool]] = mapped_column(Boolean)  # None=pending, True=approved, False=rejected
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Related artifact (for user to review)
    artifact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("generated_artifacts.id"))

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="checkpoints")


# ============================================================================
# TABLE 7: GENERATED ARTIFACTS
# ============================================================================
class GeneratedArtifact(Base):
    __tablename__ = "generated_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Artifact details
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)  # prd, architecture, code, design, docs
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Product Requirements Document"

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Actual content (code, markdown, JSON)
    content_type: Mapped[str] = mapped_column(String(50), default="text/plain")  # MIME type

    # Metadata
    file_path: Mapped[Optional[str]] = mapped_column(String(500))  # For code files: "backend/api/main.py"
    artifact_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Additional metadata as JSON

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="generated_artifacts")


# ============================================================================
# TABLE 8: USAGE METRICS
# ============================================================================
class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)

    # Agent metrics
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Cost (USD)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # API calls
    api_calls: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="usage_metrics")
