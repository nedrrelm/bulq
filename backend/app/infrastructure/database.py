import os
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.models import Base
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL environment variable must be set! See .env.example for configuration.'
    )

# Convert DATABASE_URL to async driver if needed
# postgresql:// -> postgresql+asyncpg://
# postgres:// -> postgresql+asyncpg://
if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1).replace(
        'postgres://', 'postgresql+asyncpg://', 1
    )

# Connection pool configuration
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))


engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,  # Number of connections to maintain
    max_overflow=MAX_OVERFLOW,  # Extra connections if pool exhausted
    pool_timeout=POOL_TIMEOUT,  # Seconds to wait for connection
    pool_recycle=POOL_RECYCLE,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
    echo=False,  # Set to True for SQL query logging
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# Connection pool event listeners for monitoring
# Note: Async engines use sync event listeners, but pool access is different
@event.listens_for(engine.sync_engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    """Log when a new connection is created."""
    pool = engine.pool
    logger.debug(
        'New database connection created',
        extra=get_pool_status(pool),
    )


@event.listens_for(engine.sync_engine, 'checkout')
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    pool = engine.pool
    # Log statistics
    logger.debug(
        'Connection checked out from pool',
        extra=get_pool_status(),
    )

    # Warn if pool is running low
    pool_size = pool.size() if hasattr(pool, 'size') else 0
    checked_out = pool.checkedout() if hasattr(pool, 'checkedout') else 0
    if pool_size > 0 and checked_out >= pool_size * 0.8:  # 80% utilization
        logger.warning(
            'Database connection pool is running low',
            extra=get_pool_status(),
        )

    # Alert if pool is exhausted
    overflow = pool.overflow() if hasattr(pool, 'overflow') else 0
    if overflow >= MAX_OVERFLOW:
        logger.error(
            'Database connection pool exhausted - using maximum overflow',
            extra=get_pool_status(),
        )


@event.listens_for(engine.sync_engine, 'checkin')
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    logger.debug(
        'Connection returned to pool',
        extra=get_pool_status(),
    )


def get_pool_status() -> dict:
    """Get current connection pool statistics.

    Returns:
        Dict containing pool size, checked out connections, overflow, etc.
    """
    pool = engine.pool
    pool_size = pool.size() if hasattr(pool, 'size') else 0
    checked_out = pool.checkedout() if hasattr(pool, 'checkedout') else 0
    checked_in = pool.checkedin() if hasattr(pool, 'checkedin') else 0
    overflow = pool.overflow() if hasattr(pool, 'overflow') else 0
    total_connections = pool_size + overflow

    return {
        'pool_size': pool_size,
        'max_overflow': MAX_OVERFLOW,
        'checked_out': checked_out,
        'checked_in': checked_in,
        'overflow': overflow,
        'total_connections': total_connections,
        'available': pool_size - checked_out + (MAX_OVERFLOW - overflow),
        'utilization_pct': (checked_out / total_connections * 100) if total_connections > 0 else 0,
    }


def log_pool_status() -> None:
    """Log current connection pool status."""
    status = get_pool_status()
    logger.info('Database connection pool status', extra=status)


async def create_tables() -> None:
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
