"""Utilities for managing background tasks with proper error handling."""

import asyncio
from typing import Coroutine, Any
from .request_context import get_logger

logger = get_logger(__name__)


def create_background_task(coro: Coroutine[Any, Any, Any], task_name: str = "background_task") -> asyncio.Task:
    """
    Create a background task with proper error handling and logging.

    This wrapper ensures that exceptions in background tasks are logged
    and don't fail silently.

    Args:
        coro: The coroutine to run as a background task
        task_name: Name for the task (used in logging)

    Returns:
        The created asyncio Task
    """
    task = asyncio.create_task(_wrap_task_with_error_handling(coro, task_name))
    return task


async def _wrap_task_with_error_handling(coro: Coroutine[Any, Any, Any], task_name: str) -> Any:
    """
    Wrapper that catches and logs exceptions from background tasks.

    Args:
        coro: The coroutine to execute
        task_name: Name for the task (used in logging)

    Returns:
        The result of the coroutine if successful
    """
    try:
        return await coro
    except asyncio.CancelledError:
        logger.warning(
            "Background task cancelled",
            extra={"task_name": task_name}
        )
        raise
    except Exception as e:
        logger.error(
            "Background task failed with exception",
            extra={
                "task_name": task_name,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        # Don't re-raise - this is a background task
        return None
