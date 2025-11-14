"""Transaction management utilities for ensuring data consistency.

This module provides utilities for wrapping multi-step database operations
in transactions to ensure atomicity and prevent partial state changes.
"""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any

from sqlalchemy.orm import Session

from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


@contextmanager
def transaction(
    db: Session, description: str = 'database operation'
) -> Generator[None, None, None]:
    """Context manager for explicit transaction management.

    Wraps a block of code in a database transaction. Commits on success,
    rolls back on any exception.

    Usage:
        with transaction(db, "remove group member"):
            # Multiple database operations
            repo.update_user(...)
            repo.delete_participation(...)
            # All committed together or all rolled back

    Args:
        db: SQLAlchemy database session
        description: Description of the operation for logging

    Yields:
        None

    Raises:
        Any exception raised within the context block
    """
    try:
        logger.debug(f'Starting transaction: {description}')
        yield
        db.commit()
        logger.debug(f'Transaction committed: {description}')
    except Exception as e:
        db.rollback()
        logger.error(
            'Transaction rolled back due to error',
            extra={'description': description, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise


def transactional(description: str | None = None) -> Callable:
    """Decorator to wrap a service method in a transaction.

    The decorated method must have 'self' with a 'db' attribute that is a SQLAlchemy session.
    This decorator ensures that all database operations within the method are atomic.

    Usage:
        class MyService(BaseService):
            @transactional("update user profile")
            def update_profile(self, user_id: str, data: dict):
                # Multiple repository calls
                self.repo.update_user(...)
                self.repo.create_notification(...)
                # All committed together or all rolled back

    Args:
        description: Optional description of the operation for logging.
                    If None, uses the function name.

    Returns:
        Decorated function that wraps the original in a transaction
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Get the database session from self.db
            if not hasattr(self, 'db'):
                raise AttributeError(
                    f'{self.__class__.__name__} must have a "db" attribute (SQLAlchemy Session) '
                    f'to use @transactional decorator'
                )

            db: Session = self.db
            op_description = description or f'{self.__class__.__name__}.{func.__name__}'

            with transaction(db, op_description):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def savepoint(db: Session, name: str = 'savepoint') -> Generator[None, None, None]:
    """Context manager for nested transactions using SAVEPOINTs.

    Use this for operations that need sub-transaction semantics within
    a larger transaction.

    Usage:
        with transaction(db, "outer operation"):
            # Do some work
            with savepoint(db, "inner operation"):
                # This can be rolled back independently
                repo.update_something(...)

    Args:
        db: SQLAlchemy database session
        name: Name of the savepoint for identification

    Yields:
        None

    Raises:
        Any exception raised within the context block
    """
    try:
        logger.debug(f'Creating savepoint: {name}')
        sp = db.begin_nested()
        yield
        sp.commit()
        logger.debug(f'Savepoint committed: {name}')
    except Exception as e:
        sp.rollback()
        logger.warning(
            'Savepoint rolled back',
            extra={'savepoint': name, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise


def ensure_transaction_active(db: Session) -> bool:
    """Check if a transaction is currently active on the session.

    Args:
        db: SQLAlchemy database session

    Returns:
        True if transaction is active, False otherwise
    """
    return db.in_transaction()


def flush_and_check(db: Session, description: str = 'operation') -> None:
    """Flush changes to database and log any errors without committing.

    Useful for intermediate validation of changes before committing the full transaction.

    Args:
        db: SQLAlchemy database session
        description: Description for logging

    Raises:
        Any database integrity error
    """
    try:
        logger.debug(f'Flushing changes: {description}')
        db.flush()
    except Exception as e:
        logger.error(
            'Flush failed',
            extra={'description': description, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise
