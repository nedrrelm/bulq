"""Event bus implementation for domain events."""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from ..background_tasks import create_background_task
from ..request_context import get_logger
from .domain_events import DomainEvent

logger = get_logger(__name__)


class EventBus:
    """Simple in-memory event bus for domain events.

    The event bus allows decoupling of business logic from side effects like
    WebSocket broadcasting and notifications. Services emit domain events,
    and registered handlers react to those events asynchronously.
    """

    def __init__(self) -> None:
        """Initialize event bus with empty handler registry."""
        self._handlers: dict[type[DomainEvent], list[Callable[[Any], Awaitable[None]]]] = (
            defaultdict(list)
        )

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], Awaitable[None]]
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: Async function that handles the event
        """
        self._handlers[event_type].append(handler)
        logger.debug(
            'Handler subscribed to event',
            extra={'event_type': event_type.__name__, 'handler': handler.__name__},
        )

    def emit(self, event: DomainEvent) -> None:
        """Emit a domain event to all subscribed handlers.

        Handlers are executed asynchronously as background tasks.
        Failures in handlers are logged but do not affect the caller.

        Args:
            event: The domain event to emit
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        logger.debug(
            'Emitting domain event',
            extra={'event_type': event_type.__name__, 'handler_count': len(handlers)},
        )

        for handler in handlers:
            # Fire and forget - handlers run async
            create_background_task(
                handler(event), task_name=f'{handler.__name__}_{event_type.__name__}'
            )

    def clear_handlers(self) -> None:
        """Clear all registered handlers.

        Useful for testing to ensure clean state between tests.
        """
        self._handlers.clear()
        logger.debug('All event handlers cleared')


# Global event bus instance
event_bus = EventBus()
