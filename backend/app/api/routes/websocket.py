from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.websocket_manager import manager
from app.infrastructure.auth import get_session
from app.infrastructure.database import AsyncSessionLocal, get_db
from app.infrastructure.request_context import get_logger
from app.repositories import get_group_repository, get_run_repository, get_user_repository

router = APIRouter()
logger = get_logger(__name__)


async def get_current_user_ws(
    session_token: str | None = Cookie(None, alias='session_token'),
    db: AsyncSession = Depends(get_db),
):
    """Get current user from WebSocket connection (via cookie)."""
    if not session_token:
        raise HTTPException(status_code=401, detail='Not authenticated')

    session_data = await get_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail='Invalid or expired session')

    user_repo = get_user_repository(db)
    user = await user_repo.get_user_by_id(session_data['user_id'])
    if not user:
        raise HTTPException(status_code=401, detail='User not found')

    return user


def _extract_session_token(websocket: WebSocket) -> str | None:
    """Extract session token from cookie or query parameter."""
    session_token = None

    if 'cookie' in websocket.headers:
        cookies = websocket.headers['cookie']
        for cookie in cookies.split(';'):
            if 'session_token=' in cookie:
                session_token = cookie.split('session_token=')[1].strip()
                break

    if not session_token and 'session_token' in websocket.query_params:
        session_token = websocket.query_params['session_token']

    return session_token


async def _authenticate_ws_user(
    websocket: WebSocket, db: AsyncSession, log_extra: dict
) -> object | None:
    """Authenticate a WebSocket connection and return the user, or close and return None."""
    session_token = _extract_session_token(websocket)

    if not session_token:
        logger.warning('WebSocket auth failed: No session token', extra=log_extra)
        await websocket.close(code=1008, reason='Not authenticated - no session token')
        return None

    session_data = await get_session(session_token)
    if not session_data:
        logger.warning('WebSocket auth failed: Invalid session', extra=log_extra)
        await websocket.close(code=1008, reason='Invalid or expired session')
        return None

    user_repo = get_user_repository(db)
    user_id = session_data['user_id']
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    user = await user_repo.get_user_by_id(user_id)
    if not user:
        logger.warning(
            'WebSocket auth failed: User not found',
            extra={**log_extra, 'user_id': str(user_id)},
        )
        await websocket.close(code=1008, reason='User not found')
        return None

    return user


async def _ws_heartbeat_loop(websocket: WebSocket, room_id: str, log_extra: dict) -> None:
    """Join a room, send confirmation, and run the heartbeat loop until disconnect."""
    if room_id not in manager.active_connections:
        manager.active_connections[room_id] = set()
    manager.active_connections[room_id].add(websocket)

    await manager.send_personal(websocket, {'type': 'connected', 'data': {'room': room_id}})

    try:
        while True:
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_text('pong')
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        logger.debug('WebSocket disconnected', extra=log_extra)


@router.websocket('/ws/groups/{group_id}')
async def websocket_group_endpoint(websocket: WebSocket, group_id: str) -> None:
    """WebSocket endpoint for group-level updates (new runs, run state changes)."""
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        log_extra = {'endpoint': 'group', 'group_id': group_id}
        logger.debug('WebSocket connection attempt', extra=log_extra)

        user = await _authenticate_ws_user(websocket, db, log_extra)
        if not user:
            return

        group_id_uuid = UUID(group_id)
        group_repo = get_group_repository(db)
        group = await group_repo.get_group_by_id(group_id_uuid)
        if not group:
            logger.warning('WebSocket auth failed: Group not found', extra=log_extra)
            await websocket.close(code=1008, reason='Group not found')
            return

        user_groups = await get_user_repository(db).get_user_groups(user)
        if not any(g.id == group_id_uuid for g in user_groups):
            logger.warning('WebSocket auth failed: Not a member', extra=log_extra)
            await websocket.close(code=1008, reason='Not a member of this group')
            return

        logger.info('WebSocket connected', extra={**log_extra, 'user_id': str(user.id)})
        await _ws_heartbeat_loop(websocket, f'group:{group_id}', log_extra)


@router.websocket('/ws/runs/{run_id}')
async def websocket_run_endpoint(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint for run-level updates (bids, ready status, state changes)."""
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        log_extra = {'endpoint': 'run', 'run_id': run_id}

        user = await _authenticate_ws_user(websocket, db, log_extra)
        if not user:
            return

        run_id_uuid = UUID(run_id)
        run_repo = get_run_repository(db)
        run = await run_repo.get_run_by_id(run_id_uuid)
        if not run:
            logger.warning('WebSocket auth failed: Run not found', extra=log_extra)
            await websocket.close(code=1008, reason='Run not found')
            return

        user_groups = await get_user_repository(db).get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            logger.warning('WebSocket auth failed: Not authorized', extra=log_extra)
            await websocket.close(code=1008, reason='Not authorized for this run')
            return

        logger.info('WebSocket connected', extra={**log_extra, 'user_id': str(user.id)})
        await _ws_heartbeat_loop(websocket, f'run:{run_id}', log_extra)


@router.websocket('/ws/user')
async def websocket_user_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for user-level updates (notifications)."""
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        log_extra = {'endpoint': 'user'}

        user = await _authenticate_ws_user(websocket, db, log_extra)
        if not user:
            return

        logger.info('WebSocket connected', extra={**log_extra, 'user_id': str(user.id)})
        await _ws_heartbeat_loop(websocket, f'user:{user.id}', log_extra)
