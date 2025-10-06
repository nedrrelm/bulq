from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Cookie, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..repository import get_repository
from ..websocket_manager import manager
from ..auth import get_session

router = APIRouter()


async def get_current_user_ws(
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
):
    """Get current user from WebSocket connection (via cookie)."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    repo = get_repository(db)
    user = repo.get_user_by_id(session_data["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.websocket("/ws/groups/{group_id}")
async def websocket_group_endpoint(
    websocket: WebSocket,
    group_id: str
):
    """WebSocket endpoint for group-level updates (new runs, run state changes)."""

    # IMPORTANT: Accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        from ..database import SessionLocal
        db = SessionLocal()

        # Try to get session token from cookie or query parameter
        session_token = None

        # Debug: print headers
        print(f"[GROUP WS] Headers: {dict(websocket.headers)}")
        print(f"[GROUP WS] Query params: {dict(websocket.query_params)}")

        # Try cookie first
        if "cookie" in websocket.headers:
            cookies = websocket.headers["cookie"]
            for cookie in cookies.split(";"):
                if "session_token=" in cookie:
                    session_token = cookie.split("session_token=")[1].strip()
                    break

        # If no cookie, try query parameter
        if not session_token and "session_token" in websocket.query_params:
            session_token = websocket.query_params["session_token"]

        print(f"[GROUP WS] Extracted session_token: {session_token}")

        # Authenticate user
        if not session_token:
            print(f"[GROUP WS] ERROR: No session token")
            await websocket.close(code=1008, reason="Not authenticated - no session token")
            return

        session_data = get_session(session_token)
        print(f"[GROUP WS] Session data: {session_data}")
        if not session_data:
            print(f"[GROUP WS] ERROR: Invalid or expired session")
            await websocket.close(code=1008, reason="Invalid or expired session")
            return

        repo = get_repository(db)
        user_id = session_data["user_id"]
        print(f"[GROUP WS] Looking up user_id: {user_id} (type: {type(user_id)})")

        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            from uuid import UUID
            user_id = UUID(user_id)

        user = repo.get_user_by_id(user_id)
        print(f"[GROUP WS] User: {user}")
        if not user:
            print(f"[GROUP WS] ERROR: User not found")
            await websocket.close(code=1008, reason="User not found")
            return

        # Verify user is member of group
        # Convert group_id to UUID
        if isinstance(group_id, str):
            from uuid import UUID
            group_id_uuid = UUID(group_id)
        else:
            group_id_uuid = group_id

        group = repo.get_group_by_id(group_id_uuid)
        print(f"[GROUP WS] Group: {group}")
        if not group:
            print(f"[GROUP WS] ERROR: Group not found")
            await websocket.close(code=1008, reason="Group not found")
            return

        # Check if user is member of group
        user_groups = repo.get_user_groups(user)
        is_member = any(g.id == group_id_uuid for g in user_groups)
        print(f"[GROUP WS] Is member: {is_member}")
        if not is_member:
            print(f"[GROUP WS] ERROR: Not a member of this group")
            await websocket.close(code=1008, reason="Not a member of this group")
            return

        print(f"[GROUP WS] Authentication successful! Connecting to room...")

        # Connect to room
        room_id = f"group:{group_id}"
        # Don't call manager.connect again since we already accepted
        if room_id not in manager.active_connections:
            manager.active_connections[room_id] = set()
        manager.active_connections[room_id].add(websocket)

        # Send connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "data": {"room": room_id}
        })

        # Keep connection alive and listen for disconnection
        while True:
            # Receive messages (for heartbeat/ping-pong)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    finally:
        db.close()


@router.websocket("/ws/runs/{run_id}")
async def websocket_run_endpoint(
    websocket: WebSocket,
    run_id: str
):
    """WebSocket endpoint for run-level updates (bids, ready status, state changes)."""

    # IMPORTANT: Accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        from ..database import SessionLocal
        db = SessionLocal()

        # Try to get session token from cookie or query parameter
        session_token = None

        # Try cookie first
        if "cookie" in websocket.headers:
            cookies = websocket.headers["cookie"]
            for cookie in cookies.split(";"):
                if "session_token=" in cookie:
                    session_token = cookie.split("session_token=")[1].strip()
                    break

        # If no cookie, try query parameter
        if not session_token and "session_token" in websocket.query_params:
            session_token = websocket.query_params["session_token"]

        # Authenticate user
        if not session_token:
            await websocket.close(code=1008, reason="Not authenticated")
            return

        session_data = get_session(session_token)
        if not session_data:
            await websocket.close(code=1008, reason="Invalid or expired session")
            return

        repo = get_repository(db)
        user_id = session_data["user_id"]

        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            from uuid import UUID
            user_id = UUID(user_id)

        user = repo.get_user_by_id(user_id)
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return

        # Verify run exists and user has access
        # Convert run_id to UUID too
        if isinstance(run_id, str):
            from uuid import UUID
            run_id = UUID(run_id)

        run = repo.get_run_by_id(run_id)
        if not run:
            await websocket.close(code=1008, reason="Run not found")
            return

        # Check if user is in the group that owns this run
        user_groups = repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            await websocket.close(code=1008, reason="Not authorized for this run")
            return

        # Connect to room
        room_id = f"run:{run_id}"
        # Don't call manager.connect again since we already accepted
        if room_id not in manager.active_connections:
            manager.active_connections[room_id] = set()
        manager.active_connections[room_id].add(websocket)

        # Send connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "data": {"room": room_id}
        })

        # Keep connection alive and listen for disconnection
        while True:
            # Receive messages (for heartbeat/ping-pong)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    finally:
        db.close()
