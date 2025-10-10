from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
import json


class ConnectionManager:
    """Manages WebSocket connections organized by rooms (groups and runs)."""

    def __init__(self):
        # rooms: {"group:uuid": set(websocket), "run:uuid": set(websocket)}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        """Add a client to a room."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        """Remove a client from a room."""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            # Clean up empty rooms
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        """Send a message to all clients in a room."""
        if room_id not in self.active_connections:
            return

        # Add timestamp to all messages
        message['timestamp'] = datetime.now().isoformat() + 'Z'
        message_json = json.dumps(message)

        # Send to all connections, remove dead ones
        dead_connections = set()
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(message_json)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        for dead in dead_connections:
            self.active_connections[room_id].discard(dead)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        message['timestamp'] = datetime.now().isoformat() + 'Z'
        await websocket.send_text(json.dumps(message))


# Global connection manager instance
manager = ConnectionManager()
