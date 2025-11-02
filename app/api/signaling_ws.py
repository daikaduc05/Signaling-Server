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
import traceback
import uuid
import asyncio
import time
from datetime import datetime, timedelta
from ..db import get_db
from ..models import User, Organization
from ..schemas import (
    RegisterAgentResponse,
    PeerOnlineNotification,
    PeerOfflineNotification,
    PeerInfo,
    PingMessage,
    PongMessage,
)
from ..utils import verify_token, log_info, log_error, is_same_subnet
from ..services import get_user_virtual_ip

router = APIRouter()

# Store active connections by organization
active_connections: Dict[int, List[WebSocket]] = {}
# Store agent info by connection
agent_info: Dict[WebSocket, dict] = {}
# Store last pong time for each connection (for heartbeat)
last_pong_time: Dict[WebSocket, float] = {}

# Heartbeat configuration
PING_INTERVAL = 30  # Send ping every 30 seconds
PONG_TIMEOUT = 60  # Consider dead if no pong for 60 seconds


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


async def broadcast_to_org(
    org_id: int,
    message: dict,
    exclude_ws: WebSocket = None,
    subnet: str = None,
    virtual_ip: str = None,
):
    """Broadcast message to all connections in an organization with same subnet"""
    if org_id in active_connections:
        sent_count = 0
        for connection in active_connections[org_id]:
            if connection != exclude_ws and connection in agent_info:
                # Filter by subnet if provided
                if subnet and virtual_ip:
                    peer_data = agent_info[connection]
                    peer_virtual_ip = peer_data.get("virtual_ip")
                    if not is_same_subnet(virtual_ip, peer_virtual_ip, subnet):
                        continue  # Skip peers in different subnet

                try:
                    await connection.send_text(json.dumps(message))
                    sent_count += 1
                except Exception as e:
                    log_error(f"Error broadcasting to connection: {e}")
        return sent_count
    return 0


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for signaling"""
    await websocket.accept()

    try:
        # Get token from query parameters or headers
        token = None

        # Try to get token from query parameters
        if websocket.query_params.get("token"):
            token = websocket.query_params.get("token")

        # Try to get token from headers (Authorization: Bearer <token>)
        if not token:
            auth_header = websocket.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

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

        # Initialize heartbeat for this connection (after registration)
        if websocket in agent_info:
            # Start ping task and timeout checker
            # Note: last_pong_time will be set when first ping is sent or first pong is received
            ping_task = asyncio.create_task(send_ping_periodically(websocket))
            timeout_task = asyncio.create_task(check_timeout_and_disconnect(websocket, user, db))
            
            try:
                # Keep connection alive and handle other messages
                while True:
                    try:
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        # Handle pong message
                        if message.get("type") == "pong":
                            current_time = time.time()
                            # Update last pong time (create entry if not exists)
                            last_pong_time[websocket] = current_time
                            peer_id = agent_info.get(websocket, {}).get('peer_id', 'unknown')
                            log_info(f"Received pong from user {user.email} (peer_id: {peer_id})")
                            continue
                        
                        # Handle other messages here if needed
                        # For now, just acknowledge receipt
                        
                    except WebSocketDisconnect:
                        await handle_disconnect(websocket, user)
                        break
                    except Exception as e:
                        log_error(f"WebSocket error: {e}")
                        break
            finally:
                # Cancel tasks on disconnect
                ping_task.cancel()
                timeout_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass

    except Exception as e:
        log_error(f"WebSocket connection error: {e}")
        await websocket.close()


async def handle_register(websocket: WebSocket, message: dict, user: User, db: Session):
    """Handle agent registration"""
    try:
        log_info(f"Starting registration process for user {user.email} (ID: {user.id})")
        
        # Validate message fields
        agent_id = message.get("agent_id")  # Optional
        public_ip = message.get("public_ip")
        public_port = message.get("public_port")
        relay_ip = message.get("relay_ip")  # Optional
        relay_port = message.get("relay_port")  # Optional

        log_info(f"Registration request - agent_id: {agent_id}, public_ip: {public_ip}, public_port: {public_port}, relay_ip: {relay_ip}, relay_port: {relay_port}")

        # Validate required fields
        if not public_ip or not public_port:
            log_error(f"Registration failed for user {user.email}: Missing required fields (public_ip, public_port)")
            await websocket.send_text(json.dumps({"error": "Missing required fields: public_ip, public_port"}))
            return

        # Get user's organizations
        user_orgs = user.organizations
        if not user_orgs:
            log_error(f"Registration failed for user {user.email}: User not member of any organization")
            await websocket.send_text(
                json.dumps({"error": "User not member of any organization"})
            )
            return

        # Find organization where user has virtual IP allocated
        org = None
        virtual_ip = None
        for user_org in user_orgs:
            ip = get_user_virtual_ip(db, user.id, user_org.id)
            if ip:
                org = user_org
                virtual_ip = ip
                break

        if not org or not virtual_ip:
            log_error(f"Registration failed for user {user.email}: No virtual IP allocated in any organization")
            await websocket.send_text(
                json.dumps({"error": "No virtual IP allocated for user in any organization"})
            )
            return

        org_id = org.id
        log_info(f"User {user.email} verified as member of organization {org.name} (ID: {org_id})")
        log_info(f"Virtual IP {virtual_ip} assigned to user {user.email} in organization {org_id}")

        # Generate connection ID
        connection_id = str(uuid.uuid4())

        # Generate peer_id if agent_id not provided
        peer_id = agent_id if agent_id else f"peer_{user.id}_{connection_id[:8]}"

        # Store agent info with all fields
        agent_data = {
            "connection_id": connection_id,
            "peer_id": peer_id,
            "user_id": user.id,
            "email": user.email,
            "agent_id": agent_id,
            "public_ip": public_ip,
            "public_port": public_port,
            "relay_ip": relay_ip,
            "relay_port": relay_port,
            "virtual_ip": virtual_ip,
            "org_id": org_id,
            "subnet": org.subnet,
        }
        agent_info[websocket] = agent_data

        # Add to active connections
        if org_id not in active_connections:
            active_connections[org_id] = []
        active_connections[org_id].append(websocket)
        
        log_info(f"Agent {peer_id} added to active connections for organization {org_id}")

        # Get other peers in the organization with same subnet
        peers = []
        for conn in active_connections[org_id]:
            if conn != websocket and conn in agent_info:
                peer_data = agent_info[conn]
                peer_virtual_ip = peer_data.get("virtual_ip")
                
                # Filter by subnet: only include peers in same subnet
                if is_same_subnet(virtual_ip, peer_virtual_ip, org.subnet):
                    peers.append(
                        PeerInfo(
                            peer_id=peer_data.get("peer_id", peer_data.get("agent_id", "unknown")),
                            user_id=peer_data["user_id"],
                            email=peer_data["email"],
                            agent_id=peer_data.get("agent_id"),
                            public_ip=peer_data["public_ip"],
                            public_port=peer_data["public_port"],
                            relay_ip=peer_data.get("relay_ip"),
                            relay_port=peer_data.get("relay_port"),
                            virtual_ip=peer_data["virtual_ip"],
                        )
                    )

        log_info(f"Found {len(peers)} existing peers in same subnet for user {user.email} in organization {org_id}")

        # Send registration response
        response = RegisterAgentResponse(
            status="registered",
            virtual_ip=virtual_ip,
            connection_id=connection_id,
            existing_peers=peers,
        )
        await websocket.send_text(json.dumps(response.dict()))

        log_info(f"Registration response sent to user {user.email} with {len(peers)} peers in same subnet")

        # Notify other peers about new agent (only same subnet)
        if peers:
            notification = PeerOnlineNotification(
                peer=PeerInfo(
                    peer_id=peer_id,
                    user_id=user.id,
                    email=user.email,
                    agent_id=agent_id,
                    public_ip=public_ip,
                    public_port=public_port,
                    relay_ip=relay_ip,
                    relay_port=relay_port,
                    virtual_ip=virtual_ip,
                )
            )
            sent_count = await broadcast_to_org(
                org_id, notification.dict(), exclude_ws=websocket, subnet=org.subnet, virtual_ip=virtual_ip
            )
            log_info(f"Peer online notification broadcasted to {sent_count} peers in same subnet for organization {org_id}")

        log_info(f"Agent {peer_id} successfully registered for user {user.email} in org {org_id} with virtual IP {virtual_ip}")

    except Exception as e:
        log_error(f"Error in handle_register for user {user.email}: {e}")
        log_error(traceback.format_exc())
        await websocket.send_text(json.dumps({"error": "Registration failed"}))


async def handle_disconnect(websocket: WebSocket, user: User):
    """Handle WebSocket disconnection"""
    try:
        if websocket in agent_info:
            agent_data = agent_info[websocket]
            org_id = agent_data["org_id"]
            subnet = agent_data.get("subnet")
            virtual_ip = agent_data.get("virtual_ip")

            # Create PeerInfo for offline notification (before removing from agent_info)
            peer_info = PeerInfo(
                peer_id=agent_data.get("peer_id", agent_data.get("agent_id", "unknown")),
                user_id=agent_data["user_id"],
                email=agent_data["email"],
                agent_id=agent_data.get("agent_id"),
                public_ip=agent_data["public_ip"],
                public_port=agent_data["public_port"],
                relay_ip=agent_data.get("relay_ip"),
                relay_port=agent_data.get("relay_port"),
                virtual_ip=agent_data["virtual_ip"],
            )

            # Remove from active connections
            if org_id in active_connections:
                if websocket in active_connections[org_id]:
                    active_connections[org_id].remove(websocket)
                if not active_connections[org_id]:
                    del active_connections[org_id]

            # Remove agent info (must be done after creating PeerInfo)
            del agent_info[websocket]
            
            # Clean up heartbeat tracking
            if websocket in last_pong_time:
                del last_pong_time[websocket]

            # Notify other peers about peer going offline (only same subnet)
            notification = PeerOfflineNotification(peer=peer_info)
            sent_count = await broadcast_to_org(
                org_id, notification.dict(), exclude_ws=websocket, subnet=subnet, virtual_ip=virtual_ip
            )
            log_info(f"Peer offline notification broadcasted to {sent_count} peers in same subnet for organization {org_id}")
            log_info(f"Agent disconnected for user {user.email} (peer_id: {peer_info.peer_id}) in org {org_id}")

    except Exception as e:
        log_error(f"Error in handle_disconnect: {e}")
        log_error(traceback.format_exc())


async def send_ping_periodically(websocket: WebSocket):
    """Send ping message periodically to check connection health"""
    try:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            
            # Check if websocket is still active
            if websocket not in agent_info:
                break
                
            try:
                # Send ping message
                ping_message = PingMessage(timestamp=time.time())
                await websocket.send_text(json.dumps(ping_message.dict()))
                
                # Initialize last_pong_time on first ping if not already set
                if websocket not in last_pong_time:
                    last_pong_time[websocket] = time.time()
                
                log_info(f"Sent ping to connection (peer_id: {agent_info.get(websocket, {}).get('peer_id', 'unknown')})")
            except Exception as e:
                # Connection is likely dead, break loop
                log_error(f"Error sending ping: {e}")
                break
                
    except asyncio.CancelledError:
        log_info("Ping task cancelled")
    except Exception as e:
        log_error(f"Error in send_ping_periodically: {e}")


async def check_timeout_and_disconnect(websocket: WebSocket, user: User, db: Session):
    """Check if connection is dead (no pong received for PONG_TIMEOUT seconds)"""
    try:
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            # Check if websocket is still active
            if websocket not in agent_info:
                break
                
            current_time = time.time()
            last_pong = last_pong_time.get(websocket)
            
            if last_pong is None:
                # No pong tracking yet - connection just registered and no ping sent yet
                # Give it time until first ping is sent
                continue
                
            time_since_last_pong = current_time - last_pong
            
            # Check if no pong received for more than PONG_TIMEOUT seconds
            if time_since_last_pong > PONG_TIMEOUT:
                # Connection is dead, disconnect
                log_error(f"Connection timeout for user {user.email}: No pong received for {time_since_last_pong:.1f} seconds")
                try:
                    await handle_disconnect(websocket, user)
                    await websocket.close(code=1000, reason="Connection timeout - no pong received")
                except Exception as e:
                    log_error(f"Error during timeout disconnect: {e}")
                break
                
    except asyncio.CancelledError:
        log_info("Timeout checker task cancelled")
    except Exception as e:
        log_error(f"Error in check_timeout_and_disconnect: {e}")
