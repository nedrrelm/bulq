import os
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.models import Base
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL environment variable must be set! See .env.example for configuration.'
    )

if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

# Connection pool configuration
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False
)


@event.listens_for(async_engine.sync_engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    """Log when a new connection is created."""
    pool = async_engine.pool
    logger.debug(
        'New database connection created',
        extra={
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
        },
    )


@event.listens_for(async_engine.sync_engine, 'checkout')
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    pool = async_engine.pool
    checked_out = pool.checkedout()
    overflow = pool.overflow()
    total_connections = pool.size() + overflow

    logger.debug(
        'Connection checked out from pool',
        extra={
            'checked_out': checked_out,
            'checked_in': pool.checkedin(),
            'overflow': overflow,
            'pool_size': pool.size(),
            'total_connections': total_connections,
        },
    )

    if checked_out >= pool.size() * 0.8:
        logger.warning(
            'Database connection pool is running low',
            extra={
                'checked_out': checked_out,
                'pool_size': pool.size(),
                'overflow': overflow,
                'utilization_pct': (checked_out / total_connections) * 100,
            },
        )

    if overflow >= MAX_OVERFLOW:
        logger.error(
            'Database connection pool exhausted - using maximum overflow',
            extra={
                'pool_size': pool.size(),
                'max_overflow': MAX_OVERFLOW,
                'overflow': overflow,
                'checked_out': checked_out,
            },
        )


@event.listens_for(async_engine.sync_engine, 'checkin')
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    pool = async_engine.pool
    logger.debug(
        'Connection returned to pool',
        extra={
            'checked_out': pool.checkedout(),
            'checked_in': pool.checkedin(),
            'overflow': pool.overflow(),
        },
    )


def get_pool_status() -> dict:
    """Get current connection pool statistics.

    Returns:
        Dict containing pool size, checked out connections, overflow, etc.
    """
    pool = async_engine.pool
    pool_size = pool.size()
    checked_out = pool.checkedout()
    checked_in = pool.checkedin()
    overflow = pool.overflow()
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
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session
