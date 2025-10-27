"""
Pydantic Schemas for API Request/Response Validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from backend.database.models import (
    ProjectStatus, ProjectPhase, AgentStatus, IssueSeverity, IssueStatus
)


# ============================================================================
# USER SCHEMAS
# ============================================================================
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    user_idea: str = Field(..., min_length=10)
    target_scale: Optional[str] = Field(None, pattern="^(10K|100K|10M+)$")


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    phase: Optional[ProjectPhase] = None
    overall_progress: Optional[float] = Field(None, ge=0.0, le=100.0)


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    phase: ProjectPhase
    user_idea: str
    target_scale: Optional[str]
    overall_progress: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ProjectDetail will be defined after all its dependencies


# ============================================================================
# AGENT EXECUTION SCHEMAS
# ============================================================================
class AgentExecutionCreate(BaseModel):
    project_id: int
    agent_name: str
    agent_display_name: str


class AgentExecutionUpdate(BaseModel):
    status: Optional[AgentStatus] = None
    current_task: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    output: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


class AgentExecutionResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    agent_display_name: str
    status: AgentStatus
    current_task: Optional[str]
    progress: float
    output: Optional[str]
    error_message: Optional[str]
    tokens_used: int
    cost_usd: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AGENT COMMUNICATION SCHEMAS
# ============================================================================
class AgentCommunicationCreate(BaseModel):
    project_id: int
    from_agent: str
    to_agent: str
    message: str
    message_type: str = "info"


class AgentCommunicationResponse(BaseModel):
    id: int
    project_id: int
    from_agent: str
    to_agent: str
    message: str
    message_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# REVIEW FEEDBACK SCHEMAS
# ============================================================================
class ReviewFeedbackCreate(BaseModel):
    project_id: int
    reviewer_agent: str
    target_agent: str
    issue_title: str
    issue_description: str
    severity: IssueSeverity = IssueSeverity.MEDIUM
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class ReviewFeedbackUpdate(BaseModel):
    status: Optional[IssueStatus] = None
    resolution_notes: Optional[str] = None


class ReviewFeedbackResponse(BaseModel):
    id: int
    project_id: int
    reviewer_agent: str
    target_agent: str
    issue_title: str
    issue_description: str
    severity: IssueSeverity
    status: IssueStatus
    file_path: Optional[str]
    line_number: Optional[int]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CHECKPOINT SCHEMAS
# ============================================================================
class CheckpointCreate(BaseModel):
    project_id: int
    phase: ProjectPhase
    title: str
    description: str
    artifact_id: Optional[int] = None


class CheckpointApproval(BaseModel):
    approved: bool
    user_feedback: Optional[str] = None


class CheckpointResponse(BaseModel):
    id: int
    project_id: int
    phase: ProjectPhase
    title: str
    description: str
    approved: Optional[bool]
    user_feedback: Optional[str]
    artifact_id: Optional[int]
    created_at: datetime
    reviewed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GENERATED ARTIFACT SCHEMAS
# ============================================================================
class GeneratedArtifactCreate(BaseModel):
    project_id: int
    agent_name: str
    artifact_type: str
    artifact_name: str
    content: str
    content_type: str = "text/plain"
    file_path: Optional[str] = None
    artifact_metadata: Optional[dict] = None


class GeneratedArtifactResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    artifact_type: str
    artifact_name: str
    content: str
    content_type: str
    file_path: Optional[str]
    artifact_metadata: Optional[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# USAGE METRIC SCHEMAS
# ============================================================================
class UsageMetricCreate(BaseModel):
    project_id: int
    agent_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    api_calls: int = 1


class UsageMetricResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    api_calls: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WEBSOCKET MESSAGE SCHEMAS
# ============================================================================
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str
    project_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict


class AgentStatusMessage(BaseModel):
    """Agent status update for dashboard"""
    agent_name: str
    agent_display_name: str
    status: AgentStatus
    current_task: Optional[str]
    progress: float
    tokens_used: int
    cost_usd: float
    eta_seconds: Optional[int]


# ============================================================================
# PROJECT DETAIL (defined after dependencies)
# ============================================================================
class ProjectDetail(ProjectResponse):
    """Extended project response with related data"""
    agent_executions: List[AgentExecutionResponse] = []
    checkpoints: List[CheckpointResponse] = []
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
