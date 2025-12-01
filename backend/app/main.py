import asyncio
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .api.middleware import RequestLoggingMiddleware
from .api.routes.admin import router as admin_router
from .api.routes.auth import router as auth_router
from .api.routes.distribution import router as distribution_router
from .api.routes.groups import router as groups_router
from .api.routes.notifications import router as notifications_router
from .api.routes.products import router as products_router
from .api.routes.reassignment import router as reassignment_router
from .api.routes.runs import router as runs_router
from .api.routes.search import router as search_router
from .api.routes.shopping import router as shopping_router
from .api.routes.stores import router as stores_router
from .api.routes.websocket import router as websocket_router
from .core.exceptions import AppException
from .errors.handlers import (
    app_exception_handler,
    generic_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from .infrastructure.config import ALLOWED_ORIGINS
from .infrastructure.database import create_tables
from .infrastructure.logging_config import setup_logging
from .utils.background_tasks import create_background_task

# Setup logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(level=log_level)

app = FastAPI(title='Bulq API', version='0.1.0')

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers with /api prefix to avoid conflicts with frontend routes
app.include_router(auth_router, prefix='/api')
app.include_router(groups_router, prefix='/api')
app.include_router(runs_router, prefix='/api')
app.include_router(stores_router, prefix='/api')
app.include_router(shopping_router, prefix='/api')
app.include_router(distribution_router, prefix='/api')
app.include_router(products_router, prefix='/api')
app.include_router(search_router, prefix='/api')
app.include_router(notifications_router, prefix='/api')
app.include_router(reassignment_router, prefix='/api')
app.include_router(admin_router, prefix='/api')
app.include_router(websocket_router, prefix='/api')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup_event():
    """Create database tables, seed data, and setup event handlers on startup."""
    await create_tables()

    # Register event handlers for domain events
    from .api.websocket_manager import manager
    from .events.domain_events import (
        BidPlacedEvent,
        BidRetractedEvent,
        MemberJoinedEvent,
        MemberLeftEvent,
        MemberRemovedEvent,
        ReadyToggledEvent,
        RunCancelledEvent,
        RunCreatedEvent,
        RunStateChangedEvent,
    )
    from .events.event_bus import event_bus
    from .events.handlers.notification_handler import NotificationEventHandler
    from .events.handlers.websocket_handler import WebSocketEventHandler
    from .repositories import get_notification_repository

    # Create event handlers
    ws_handler = WebSocketEventHandler(manager)

    # Subscribe WebSocket handler to events
    event_bus.subscribe(BidPlacedEvent, ws_handler.handle_bid_placed)
    event_bus.subscribe(BidRetractedEvent, ws_handler.handle_bid_retracted)
    event_bus.subscribe(ReadyToggledEvent, ws_handler.handle_ready_toggled)
    event_bus.subscribe(RunStateChangedEvent, ws_handler.handle_run_state_changed)
    event_bus.subscribe(RunCreatedEvent, ws_handler.handle_run_created)
    event_bus.subscribe(RunCancelledEvent, ws_handler.handle_run_cancelled)
    event_bus.subscribe(MemberJoinedEvent, ws_handler.handle_member_joined)
    event_bus.subscribe(MemberRemovedEvent, ws_handler.handle_member_removed)
    event_bus.subscribe(MemberLeftEvent, ws_handler.handle_member_left)

    # Note: NotificationEventHandler needs repository which is per-request
    # We'll create a handler factory that gets repo from database session
    # For now, we subscribe a lambda that creates handler on-demand
    async def handle_run_state_changed_notification(event: RunStateChangedEvent):
        """Handle run state changed event for notifications."""
        from .infrastructure.database import SessionLocal

        async with SessionLocal() as db:
            try:
                notification_repo = get_notification_repository(db)
                notification_handler = NotificationEventHandler(notification_repo)
                await notification_handler.handle_run_state_changed(event)
                await db.commit()
            except Exception:
                await db.rollback()
            finally:
                db.close()
                raise

    event_bus.subscribe(RunStateChangedEvent, handle_run_state_changed_notification)

    from .infrastructure.request_context import get_logger

    logger = get_logger(__name__)
    logger.info('✅ Event handlers registered successfully')

    # Initialize default settings
    from .infrastructure.database import SessionLocal
    from .infrastructure.runtime_settings import initialize_default_settings

    try:
        async with SessionLocal() as db:
            # Use run_sync to run synchronous code with async session
            await initialize_default_settings(db)
        logger.info('⚙️  Default settings initialized')
    except Exception as e:
        logger.error(f'Failed to initialize default settings: {e}', exc_info=True)

    # Create seed data if in development
    import os

    if os.getenv('ENV') == 'development':
        try:
            from .infrastructure.config import REPO_MODE
            from .scripts.seed_data import create_seed_data

            if REPO_MODE == 'memory':
                # Memory mode: pass None as db_session
                create_seed_data(None)
                logger.info('🌱 Seed data created (memory mode)')
            else:
                # Database mode: pass db session
                from .infrastructure.database import SessionLocal

                db = SessionLocal()
                try:
                    create_seed_data(db)
                    db.commit()
                    logger.info('🌱 Seed data created (database mode)')
                finally:
                    db.close()
        except ImportError as e:
            logger.warning(f'Could not import seed data: {e}. Skipping seed data creation.')
            raise
        except Exception as e:
            logger.error(f'Failed to create seed data: {e}', exc_info=True)
            raise

    # Start background task for session cleanup
    from .infrastructure.auth import cleanup_expired_sessions
    from .infrastructure.database import log_pool_status

    async def session_cleanup_loop():
        """Periodically clean up expired sessions to prevent memory leak."""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            cleanup_expired_sessions()

    async def pool_monitoring_loop():
        """Periodically log connection pool statistics."""
        while True:
            await asyncio.sleep(300)  # Log every 5 minutes
            log_pool_status()

    create_background_task(session_cleanup_loop(), task_name='session_cleanup_loop')
    create_background_task(pool_monitoring_loop(), task_name='pool_monitoring_loop')


@app.get('/')
async def hello_world():
    """Root endpoint returning welcome message."""
    return {'message': 'Hello World from Bulq Backend!'}


@app.get('/health')
async def health_check():
    """Health check endpoint for monitoring."""
    return {'status': 'healthy'}


@app.get('/db-health')
async def db_health_check():
    """Check database connectivity and connection pool status."""
    try:
        from sqlalchemy import text

        from .infrastructure.database import engine, get_pool_status

        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))

        pool_status = get_pool_status()
        return {
            'status': 'healthy',
            'database': 'connected',
            'pool': pool_status,
        }
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}
