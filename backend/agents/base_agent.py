"""
Base Agent Class
Parent class for all 11 DARKAGENTS specialized agents
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from langchain.memory import ConversationBufferMemory
from sqlalchemy.orm import Session

from backend.services.claude_service import claude_service
from backend.database import (
    AgentExecution, AgentCommunication, UsageMetric, Project
)
from backend.database.models import AgentStatus
import structlog

logger = structlog.get_logger()


class BaseAgent:
    """
    Base class for all DARKAGENTS agents

    Each agent has:
    - Unique name and personality
    - LangChain memory for conversation context
    - Progress tracking
    - Communication with other agents
    - Token/cost tracking
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        role: str,
        temperature: float = 0.5,
        max_tokens: int = 4096
    ):
        self.name = name
        self.display_name = display_name
        self.role = role
        self.temperature = temperature
        self.max_tokens = max_tokens

        # LangChain memory for conversation context
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )

        # Personality prompt (to be overridden by subclasses)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with personality
        Should be overridden by subclasses to add specific personality
        """
        return f"""You are {self.display_name}, a specialized AI agent in the DARKAGENTS platform.

Your role: {self.role}

You are part of an 11-agent team building production-ready SaaS applications.
Always stay in character and perform your role with excellence."""

    def execute(
        self,
        project_id: int,
        input_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the agent's main task

        Args:
            project_id: Project ID
            input_data: Input data for the agent
            db: Database session

        Returns:
            Dict with agent output, deliverables, and metadata
        """
        # Create agent execution record
        execution = self._create_execution(project_id, db)

        try:
            # Update status to WORKING
            self._update_status(execution, AgentStatus.WORKING, "Starting work...", 0, db)

            # Perform the agent's work (to be implemented by subclasses)
            result = self._perform_work(input_data, execution, db)

            # Update status to COMPLETED
            self._update_status(execution, AgentStatus.COMPLETED, "Work completed", 100, db)

            # Save output
            execution.output = json.dumps(result)
            db.commit()

            logger.info(
                "agent_completed",
                agent=self.name,
                project_id=project_id,
                tokens=execution.tokens_used,
                cost=execution.cost_usd
            )

            return result

        except Exception as e:
            # Update status to ERROR
            execution.status = AgentStatus.ERROR
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()

            logger.error(
                "agent_failed",
                agent=self.name,
                project_id=project_id,
                error=str(e)
            )

            raise

    def _perform_work(
        self,
        input_data: Dict[str, Any],
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Perform the agent's specific work
        Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _perform_work()")

    def _create_execution(self, project_id: int, db: Session) -> AgentExecution:
        """Create an agent execution record"""
        execution = AgentExecution(
            project_id=project_id,
            agent_name=self.name,
            agent_display_name=self.display_name,
            status=AgentStatus.QUEUED,
            progress=0.0,
            tokens_used=0,
            cost_usd=0.0,
            started_at=datetime.utcnow()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    def _update_status(
        self,
        execution: AgentExecution,
        status: AgentStatus,
        task: str,
        progress: float,
        db: Session
    ):
        """Update agent execution status"""
        execution.status = status
        execution.current_task = task
        execution.progress = progress

        if status == AgentStatus.COMPLETED or status == AgentStatus.ERROR:
            execution.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(execution)

        logger.info(
            "agent_status_update",
            agent=self.name,
            status=status.value,
            task=task,
            progress=progress
        )

    def chat(
        self,
        user_message: str,
        execution: AgentExecution,
        db: Session
    ) -> str:
        """
        Have a conversation with Claude using the agent's personality

        Args:
            user_message: Message from user or another agent
            execution: Current execution record
            db: Database session

        Returns:
            Claude's response
        """
        # Add user message to memory
        self.memory.chat_memory.add_user_message(user_message)

        # Get conversation history
        history = self.memory.load_memory_variables({})
        messages = []

        # Convert LangChain messages to Claude format
        if "chat_history" in history:
            for msg in history["chat_history"]:
                messages.append({
                    "role": "user" if msg.type == "human" else "assistant",
                    "content": msg.content
                })

        # Add current message if not in history
        if not messages or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # Call Claude
        response = claude_service.generate(
            messages=messages,
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Add response to memory
        self.memory.chat_memory.add_ai_message(response["content"])

        # Track usage
        self._track_usage(execution, response, db)

        return response["content"]

    def _track_usage(
        self,
        execution: AgentExecution,
        response: Dict[str, Any],
        db: Session
    ):
        """Track token usage and cost"""
        usage = response["usage"]

        # Update execution totals
        execution.tokens_used += usage["total_tokens"]
        execution.cost_usd += response["cost_usd"]

        # Create usage metric record
        metric = UsageMetric(
            project_id=execution.project_id,
            agent_name=self.name,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            cost_usd=response["cost_usd"],
            api_calls=1
        )
        db.add(metric)
        db.commit()

        logger.info(
            "agent_usage_tracked",
            agent=self.name,
            tokens=usage["total_tokens"],
            cost=response["cost_usd"]
        )

    def send_message(
        self,
        to_agent: str,
        message: str,
        project_id: int,
        db: Session,
        message_type: str = "info"
    ):
        """
        Send a message to another agent

        Args:
            to_agent: Name of recipient agent
            message: Message content
            project_id: Project ID
            db: Database session
            message_type: Type of message (info, warning, error, success)
        """
        communication = AgentCommunication(
            project_id=project_id,
            from_agent=self.name,
            to_agent=to_agent,
            message=message,
            message_type=message_type
        )
        db.add(communication)
        db.commit()

        logger.info(
            "agent_message_sent",
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type
        )

    def get_messages(
        self,
        project_id: int,
        db: Session,
        from_agent: Optional[str] = None
    ) -> List[AgentCommunication]:
        """
        Get messages sent to this agent

        Args:
            project_id: Project ID
            db: Database session
            from_agent: Optional filter by sender

        Returns:
            List of messages
        """
        query = db.query(AgentCommunication).filter(
            AgentCommunication.project_id == project_id,
            AgentCommunication.to_agent == self.name
        )

        if from_agent:
            query = query.filter(AgentCommunication.from_agent == from_agent)

        return query.order_by(AgentCommunication.created_at).all()

    def get_project(self, project_id: int, db: Session) -> Project:
        """Get project details"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project
