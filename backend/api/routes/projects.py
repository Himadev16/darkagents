"""
Projects API Routes
Project creation, retrieval, and management
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db, User, Project, AgentExecution, UsageMetric
from backend.database.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetail,
    ProjectUpdate
)
from backend.api.dependencies import get_current_active_user

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new DARKAGENTS project

    Args:
        project_data: Project creation data (name, description, user_idea, target_scale)
        current_user: Authenticated user
        db: Database session

    Returns:
        Created project object
    """
    new_project = Project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        user_idea=project_data.user_idea,
        target_scale=project_data.target_scale,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all projects for the current user

    Args:
        current_user: Authenticated user
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of projects
    """
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific project

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Detailed project information with agent executions and checkpoints

    Raises:
        HTTPException: If project not found or user doesn't have access
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Calculate total tokens and cost
    metrics = db.query(
        func.sum(UsageMetric.total_tokens).label("total_tokens"),
        func.sum(UsageMetric.cost_usd).label("total_cost")
    ).filter(UsageMetric.project_id == project_id).first()

    # Build response with additional data
    project_dict = {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "phase": project.phase,
        "user_idea": project.user_idea,
        "target_scale": project.target_scale,
        "overall_progress": project.overall_progress,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "completed_at": project.completed_at,
        "agent_executions": project.agent_executions,
        "checkpoints": project.checkpoints,
        "total_tokens_used": metrics.total_tokens or 0,
        "total_cost_usd": float(metrics.total_cost or 0.0)
    }

    return project_dict


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update project details

    Args:
        project_id: Project ID
        project_data: Fields to update
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or user doesn't have access
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project (soft delete by setting status to CANCELLED)

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If project not found or user doesn't have access
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Soft delete
    from backend.database.models import ProjectStatus
    project.status = ProjectStatus.CANCELLED
    db.commit()
