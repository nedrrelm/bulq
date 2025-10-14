import os
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.models import Base
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL environment variable must be set! See .env.example for configuration.'
    )

# Connection pool configuration
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,  # Number of connections to maintain
    max_overflow=MAX_OVERFLOW,  # Extra connections if pool exhausted
    pool_timeout=POOL_TIMEOUT,  # Seconds to wait for connection
    pool_recycle=POOL_RECYCLE,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Connection pool event listeners for monitoring
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    """Log when a new connection is created."""
    pool = engine.pool
    logger.debug(
        'New database connection created',
        extra={
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
        },
    )


@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    pool = engine.pool
    checked_out = pool.checkedout()
    overflow = pool.overflow()
    total_connections = pool.size() + overflow

    # Log statistics
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

    # Warn if pool is running low
    if checked_out >= pool.size() * 0.8:  # 80% utilization
        logger.warning(
            'Database connection pool is running low',
            extra={
                'checked_out': checked_out,
                'pool_size': pool.size(),
                'overflow': overflow,
                'utilization_pct': (checked_out / total_connections) * 100,
            },
        )

    # Alert if pool is exhausted
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


@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    pool = engine.pool
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
    pool = engine.pool
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


def create_tables() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
