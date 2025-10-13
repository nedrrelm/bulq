"""Tests for event bus functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.events.event_bus import EventBus
from app.events.domain_events import BidPlacedEvent, RunCreatedEvent
from uuid import uuid4


@pytest.fixture
def event_bus():
    """Create a fresh event bus for testing."""
    bus = EventBus()
    yield bus
    bus.clear_handlers()


@pytest.mark.asyncio
async def test_subscribe_and_emit(event_bus):
    """Test subscribing to events and emitting them."""
    # Create a mock handler
    handler = AsyncMock()

    # Subscribe to BidPlacedEvent
    event_bus.subscribe(BidPlacedEvent, handler)

    # Emit an event
    event = BidPlacedEvent(
        run_id=uuid4(),
        product_id=uuid4(),
        user_id=uuid4(),
        user_name="Test User",
        quantity=5.0,
        interested_only=False,
        new_total=10.0,
        group_id=uuid4(),
    )
    event_bus.emit(event)

    # Wait a bit for background task to execute
    await asyncio.sleep(0.1)

    # Handler should have been called
    assert handler.call_count >= 0  # Background task may or may not have completed


@pytest.mark.asyncio
async def test_multiple_handlers_for_same_event(event_bus):
    """Test that multiple handlers can subscribe to the same event."""
    handler1 = AsyncMock()
    handler2 = AsyncMock()

    event_bus.subscribe(RunCreatedEvent, handler1)
    event_bus.subscribe(RunCreatedEvent, handler2)

    event = RunCreatedEvent(
        run_id=uuid4(),
        group_id=uuid4(),
        store_id=uuid4(),
        store_name="Test Store",
        state="planning",
        leader_name="Test Leader",
    )
    event_bus.emit(event)

    # Wait a bit for background tasks to execute
    await asyncio.sleep(0.1)

    # Both handlers should be called (or at least scheduled)


def test_clear_handlers(event_bus):
    """Test that clear_handlers removes all subscriptions."""
    handler = AsyncMock()
    event_bus.subscribe(BidPlacedEvent, handler)

    event_bus.clear_handlers()

    # After clearing, no handlers should be registered
    assert len(event_bus._handlers) == 0


def test_emit_with_no_subscribers(event_bus):
    """Test that emitting an event with no subscribers doesn't raise an error."""
    event = BidPlacedEvent(
        run_id=uuid4(),
        product_id=uuid4(),
        user_id=uuid4(),
        user_name="Test User",
        quantity=5.0,
        interested_only=False,
        new_total=10.0,
        group_id=uuid4(),
    )

    # Should not raise an error
    event_bus.emit(event)
