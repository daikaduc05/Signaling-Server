from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from typing import Dict, List
import json
import logging
from ..db import get_db
from ..models import User, Organization, VirtualIPMapping
from ..schemas import (
    RegisterAgentRequest,
    RegisterAgentResponse,
    PeerOnlineNotification,
    PeerInfo,
)
from ..utils import verify_token, log_info, log_error
from ..services import get_user_virtual_ip
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer()

# Store active connections by organization
active_connections: Dict[int, List[WebSocket]] = {}
# Store agent info by connection
agent_info: Dict[WebSocket, dict] = {}

logger = logging.getLogger(__name__)


def get_user_from_token(token: str, db: Session) -> User:
    """Get user from JWT token"""
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def broadcast_to_org(org_id: int, message: dict, exclude_ws: WebSocket = None):
    """Broadcast message to all connections in an organization"""
    if org_id in active_connections:
        for connection in active_connections[org_id]:
            if connection != exclude_ws:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    log_error(f"Error broadcasting to connection: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = None, db: Session = Depends(get_db)
):
    """WebSocket endpoint for signaling"""
    await websocket.accept()

    try:
        # Authenticate user
        if not token:
            await websocket.close(code=4001, reason="No token provided")
            return

        user = get_user_from_token(token, db)
        log_info(f"User {user.email} connected to WebSocket")

        # Wait for register message
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "register":
                    await handle_register(websocket, message, user, db)
                    break
                else:
                    await websocket.send_text(
                        json.dumps({"error": "First message must be register"})
                    )

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
            except Exception as e:
                log_error(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({"error": "Processing error"}))

        # Keep connection alive and handle other messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                # Handle other message types here if needed

            except WebSocketDisconnect:
                await handle_disconnect(websocket, user)
                break
            except Exception as e:
                log_error(f"WebSocket error: {e}")
                break

    except Exception as e:
        log_error(f"WebSocket connection error: {e}")
        await websocket.close()


async def handle_register(websocket: WebSocket, message: dict, user: User, db: Session):
    """Handle agent registration"""
    try:
        # Validate message
        org_id = message.get("org_id")
        agent_id = message.get("agent_id")
        public_ip = message.get("public_ip")
        public_port = message.get("public_port")

        if not all([org_id, agent_id, public_ip, public_port]):
            await websocket.send_text(json.dumps({"error": "Missing required fields"}))
            return

        # Check if user is member of organization
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org or user not in org.users:
            await websocket.send_text(
                json.dumps({"error": "User not member of organization"})
            )
            return

        # Get user's virtual IP
        virtual_ip = get_user_virtual_ip(db, user.id, org_id)
        if not virtual_ip:
            await websocket.send_text(
                json.dumps(
                    {"error": "No virtual IP allocated for user in this organization"}
                )
            )
            return

        # Store agent info
        agent_data = {
            "user_id": user.id,
            "email": user.email,
            "agent_id": agent_id,
            "public_ip": public_ip,
            "public_port": public_port,
            "virtual_ip": virtual_ip,
            "org_id": org_id,
        }
        agent_info[websocket] = agent_data

        # Add to active connections
        if org_id not in active_connections:
            active_connections[org_id] = []
        active_connections[org_id].append(websocket)

        # Get other peers in the organization
        peers = []
        for conn in active_connections[org_id]:
            if conn != websocket and conn in agent_info:
                peer_data = agent_info[conn]
                peers.append(
                    PeerInfo(
                        user_id=peer_data["user_id"],
                        email=peer_data["email"],
                        agent_id=peer_data["agent_id"],
                        public_ip=peer_data["public_ip"],
                        public_port=peer_data["public_port"],
                        virtual_ip=peer_data["virtual_ip"],
                    )
                )

        # Send registration response
        response = RegisterAgentResponse(status="registered", peers=peers)
        await websocket.send_text(json.dumps(response.dict()))

        # Notify other peers about new agent
        if peers:  # Only broadcast if there are other peers
            notification = PeerOnlineNotification(
                user_id=user.id,
                email=user.email,
                agent_id=agent_id,
                public_ip=public_ip,
                public_port=public_port,
                virtual_ip=virtual_ip,
            )
            await broadcast_to_org(org_id, notification.dict(), exclude_ws=websocket)

        log_info(f"Agent {agent_id} registered for user {user.email} in org {org_id}")

    except Exception as e:
        log_error(f"Error in handle_register: {e}")
        await websocket.send_text(json.dumps({"error": "Registration failed"}))


async def handle_disconnect(websocket: WebSocket, user: User):
    """Handle WebSocket disconnection"""
    try:
        if websocket in agent_info:
            agent_data = agent_info[websocket]
            org_id = agent_data["org_id"]

            # Remove from active connections
            if org_id in active_connections:
                if websocket in active_connections[org_id]:
                    active_connections[org_id].remove(websocket)
                if not active_connections[org_id]:
                    del active_connections[org_id]

            # Remove agent info
            del agent_info[websocket]

            log_info(f"Agent disconnected for user {user.email} in org {org_id}")

    except Exception as e:
        log_error(f"Error in handle_disconnect: {e}")
