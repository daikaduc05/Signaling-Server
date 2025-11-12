"""
MVP Signaling Server - FastAPI WebSocket Server
Simple signaling server for WebRTC peer-to-peer connections
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MVP Signaling Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for connected clients
connected_clients: Dict[str, WebSocket] = {}
client_rooms: Dict[str, Set[str]] = {}  # room_id -> set of client_ids


class SignalingMessage(BaseModel):
    type: str
    from_id: str = None
    to_id: str = None
    data: dict = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "MVP Signaling Server",
        "version": "1.0.0",
        "connected_clients": len(connected_clients),
        "active_rooms": len(client_rooms),
    }


@app.get("/status")
async def status():
    """Get server status"""
    return {
        "connected_clients": len(connected_clients),
        "clients": list(connected_clients.keys()),
        "active_rooms": len(client_rooms),
        "rooms": {room_id: list(clients) for room_id, clients in client_rooms.items()},
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint for signaling"""
    await websocket.accept()
    connected_clients[client_id] = websocket
    logger.info(
        f"Client {client_id} connected. Total clients: {len(connected_clients)}"
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            await handle_message(client_id, message, websocket)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        await cleanup_client(client_id)
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        await cleanup_client(client_id)


async def handle_message(client_id: str, message: dict, websocket: WebSocket):
    """Handle incoming signaling messages"""
    msg_type = message.get("type")

    if msg_type == "register":
        await handle_register(client_id, message, websocket)
    elif msg_type == "offer":
        await handle_offer(client_id, message)
    elif msg_type == "answer":
        await handle_answer(client_id, message)
    elif msg_type == "candidate":
        await handle_candidate(client_id, message)
    elif msg_type == "bye":
        await handle_bye(client_id, message)
    else:
        logger.warning(f"Unknown message type from {client_id}: {msg_type}")


async def handle_register(client_id: str, message: dict, websocket: WebSocket):
    """Handle client registration"""
    token = message.get("token")
    logger.info(f"Client {client_id} registered with token: {token}")

    # Send registration confirmation
    response = {"type": "registered", "id": client_id, "status": "success"}
    await websocket.send_text(json.dumps(response))


async def handle_offer(client_id: str, message: dict):
    """Handle WebRTC offer"""
    to_id = message.get("to")
    if not to_id:
        logger.error(f"Offer from {client_id} missing 'to' field")
        return

    if to_id not in connected_clients:
        logger.warning(f"Offer from {client_id} to unknown client {to_id}")
        # Send error back to sender
        error_msg = {"type": "error", "message": f"Target client {to_id} not found"}
        await send_to_client(client_id, error_msg)
        return

    # Forward offer to target client
    offer_msg = {
        "type": "offer",
        "from": client_id,
        "to": to_id,
        "sdp": message.get("sdp"),
    }
    await send_to_client(to_id, offer_msg)
    logger.info(f"Forwarded offer from {client_id} to {to_id}")


async def handle_answer(client_id: str, message: dict):
    """Handle WebRTC answer"""
    to_id = message.get("to")
    if not to_id:
        logger.error(f"Answer from {client_id} missing 'to' field")
        return

    if to_id not in connected_clients:
        logger.warning(f"Answer from {client_id} to unknown client {to_id}")
        return

    # Forward answer to target client
    answer_msg = {
        "type": "answer",
        "from": client_id,
        "to": to_id,
        "sdp": message.get("sdp"),
    }
    await send_to_client(to_id, answer_msg)
    logger.info(f"Forwarded answer from {client_id} to {to_id}")


async def handle_candidate(client_id: str, message: dict):
    """Handle ICE candidate"""
    to_id = message.get("to")
    if not to_id:
        logger.error(f"Candidate from {client_id} missing 'to' field")
        return

    if to_id not in connected_clients:
        logger.warning(f"Candidate from {client_id} to unknown client {to_id}")
        return

    # Forward candidate to target client
    candidate_msg = {
        "type": "candidate",
        "from": client_id,
        "to": to_id,
        "candidate": message.get("candidate"),
    }
    await send_to_client(to_id, candidate_msg)
    logger.info(f"Forwarded ICE candidate from {client_id} to {to_id}")


async def handle_bye(client_id: str, message: dict):
    """Handle connection termination"""
    to_id = message.get("to")
    if to_id and to_id in connected_clients:
        # Forward bye message to target client
        bye_msg = {"type": "bye", "from": client_id, "to": to_id}
        await send_to_client(to_id, bye_msg)
        logger.info(f"Forwarded bye from {client_id} to {to_id}")


async def send_to_client(client_id: str, message: dict):
    """Send message to specific client"""
    if client_id in connected_clients:
        try:
            websocket = connected_clients[client_id]
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            await cleanup_client(client_id)


async def cleanup_client(client_id: str):
    """Clean up client connection and remove from rooms"""
    connected_clients.pop(client_id, None)

    rooms_to_remove = []
    for room_id, clients in client_rooms.items():
        if client_id in clients:
            clients.discard(client_id)
        if not clients:
            rooms_to_remove.append(room_id)

    for room_id in rooms_to_remove:
        del client_rooms[room_id]

    logger.info(
        f"Cleaned up client {client_id}. Remaining clients: {len(connected_clients)}"
    )


@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    logger.info("MVP Signaling Server starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Server shutdown event"""
    logger.info("MVP Signaling Server shutting down...")
    # Close all WebSocket connections
    for client_id, websocket in connected_clients.items():
        try:
            await websocket.close()
        except:
            pass
    connected_clients.clear()
    client_rooms.clear()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
