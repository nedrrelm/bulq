"""Transaction management utilities for ensuring data consistency.

This module provides utilities for wrapping multi-step database operations
in transactions to ensure atomicity and prevent partial state changes.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def transaction(
    db: AsyncSession, description: str = 'database operation'
) -> AsyncGenerator[None, None]:
    """Context manager for explicit transaction management.

    Wraps a block of code in a database transaction. Commits on success,
    rolls back on any exception.

    Usage:
        async with transaction(db, "remove group member"):
            # Multiple database operations
            await user_repo.update_user(...)
            await run_repo.delete_participation(...)
            # All committed together or all rolled back

    Args:
        db: SQLAlchemy async database session
        description: Description of the operation for logging

    Yields:
        None

    Raises:
        Any exception raised within the context block
    """
    try:
        logger.debug(f'Starting transaction: {description}')
        yield
        await db.commit()
        logger.debug(f'Transaction committed: {description}')
    except Exception as e:
        await db.rollback()
        logger.error(
            'Transaction rolled back due to error',
            extra={'description': description, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise


def transactional(description: str | None = None) -> Callable:
    """Decorator to wrap a service method in a transaction.

    The decorated method must have 'self' with a 'db' attribute that is an AsyncSession.
    This decorator ensures that all database operations within the method are atomic.

    Usage:
        class MyService(BaseService):
            @transactional("update user profile")
            async def update_profile(self, user_id: str, data: dict):
                # Multiple repository calls
                await self.user_repo.update_user(...)
                await self.notification_repo.create_notification(...)
                # All committed together or all rolled back

    Args:
        description: Optional description of the operation for logging.
                    If None, uses the function name.

    Returns:
        Decorated function that wraps the original in a transaction
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Get the database session from self.db
            if not hasattr(self, 'db'):
                raise AttributeError(
                    f'{self.__class__.__name__} must have a "db" attribute (AsyncSession) '
                    f'to use @transactional decorator'
                )

            db: AsyncSession = self.db
            op_description = description or f'{self.__class__.__name__}.{func.__name__}'

            async with transaction(db, op_description):
                return await func(self, *args, **kwargs)

        return wrapper

    return decorator


@asynccontextmanager
async def savepoint(db: AsyncSession, name: str = 'savepoint') -> AsyncGenerator[None, None]:
    """Context manager for nested transactions using SAVEPOINTs.

    Use this for operations that need sub-transaction semantics within
    a larger transaction.

    Usage:
        async with transaction(db, "outer operation"):
            # Do some work
            async with savepoint(db, "inner operation"):
                # This can be rolled back independently
                await repo.update_something(...)

    Args:
        db: SQLAlchemy async database session
        name: Name of the savepoint for identification

    Yields:
        None

    Raises:
        Any exception raised within the context block
    """
    try:
        logger.debug(f'Creating savepoint: {name}')
        sp = await db.begin_nested()
        yield
        await sp.commit()
        logger.debug(f'Savepoint committed: {name}')
    except Exception as e:
        await sp.rollback()
        logger.warning(
            'Savepoint rolled back',
            extra={'savepoint': name, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise


def ensure_transaction_active(db: AsyncSession) -> bool:
    """Check if a transaction is currently active on the session.

    Args:
        db: SQLAlchemy async database session

    Returns:
        True if transaction is active, False otherwise
    """
    return db.in_transaction()


async def flush_and_check(db: AsyncSession, description: str = 'operation') -> None:
    """Flush changes to database and log any errors without committing.

    Useful for intermediate validation of changes before committing the full transaction.

    Args:
        db: SQLAlchemy async database session
        description: Description for logging

    Raises:
        Any database integrity error
    """
    try:
        logger.debug(f'Flushing changes: {description}')
        await db.flush()
    except Exception as e:
        logger.error(
            'Flush failed',
            extra={'description': description, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise
