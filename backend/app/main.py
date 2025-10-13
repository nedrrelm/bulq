import asyncio
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .background_tasks import create_background_task
from .config import ALLOWED_ORIGINS
from .database import create_tables
from .error_handlers import (
    app_exception_handler,
    generic_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from .exceptions import AppException
from .logging_config import setup_logging
from .middleware import RequestLoggingMiddleware
from .routes.admin import router as admin_router
from .routes.auth import router as auth_router
from .routes.distribution import router as distribution_router
from .routes.groups import router as groups_router
from .routes.notifications import router as notifications_router
from .routes.products import router as products_router
from .routes.reassignment import router as reassignment_router
from .routes.runs import router as runs_router
from .routes.search import router as search_router
from .routes.shopping import router as shopping_router
from .routes.stores import router as stores_router
from .routes.websocket import router as websocket_router

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

# Include routers
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(runs_router)
app.include_router(stores_router)
app.include_router(shopping_router)
app.include_router(distribution_router)
app.include_router(products_router)
app.include_router(search_router)
app.include_router(notifications_router)
app.include_router(reassignment_router)
app.include_router(admin_router)
app.include_router(websocket_router)

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
    create_tables()

    # Register event handlers for domain events
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
    from .repository import get_repository
    from .websocket_manager import manager

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
        from .database import SessionLocal
        db = SessionLocal()
        try:
            repo = get_repository(db)
            notification_handler = NotificationEventHandler(repo)
            await notification_handler.handle_run_state_changed(event)
            db.commit()
        finally:
            db.close()

    event_bus.subscribe(RunStateChangedEvent, handle_run_state_changed_notification)

    from .request_context import get_logger
    logger = get_logger(__name__)
    logger.info('Event handlers registered successfully')

    # Create seed data if in development
    import os

    if os.getenv('ENV') == 'development':
        try:
            from .scripts.seed_data import create_seed_data

            create_seed_data()
        except ImportError:
            print('Warning: Could not import seed data. Skipping seed data creation.')

    # Start background task for session cleanup
    from .auth import cleanup_expired_sessions
    from .database import log_pool_status

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

        from .database import engine, get_pool_status

        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))

        pool_status = get_pool_status()
        return {
            'status': 'healthy',
            'database': 'connected',
            'pool': pool_status,
        }
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}
