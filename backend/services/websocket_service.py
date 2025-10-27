"""
WebSocket Manager
Handles WebSocket connections and broadcasts real-time updates to clients
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime
import structlog

logger = structlog.get_logger()


class WebSocketManager:
    """
    Manages WebSocket connections for real-time agent updates

    Features:
    - Multiple connections per project
    - Broadcast to all clients watching a project
    - Message types: agent_status, agent_communication, checkpoint_required
    - Automatic cleanup on disconnect
    """

    def __init__(self):
        # project_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int):
        """Accept a new WebSocket connection for a project"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()

        self.active_connections[project_id].add(websocket)

        logger.info(
            "websocket_connected",
            project_id=project_id,
            total_connections=len(self.active_connections[project_id])
        )

        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to DARKAGENTS mission control"
            }
        )

    def disconnect(self, websocket: WebSocket, project_id: int):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)

            # Clean up empty project connections
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

        logger.info(
            "websocket_disconnected",
            project_id=project_id,
            remaining_connections=len(self.active_connections.get(project_id, set()))
        )

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("websocket_send_failed", error=str(e))

    async def broadcast_to_project(self, project_id: int, message: dict):
        """
        Broadcast a message to all clients watching a project

        Message types:
        - agent_status: Real-time agent progress updates
        - agent_communication: Inter-agent messages
        - checkpoint_required: User approval needed
        - issue_found: Review feedback
        - issue_resolved: Issue fixed
        """
        if project_id not in self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        # Broadcast to all connections
        disconnected = set()
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error(
                    "websocket_broadcast_failed",
                    project_id=project_id,
                    error=str(e)
                )
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, project_id)

        logger.debug(
            "websocket_broadcast",
            project_id=project_id,
            message_type=message.get("type"),
            recipients=len(self.active_connections.get(project_id, set()))
        )

    async def broadcast_agent_status(
        self,
        project_id: int,
        agent_name: str,
        agent_display_name: str,
        status: str,
        current_task: str,
        progress: float,
        tokens_used: int,
        cost_usd: float,
        eta_seconds: int = None
    ):
        """
        Broadcast agent status update

        This is the main message type for the dashboard - shows live agent progress
        """
        message = {
            "type": "agent_status",
            "project_id": project_id,
            "data": {
                "agent_name": agent_name,
                "agent_display_name": agent_display_name,
                "status": status,
                "current_task": current_task,
                "progress": progress,
                "tokens_used": tokens_used,
                "cost_usd": round(cost_usd, 4),
                "eta_seconds": eta_seconds
            }
        }
        await self.broadcast_to_project(project_id, message)

    async def broadcast_agent_communication(
        self,
        project_id: int,
        from_agent: str,
        to_agent: str,
        message_text: str,
        message_type: str = "info"
    ):
        """
        Broadcast inter-agent communication

        Shows in the communication log on the dashboard
        """
        message = {
            "type": "agent_communication",
            "project_id": project_id,
            "data": {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message": message_text,
                "message_type": message_type
            }
        }
        await self.broadcast_to_project(project_id, message)

    async def broadcast_checkpoint_required(
        self,
        project_id: int,
        checkpoint_id: int,
        phase: str,
        title: str,
        description: str,
        artifact_id: int = None
    ):
        """
        Broadcast checkpoint approval request

        Pauses workflow until user approves
        """
        message = {
            "type": "checkpoint_required",
            "project_id": project_id,
            "data": {
                "checkpoint_id": checkpoint_id,
                "phase": phase,
                "title": title,
                "description": description,
                "artifact_id": artifact_id
            }
        }
        await self.broadcast_to_project(project_id, message)

    async def broadcast_issue_found(
        self,
        project_id: int,
        issue_id: int,
        reviewer_agent: str,
        target_agent: str,
        issue_title: str,
        severity: str
    ):
        """
        Broadcast issue discovered during review

        Shows in the issue tracker panel
        """
        message = {
            "type": "issue_found",
            "project_id": project_id,
            "data": {
                "issue_id": issue_id,
                "reviewer_agent": reviewer_agent,
                "target_agent": target_agent,
                "issue_title": issue_title,
                "severity": severity,
                "status": "open"
            }
        }
        await self.broadcast_to_project(project_id, message)

    async def broadcast_issue_resolved(
        self,
        project_id: int,
        issue_id: int
    ):
        """
        Broadcast issue resolution

        Updates the issue tracker panel
        """
        message = {
            "type": "issue_resolved",
            "project_id": project_id,
            "data": {
                "issue_id": issue_id,
                "status": "resolved"
            }
        }
        await self.broadcast_to_project(project_id, message)

    def get_connection_count(self, project_id: int) -> int:
        """Get number of active connections for a project"""
        return len(self.active_connections.get(project_id, set()))


# Global WebSocket manager instance
ws_manager = WebSocketManager()
