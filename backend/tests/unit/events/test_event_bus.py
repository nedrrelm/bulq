"""Unit tests for EventBus implementation.

Tests cover:
- Subscription management (subscribe, multiple handlers, different event types)
- Event emission (handlers called with correct data, async execution)
- Handler execution (background tasks, exception handling, fire-and-forget)
- Clear handlers functionality
- Edge cases (invalid types, large handler count, global instance)
"""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from app.events.domain_events import BidPlacedEvent, DomainEvent
from app.events.event_bus import EventBus, event_bus


@dataclass
class CustomTestEvent(DomainEvent):
    """Custom test event for testing."""

    test_id: str
    test_value: int


@dataclass
class AnotherTestEvent(DomainEvent):
    """Another test event for testing separation."""

    data: str


class TestSubscription:
    """Test EventBus.subscribe() method."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        return EventBus()

    @pytest.fixture
    def mock_handler(self):
        """Create a mock async handler."""
        handler = AsyncMock()
        handler.__name__ = 'mock_handler'
        return handler

    def test_subscribe_registers_handler_for_event_type(self, bus, mock_handler):
        """Test that subscribe() registers a handler for an event type."""
        bus.subscribe(CustomTestEvent, mock_handler)

        assert CustomTestEvent in bus._handlers
        assert mock_handler in bus._handlers[CustomTestEvent]

    def test_multiple_handlers_for_same_event_type(self, bus):
        """Test that multiple handlers can be subscribed to same event type."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'
        handler3 = AsyncMock()
        handler3.__name__ = 'handler3'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(CustomTestEvent, handler2)
        bus.subscribe(CustomTestEvent, handler3)

        assert len(bus._handlers[CustomTestEvent]) == 3
        assert handler1 in bus._handlers[CustomTestEvent]
        assert handler2 in bus._handlers[CustomTestEvent]
        assert handler3 in bus._handlers[CustomTestEvent]

    def test_handlers_for_different_event_types_are_separate(self, bus, mock_handler):
        """Test that handlers for different event types are kept separate."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(AnotherTestEvent, handler2)

        assert len(bus._handlers[CustomTestEvent]) == 1
        assert len(bus._handlers[AnotherTestEvent]) == 1
        assert handler1 in bus._handlers[CustomTestEvent]
        assert handler1 not in bus._handlers[AnotherTestEvent]
        assert handler2 in bus._handlers[AnotherTestEvent]
        assert handler2 not in bus._handlers[CustomTestEvent]

    def test_handler_list_grows_with_each_subscription(self, bus):
        """Test that handler list grows with each subscription."""
        handlers = [AsyncMock() for _ in range(5)]
        for i, handler in enumerate(handlers):
            handler.__name__ = f'handler_{i}'

        for i, handler in enumerate(handlers):
            bus.subscribe(CustomTestEvent, handler)
            assert len(bus._handlers[CustomTestEvent]) == i + 1

    def test_subscribing_same_handler_twice_adds_it_twice(self, bus, mock_handler):
        """Test that subscribing same handler twice adds it to list twice."""
        bus.subscribe(CustomTestEvent, mock_handler)
        bus.subscribe(CustomTestEvent, mock_handler)

        assert len(bus._handlers[CustomTestEvent]) == 2
        assert bus._handlers[CustomTestEvent].count(mock_handler) == 2

    def test_subscribe_initializes_empty_list_for_new_event_type(self, bus, mock_handler):
        """Test that subscribing to new event type initializes handler list."""
        bus.subscribe(CustomTestEvent, mock_handler)

        assert CustomTestEvent in bus._handlers
        assert isinstance(bus._handlers[CustomTestEvent], list)


class TestEmission:
    """Test EventBus.emit() method."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_emit_calls_subscribed_handlers(self, bus):
        """Test that emit() calls subscribed handlers."""
        handler_called = asyncio.Event()
        handler = AsyncMock(side_effect=lambda e: handler_called.set())
        handler.__name__ = 'test_handler'

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.subscribe(CustomTestEvent, handler)
            event = CustomTestEvent(test_id='123', test_value=42)
            bus.emit(event)

            # Verify create_background_task was called
            assert mock_create_task.call_count == 1

    @pytest.mark.asyncio
    async def test_handlers_receive_correct_event_data(self, bus):
        """Test that handlers receive correct event data."""
        received_events = []

        async def capture_handler(event):
            received_events.append(event)

        capture_handler.__name__ = 'capture_handler'

        bus.subscribe(CustomTestEvent, capture_handler)
        event = CustomTestEvent(test_id='test-123', test_value=99)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            # Simulate immediate execution for testing
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(event)
            await asyncio.sleep(0.01)  # Give task time to execute

        assert len(received_events) == 1
        assert received_events[0] == event
        assert received_events[0].test_id == 'test-123'
        assert received_events[0].test_value == 99

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called_for_same_event(self, bus):
        """Test that all handlers are called when event is emitted."""
        call_counts = {'h1': 0, 'h2': 0, 'h3': 0}

        async def handler1(event):
            call_counts['h1'] += 1

        async def handler2(event):
            call_counts['h2'] += 1

        async def handler3(event):
            call_counts['h3'] += 1

        handler1.__name__ = 'handler1'
        handler2.__name__ = 'handler2'
        handler3.__name__ = 'handler3'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(CustomTestEvent, handler2)
        bus.subscribe(CustomTestEvent, handler3)

        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            # Simulate immediate execution
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(event)
            await asyncio.sleep(0.01)

        assert call_counts['h1'] == 1
        assert call_counts['h2'] == 1
        assert call_counts['h3'] == 1

    def test_handlers_for_different_event_types_not_called(self, bus):
        """Test that handlers for different event types aren't called."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(AnotherTestEvent, handler2)

        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            # Only handler1 should be scheduled
            assert mock_create_task.call_count == 1

    def test_emitting_event_with_no_handlers_does_not_crash(self, bus):
        """Test that emitting event with no handlers doesn't crash."""
        event = CustomTestEvent(test_id='123', test_value=42)

        # Should not raise any exception
        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            # No handlers, so create_background_task shouldn't be called
            assert mock_create_task.call_count == 0

    @pytest.mark.asyncio
    async def test_async_handlers_are_executed(self, bus):
        """Test that async handlers are properly executed."""
        execution_flag = {'executed': False}

        async def async_handler(event):
            await asyncio.sleep(0.001)
            execution_flag['executed'] = True

        async_handler.__name__ = 'async_handler'

        bus.subscribe(CustomTestEvent, async_handler)
        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            # Simulate immediate execution
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(event)
            await asyncio.sleep(0.01)

        assert execution_flag['executed'] is True

    def test_handler_execution_is_fire_and_forget(self, bus):
        """Test that handler execution doesn't block emit() call."""
        handler = AsyncMock()
        handler.__name__ = 'blocking_handler'

        bus.subscribe(CustomTestEvent, handler)
        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            # emit() should return immediately without waiting for handler
            bus.emit(event)

            # Just verify it was scheduled, not executed
            assert mock_create_task.call_count == 1


class TestHandlerExecution:
    """Test handler execution details."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        return EventBus()

    def test_handlers_run_as_background_tasks(self, bus):
        """Test that handlers are executed as background tasks."""
        handler = AsyncMock()
        handler.__name__ = 'test_handler'

        bus.subscribe(CustomTestEvent, handler)
        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            # Verify create_background_task was called with correct arguments
            assert mock_create_task.call_count == 1
            call_args = mock_create_task.call_args
            assert 'task_name' in call_args.kwargs
            assert call_args.kwargs['task_name'] == 'test_handler_CustomTestEvent'

    @pytest.mark.asyncio
    async def test_handler_exceptions_dont_crash_emitter(self, bus):
        """Test that handler exceptions are caught and logged."""

        async def failing_handler(event):
            raise ValueError('Handler failed intentionally')

        failing_handler.__name__ = 'failing_handler'

        bus.subscribe(CustomTestEvent, failing_handler)
        event = CustomTestEvent(test_id='123', test_value=42)

        # Should not raise exception
        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            # Use real create_background_task to test error handling
            from app.utils.background_tasks import create_background_task

            mock_create_task.side_effect = create_background_task

            bus.emit(event)
            await asyncio.sleep(0.01)  # Let handler execute and fail

            # Test passes if no exception is raised

    @pytest.mark.asyncio
    async def test_multiple_events_emitted_in_sequence(self, bus):
        """Test that multiple events can be emitted in sequence."""
        received_events = []

        async def tracking_handler(event):
            received_events.append(event)

        tracking_handler.__name__ = 'tracking_handler'

        bus.subscribe(CustomTestEvent, tracking_handler)

        events = [
            CustomTestEvent(test_id='1', test_value=10),
            CustomTestEvent(test_id='2', test_value=20),
            CustomTestEvent(test_id='3', test_value=30),
        ]

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            for event in events:
                bus.emit(event)

            await asyncio.sleep(0.01)

        assert len(received_events) == 3
        assert received_events[0].test_id == '1'
        assert received_events[1].test_id == '2'
        assert received_events[2].test_id == '3'

    @pytest.mark.asyncio
    async def test_handler_receives_full_event_object_with_all_fields(self, bus):
        """Test that handler receives complete event object."""
        received_event = None

        async def inspector_handler(event):
            nonlocal received_event
            received_event = event

        inspector_handler.__name__ = 'inspector_handler'

        bus.subscribe(CustomTestEvent, inspector_handler)
        original_event = CustomTestEvent(test_id='full-test', test_value=999)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(original_event)
            await asyncio.sleep(0.01)

        assert received_event is not None
        assert received_event.test_id == 'full-test'
        assert received_event.test_value == 999
        assert isinstance(received_event, CustomTestEvent)
        assert isinstance(received_event, DomainEvent)


class TestClearHandlers:
    """Test EventBus.clear_handlers() method."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        return EventBus()

    def test_clear_handlers_removes_all_handlers(self, bus):
        """Test that clear_handlers() removes all registered handlers."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(AnotherTestEvent, handler2)

        assert len(bus._handlers) == 2

        bus.clear_handlers()

        assert len(bus._handlers) == 0

    def test_events_dont_trigger_handlers_after_clearing(self, bus):
        """Test that events don't trigger handlers after clearing."""
        handler = AsyncMock()
        handler.__name__ = 'handler'

        bus.subscribe(CustomTestEvent, handler)
        bus.clear_handlers()

        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            # No handlers should be called
            assert mock_create_task.call_count == 0

    def test_can_resubscribe_after_clearing(self, bus):
        """Test that handlers can be re-subscribed after clearing."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'

        bus.subscribe(CustomTestEvent, handler1)
        bus.clear_handlers()
        bus.subscribe(CustomTestEvent, handler2)

        assert len(bus._handlers[CustomTestEvent]) == 1
        assert handler2 in bus._handlers[CustomTestEvent]
        assert handler1 not in bus._handlers[CustomTestEvent]

    def test_clearing_when_no_handlers_exist(self, bus):
        """Test that clearing when no handlers exist doesn't crash."""
        # Should not raise any exception
        bus.clear_handlers()

        assert len(bus._handlers) == 0

    def test_clear_handlers_multiple_times(self, bus):
        """Test that clear_handlers() can be called multiple times."""
        handler = AsyncMock()
        handler.__name__ = 'handler'

        bus.subscribe(CustomTestEvent, handler)
        bus.clear_handlers()
        bus.clear_handlers()
        bus.clear_handlers()

        assert len(bus._handlers) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        return EventBus()

    def test_with_very_large_number_of_handlers(self, bus):
        """Test with very large number of handlers (100)."""
        handlers = []
        for i in range(100):
            handler = AsyncMock()
            handler.__name__ = f'handler_{i}'
            handlers.append(handler)
            bus.subscribe(CustomTestEvent, handler)

        assert len(bus._handlers[CustomTestEvent]) == 100

        event = CustomTestEvent(test_id='123', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            # All 100 handlers should be scheduled
            assert mock_create_task.call_count == 100

    def test_emitting_events_of_multiple_types(self, bus):
        """Test emitting events of different types."""
        handler1 = AsyncMock()
        handler1.__name__ = 'handler1'
        handler2 = AsyncMock()
        handler2.__name__ = 'handler2'

        bus.subscribe(CustomTestEvent, handler1)
        bus.subscribe(AnotherTestEvent, handler2)

        event1 = CustomTestEvent(test_id='123', test_value=42)
        event2 = AnotherTestEvent(data='test')

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event1)
            bus.emit(event2)

            # Both handlers should be scheduled
            assert mock_create_task.call_count == 2

    def test_handler_with_no_name_attribute(self, bus):
        """Test subscribing handler without __name__ attribute."""
        # Create a mock without __name__
        handler = AsyncMock()
        del handler.__name__

        # Should handle gracefully or raise appropriate error
        try:
            bus.subscribe(CustomTestEvent, handler)
            # If it works, verify it's registered
            assert handler in bus._handlers[CustomTestEvent]
        except AttributeError:
            # If it requires __name__, that's acceptable behavior
            pass

    @pytest.mark.asyncio
    async def test_event_with_complex_data_types(self, bus):
        """Test events with complex nested data."""
        from uuid import uuid4

        received_event = None

        async def handler(event):
            nonlocal received_event
            received_event = event

        handler.__name__ = 'handler'

        bus.subscribe(BidPlacedEvent, handler)

        event = BidPlacedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            user_name='Test User',
            quantity=10.5,
            interested_only=False,
            new_total=100.5,
            group_id=uuid4(),
        )

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(event)
            await asyncio.sleep(0.01)

        assert received_event is not None
        assert received_event.user_name == 'Test User'
        assert received_event.quantity == 10.5


class TestGlobalEventBusInstance:
    """Test the global event_bus instance."""

    def test_global_event_bus_instance_exists(self):
        """Test that global event_bus instance exists and is EventBus."""
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)

    def test_global_event_bus_is_functional(self):
        """Test that global event_bus instance works correctly."""
        handler = AsyncMock()
        handler.__name__ = 'global_test_handler'

        # Clean up before test
        event_bus.clear_handlers()

        event_bus.subscribe(CustomTestEvent, handler)
        event = CustomTestEvent(test_id='global', test_value=42)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            event_bus.emit(event)

            assert mock_create_task.call_count == 1

        # Clean up after test
        event_bus.clear_handlers()

    def test_global_event_bus_can_be_cleared(self):
        """Test that global event_bus can be cleared."""
        handler = AsyncMock()
        handler.__name__ = 'handler'

        event_bus.subscribe(CustomTestEvent, handler)
        event_bus.clear_handlers()

        assert len(event_bus._handlers) == 0
