from fastapi import APIRouter, Cookie, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.websocket_manager import manager
from app.infrastructure.auth import get_session
from app.infrastructure.database import get_db
from app.infrastructure.request_context import get_logger
from app.repositories import get_user_repository, get_group_repository, get_run_repository

router = APIRouter()
logger = get_logger(__name__)


async def get_current_user_ws(
    session_token: str | None = Cookie(None, alias='session_token'), db: Session = Depends(get_db)
):
    """Get current user from WebSocket connection (via cookie)."""
    if not session_token:
        raise HTTPException(status_code=401, detail='Not authenticated')

    session_data = get_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail='Invalid or expired session')

    user_repo = get_user_repository(db); group_repo = get_group_repository(db); run_repo = get_run_repository(db)
    user = user_repo.get_user_by_id(session_data['user_id'])
    if not user:
        raise HTTPException(status_code=401, detail='User not found')

    return user


@router.websocket('/ws/groups/{group_id}')
async def websocket_group_endpoint(websocket: WebSocket, group_id: str) -> None:
    """WebSocket endpoint for group-level updates (new runs, run state changes)."""
    # IMPORTANT: Accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        from app.infrastructure.database import SessionLocal

        db = SessionLocal()

        # Try to get session token from cookie or query parameter
        session_token = None

        logger.debug('WebSocket connection attempt', extra={'endpoint': 'group', 'group_id': group_id})

        # Try cookie first
        if 'cookie' in websocket.headers:
            cookies = websocket.headers['cookie']
            for cookie in cookies.split(';'):
                if 'session_token=' in cookie:
                    session_token = cookie.split('session_token=')[1].strip()
                    break

        # If no cookie, try query parameter
        if not session_token and 'session_token' in websocket.query_params:
            session_token = websocket.query_params['session_token']

        # Authenticate user
        if not session_token:
            logger.warning('WebSocket auth failed: No session token', extra={'group_id': group_id})
            await websocket.close(code=1008, reason='Not authenticated - no session token')
            return

        session_data = get_session(session_token)
        if not session_data:
            logger.warning('WebSocket auth failed: Invalid session', extra={'group_id': group_id})
            await websocket.close(code=1008, reason='Invalid or expired session')
            return

        user_repo = get_user_repository(db); group_repo = get_group_repository(db); run_repo = get_run_repository(db)
        user_id = session_data['user_id']

        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            from uuid import UUID

            user_id = UUID(user_id)

        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning('WebSocket auth failed: User not found', extra={'user_id': str(user_id), 'group_id': group_id})
            await websocket.close(code=1008, reason='User not found')
            return

        # Verify user is member of group
        # Convert group_id to UUID
        if isinstance(group_id, str):
            from uuid import UUID

            group_id_uuid = UUID(group_id)
        else:
            group_id_uuid = group_id

        group = group_repo.get_group_by_id(group_id_uuid)
        if not group:
            logger.warning('WebSocket auth failed: Group not found', extra={'user_id': str(user_id), 'group_id': group_id})
            await websocket.close(code=1008, reason='Group not found')
            return

        # Check if user is member of group
        user_groups = user_repo.get_user_groups(user)
        is_member = any(g.id == group_id_uuid for g in user_groups)
        if not is_member:
            logger.warning('WebSocket auth failed: Not a member', extra={'user_id': str(user_id), 'group_id': group_id})
            await websocket.close(code=1008, reason='Not a member of this group')
            return

        logger.info('WebSocket connected', extra={'user_id': str(user_id), 'group_id': group_id, 'endpoint': 'group'})

        # Connect to room
        room_id = f'group:{group_id}'
        # Don't call manager.connect again since we already accepted
        if room_id not in manager.active_connections:
            manager.active_connections[room_id] = set()
        manager.active_connections[room_id].add(websocket)

        # Send connection confirmation
        await manager.send_personal(websocket, {'type': 'connected', 'data': {'room': room_id}})

        # Keep connection alive and listen for disconnection
        while True:
            # Receive messages (for heartbeat/ping-pong)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == 'ping':
                await websocket.send_text('pong')

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        logger.debug('WebSocket disconnected', extra={'group_id': group_id, 'endpoint': 'group'})
    finally:
     await db.close()


@router.websocket('/ws/runs/{run_id}')
async def websocket_run_endpoint(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint for run-level updates (bids, ready status, state changes)."""
    # IMPORTANT: Accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        from app.infrastructure.database import SessionLocal

        db = SessionLocal()

        # Try to get session token from cookie or query parameter
        session_token = None

        # Try cookie first
        if 'cookie' in websocket.headers:
            cookies = websocket.headers['cookie']
            for cookie in cookies.split(';'):
                if 'session_token=' in cookie:
                    session_token = cookie.split('session_token=')[1].strip()
                    break

        # If no cookie, try query parameter
        if not session_token and 'session_token' in websocket.query_params:
            session_token = websocket.query_params['session_token']

        # Authenticate user
        if not session_token:
            logger.warning('WebSocket auth failed: No session token', extra={'run_id': str(run_id)})
            await websocket.close(code=1008, reason='Not authenticated')
            return

        session_data = get_session(session_token)
        if not session_data:
            logger.warning('WebSocket auth failed: Invalid session', extra={'run_id': str(run_id)})
            await websocket.close(code=1008, reason='Invalid or expired session')
            return

        user_repo = get_user_repository(db); group_repo = get_group_repository(db); run_repo = get_run_repository(db)
        user_id = session_data['user_id']

        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            from uuid import UUID

            user_id = UUID(user_id)

        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning('WebSocket auth failed: User not found', extra={'user_id': str(user_id), 'run_id': str(run_id)})
            await websocket.close(code=1008, reason='User not found')
            return

        # Verify run exists and user has access
        # Convert run_id to UUID too
        if isinstance(run_id, str):
            from uuid import UUID

            run_id = UUID(run_id)

        run = run_repo.get_run_by_id(run_id)
        if not run:
            logger.warning('WebSocket auth failed: Run not found', extra={'user_id': str(user_id), 'run_id': str(run_id)})
            await websocket.close(code=1008, reason='Run not found')
            return

        # Check if user is in the group that owns this run
        user_groups = user_repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            logger.warning('WebSocket auth failed: Not authorized', extra={'user_id': str(user_id), 'run_id': str(run_id)})
            await websocket.close(code=1008, reason='Not authorized for this run')
            return

        logger.info('WebSocket connected', extra={'user_id': str(user_id), 'run_id': str(run_id), 'endpoint': 'run'})

        # Connect to room
        room_id = f'run:{run_id}'
        # Don't call manager.connect again since we already accepted
        if room_id not in manager.active_connections:
            manager.active_connections[room_id] = set()
        manager.active_connections[room_id].add(websocket)

        # Send connection confirmation
        await manager.send_personal(websocket, {'type': 'connected', 'data': {'room': room_id}})

        # Keep connection alive and listen for disconnection
        while True:
            # Receive messages (for heartbeat/ping-pong)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == 'ping':
                await websocket.send_text('pong')

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        logger.debug('WebSocket disconnected', extra={'run_id': str(run_id), 'endpoint': 'run'})
    finally:
       await db.close()


@router.websocket('/ws/user')
async def websocket_user_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for user-level updates (notifications)."""
    # IMPORTANT: Accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        from app.infrastructure.database import SessionLocal

        db = SessionLocal()

        # Try to get session token from cookie or query parameter
        session_token = None

        # Try cookie first
        if 'cookie' in websocket.headers:
            cookies = websocket.headers['cookie']
            for cookie in cookies.split(';'):
                if 'session_token=' in cookie:
                    session_token = cookie.split('session_token=')[1].strip()
                    break

        # If no cookie, try query parameter
        if not session_token and 'session_token' in websocket.query_params:
            session_token = websocket.query_params['session_token']

        # Authenticate user
        if not session_token:
            logger.warning('WebSocket auth failed: No session token', extra={'endpoint': 'user'})
            await websocket.close(code=1008, reason='Not authenticated')
            return

        session_data = get_session(session_token)
        if not session_data:
            logger.warning('WebSocket auth failed: Invalid session', extra={'endpoint': 'user'})
            await websocket.close(code=1008, reason='Invalid or expired session')
            return

        user_repo = get_user_repository(db); group_repo = get_group_repository(db); run_repo = get_run_repository(db)
        user_id = session_data['user_id']

        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            from uuid import UUID

            user_id = UUID(user_id)

        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning('WebSocket auth failed: User not found', extra={'user_id': str(user_id), 'endpoint': 'user'})
            await websocket.close(code=1008, reason='User not found')
            return

        logger.info('WebSocket connected', extra={'user_id': str(user_id), 'endpoint': 'user'})

        # Connect to user-specific room
        room_id = f'user:{user_id}'
        if room_id not in manager.active_connections:
            manager.active_connections[room_id] = set()
        manager.active_connections[room_id].add(websocket)

        # Send connection confirmation
        await manager.send_personal(websocket, {'type': 'connected', 'data': {'room': room_id}})

        # Keep connection alive and listen for disconnection
        while True:
            # Receive messages (for heartbeat/ping-pong)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == 'ping':
                await websocket.send_text('pong')

    except WebSocketDisconnect:
        room_id_disconnect = f'user:{user_id}'
        manager.disconnect(websocket, room_id_disconnect)
        logger.debug('WebSocket disconnected', extra={'user_id': str(user_id), 'endpoint': 'user'})
    finally:
        await db.close()
