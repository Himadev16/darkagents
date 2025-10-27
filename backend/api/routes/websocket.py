"""
WebSocket API Routes
Real-time communication for dashboard updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from backend.database import get_db, Project
from backend.services.websocket_service import ws_manager
import structlog

logger = structlog.get_logger()

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time project updates

    Usage (JavaScript):
    ```js
    const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.type, data);
    };
    ```

    Message types received:
    - connected: Initial connection confirmation
    - agent_status: Real-time agent progress
    - agent_communication: Inter-agent messages
    - checkpoint_required: User approval needed
    - issue_found: Review found an issue
    - issue_resolved: Issue was fixed
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        await websocket.close(code=1008, reason="Project not found")
        return

    # Accept connection
    await ws_manager.connect(websocket, project_id)

    try:
        # Keep connection alive and listen for client messages (if needed)
        while True:
            # Wait for any message from client (heartbeat, commands, etc.)
            data = await websocket.receive_text()

            # Handle client messages if needed
            # For now, we just log and ignore
            logger.debug(
                "websocket_client_message",
                project_id=project_id,
                message=data
            )

            # Echo back a pong for heartbeat
            if data == "ping":
                await ws_manager.send_personal_message(
                    websocket,
                    {"type": "pong", "project_id": project_id}
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)
        logger.info(
            "websocket_client_disconnected",
            project_id=project_id
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            project_id=project_id,
            error=str(e)
        )
        ws_manager.disconnect(websocket, project_id)
