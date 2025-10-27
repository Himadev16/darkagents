"""
Agent Execution API Routes
Trigger and manage AI agent execution
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db, Project
from backend.database.models import User
from backend.api.dependencies import get_current_active_user
from backend.agents import ProductManagerAgent
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""
    project_id: int
    agent_name: str  # "product_manager", "system_architect", etc.
    input_data: dict = {}


class AgentExecutionResponse(BaseModel):
    """Response after triggering agent execution"""
    message: str
    project_id: int
    agent_name: str
    execution_id: int


def execute_agent_async(
    agent_name: str,
    project_id: int,
    input_data: dict,
    db: Session
):
    """
    Execute an agent asynchronously in the background

    This function runs in a background task so the API response is immediate
    """
    try:
        logger.info(
            "agent_execution_started",
            agent_name=agent_name,
            project_id=project_id
        )

        # Get the appropriate agent
        agent = None
        if agent_name == "product_manager":
            agent = ProductManagerAgent()
        # Add more agents here as we implement them
        # elif agent_name == "system_architect":
        #     agent = SystemArchitectAgent()
        else:
            logger.error("unknown_agent", agent_name=agent_name)
            return

        # Execute the agent
        result = agent.execute(project_id, input_data, db)

        logger.info(
            "agent_execution_completed",
            agent_name=agent_name,
            project_id=project_id,
            result_keys=list(result.keys())
        )

    except Exception as e:
        logger.error(
            "agent_execution_failed",
            agent_name=agent_name,
            project_id=project_id,
            error=str(e)
        )


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Trigger an AI agent to execute

    This endpoint:
    1. Validates the project belongs to the user
    2. Starts the agent in a background task
    3. Returns immediately with execution info
    4. Agent broadcasts progress via WebSocket

    Usage:
    ```bash
    curl -X POST http://localhost:8000/api/agents/execute \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": 1,
        "agent_name": "product_manager",
        "input_data": {}
      }'
    ```

    Then connect to WebSocket to watch real-time progress:
    ```js
    const ws = new WebSocket('ws://localhost:8000/ws/1');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_status') {
            console.log(data.data);
        }
    };
    ```
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Validate agent name
    valid_agents = [
        "product_manager",
        # Add more as we implement them
        # "system_architect",
        # "backend_developer",
        # etc.
    ]

    if request.agent_name not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent name. Valid agents: {', '.join(valid_agents)}"
        )

    # Create a new database session for the background task
    # (can't share sessions across threads)
    from backend.database import SessionLocal

    # Schedule agent execution in background
    background_tasks.add_task(
        execute_agent_async,
        agent_name=request.agent_name,
        project_id=request.project_id,
        input_data=request.input_data,
        db=SessionLocal()  # New session for background task
    )

    logger.info(
        "agent_execution_triggered",
        agent_name=request.agent_name,
        project_id=request.project_id,
        user_id=current_user.id
    )

    return {
        "message": f"{request.agent_name} execution started. Connect to WebSocket /ws/{request.project_id} for real-time updates.",
        "project_id": request.project_id,
        "agent_name": request.agent_name,
        "execution_id": 0  # Placeholder - will be created by agent
    }


@router.get("/available")
async def list_available_agents():
    """
    List all available agents

    Returns info about each agent including name, role, and status
    """
    agents = [
        {
            "name": "product_manager",
            "display_name": "Product Manager",
            "role": "Transform user ideas into detailed product requirements",
            "status": "available",
            "deliverables": [
                "Product Requirements Document (PRD)",
                "User Personas",
                "User Stories",
                "Feature Prioritization Matrix",
                "Success Metrics",
                "Competitive Analysis"
            ]
        },
        # Add more agents as we implement them
    ]

    return {
        "agents": agents,
        "total": len(agents)
    }
