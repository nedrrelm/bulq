from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import asyncio
from .database import create_tables
from .background_tasks import create_background_task
from .routes.auth import router as auth_router
from .routes.groups import router as groups_router
from .routes.runs import router as runs_router
from .routes.stores import router as stores_router
from .routes.shopping import router as shopping_router
from .routes.distribution import router as distribution_router
from .routes.products import router as products_router
from .routes.websocket import router as websocket_router
from .routes.search import router as search_router
from .routes.notifications import router as notifications_router
from .routes.reassignment import router as reassignment_router
from .routes.admin import router as admin_router
from .exceptions import AppException
from .error_handlers import (
    app_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
)
from .logging_config import setup_logging
from .middleware import RequestLoggingMiddleware
import os

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level)

app = FastAPI(title="Bulq API", version="0.1.0")

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
from .config import ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Create database tables and seed data on startup."""
    create_tables()

    # Create seed data if in development
    import os
    if os.getenv("ENV") == "development":
        try:
            from .scripts.seed_data import create_seed_data
            create_seed_data()
        except ImportError:
            print("Warning: Could not import seed data. Skipping seed data creation.")

    # Start background task for session cleanup
    from .auth import cleanup_expired_sessions
    async def session_cleanup_loop():
        """Periodically clean up expired sessions to prevent memory leak."""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            cleanup_expired_sessions()

    create_background_task(session_cleanup_loop(), task_name="session_cleanup_loop")

@app.get("/")
async def hello_world():
    return {"message": "Hello World from Bulq Backend!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health_check():
    """Check database connectivity."""
    try:
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
