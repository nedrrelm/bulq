"""Unit tests for domain event dataclasses.

Tests cover:
- DomainEvent base class instantiation and inheritance
- All event dataclass types (instantiation, field access, equality, repr)
- Event field validation (missing fields, type checking)
- UUID field handling
- Optional fields
- Integration with event bus
"""

from dataclasses import is_dataclass
from uuid import UUID, uuid4

import pytest

from app.events.domain_events import (
    BidPlacedEvent,
    BidRetractedEvent,
    CommentUpdatedEvent,
    DistributionUpdatedEvent,
    DomainEvent,
    HelperToggledEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
    MemberRemovedEvent,
    ReadyToggledEvent,
    RunCancelledEvent,
    RunCreatedEvent,
    RunStateChangedEvent,
    ShoppingItemUpdatedEvent,
)
from app.events.event_bus import EventBus


class TestDomainEventBaseClass:
    """Test DomainEvent base class."""

    def test_can_instantiate_base_domain_event(self):
        """Test that base DomainEvent can be instantiated."""
        event = DomainEvent()

        assert event is not None
        assert isinstance(event, DomainEvent)

    def test_domain_event_is_dataclass(self):
        """Test that DomainEvent is a dataclass."""
        assert is_dataclass(DomainEvent)

    def test_inheritance_works(self):
        """Test that inheritance from DomainEvent works."""
        event = BidPlacedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=uuid4(),
        )

        assert isinstance(event, DomainEvent)
        assert isinstance(event, BidPlacedEvent)


class TestBidPlacedEvent:
    """Test BidPlacedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test that BidPlacedEvent can be instantiated with all required fields."""
        run_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = BidPlacedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            user_name='John Doe',
            quantity=5.0,
            interested_only=False,
            new_total=50.0,
            group_id=group_id,
        )

        assert event is not None
        assert isinstance(event, BidPlacedEvent)

    def test_fields_are_accessible(self):
        """Test that all fields are accessible."""
        run_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = BidPlacedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            user_name='Jane Smith',
            quantity=3.5,
            interested_only=True,
            new_total=35.0,
            group_id=group_id,
        )

        assert event.run_id == run_id
        assert event.product_id == product_id
        assert event.user_id == user_id
        assert event.user_name == 'Jane Smith'
        assert event.quantity == 3.5
        assert event.interested_only is True
        assert event.new_total == 35.0
        assert event.group_id == group_id

    def test_dataclass_equality(self):
        """Test that two events with same data are equal."""
        run_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event1 = BidPlacedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=group_id,
        )

        event2 = BidPlacedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=group_id,
        )

        assert event1 == event2

    def test_dataclass_repr(self):
        """Test that string representation works."""
        event = BidPlacedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=uuid4(),
        )

        repr_str = repr(event)
        assert 'BidPlacedEvent' in repr_str
        assert 'user_name' in repr_str

    def test_inherits_from_domain_event(self):
        """Test that BidPlacedEvent inherits from DomainEvent."""
        event = BidPlacedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=uuid4(),
        )

        assert isinstance(event, DomainEvent)

    def test_uuid_fields_work_correctly(self):
        """Test that UUID fields work correctly."""
        run_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = BidPlacedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            user_name='Test',
            quantity=1.0,
            interested_only=False,
            new_total=10.0,
            group_id=group_id,
        )

        assert isinstance(event.run_id, UUID)
        assert isinstance(event.product_id, UUID)
        assert isinstance(event.user_id, UUID)
        assert isinstance(event.group_id, UUID)


class TestBidRetractedEvent:
    """Test BidRetractedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = BidRetractedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            new_total=0.0,
            group_id=uuid4(),
        )

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = BidRetractedEvent(
            run_id=run_id,
            product_id=product_id,
            user_id=user_id,
            new_total=25.0,
            group_id=group_id,
        )

        assert event.run_id == run_id
        assert event.product_id == product_id
        assert event.user_id == user_id
        assert event.new_total == 25.0
        assert event.group_id == group_id

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = BidRetractedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            new_total=0.0,
            group_id=uuid4(),
        )

        assert isinstance(event, DomainEvent)


class TestReadyToggledEvent:
    """Test ReadyToggledEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = ReadyToggledEvent(run_id=uuid4(), user_id=uuid4(), is_ready=True, group_id=uuid4())

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = ReadyToggledEvent(run_id=run_id, user_id=user_id, is_ready=False, group_id=group_id)

        assert event.run_id == run_id
        assert event.user_id == user_id
        assert event.is_ready is False
        assert event.group_id == group_id

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = ReadyToggledEvent(run_id=uuid4(), user_id=uuid4(), is_ready=True, group_id=uuid4())

        assert isinstance(event, DomainEvent)


class TestRunStateChangedEvent:
    """Test RunStateChangedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = RunStateChangedEvent(
            run_id=uuid4(),
            group_id=uuid4(),
            old_state='draft',
            new_state='active',
            store_name='Test Store',
        )

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        group_id = uuid4()

        event = RunStateChangedEvent(
            run_id=run_id,
            group_id=group_id,
            old_state='active',
            new_state='completed',
            store_name='Super Market',
        )

        assert event.run_id == run_id
        assert event.group_id == group_id
        assert event.old_state == 'active'
        assert event.new_state == 'completed'
        assert event.store_name == 'Super Market'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = RunStateChangedEvent(
            run_id=uuid4(),
            group_id=uuid4(),
            old_state='draft',
            new_state='active',
            store_name='Test Store',
        )

        assert isinstance(event, DomainEvent)


class TestRunCreatedEvent:
    """Test RunCreatedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = RunCreatedEvent(
            run_id=uuid4(),
            group_id=uuid4(),
            store_id=uuid4(),
            store_name='Test Store',
            state='draft',
            leader_name='John Doe',
        )

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        event = RunCreatedEvent(
            run_id=run_id,
            group_id=group_id,
            store_id=store_id,
            store_name='Super Market',
            state='draft',
            leader_name='Jane Smith',
        )

        assert event.run_id == run_id
        assert event.group_id == group_id
        assert event.store_id == store_id
        assert event.store_name == 'Super Market'
        assert event.state == 'draft'
        assert event.leader_name == 'Jane Smith'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = RunCreatedEvent(
            run_id=uuid4(),
            group_id=uuid4(),
            store_id=uuid4(),
            store_name='Test Store',
            state='draft',
            leader_name='Test Leader',
        )

        assert isinstance(event, DomainEvent)


class TestRunCancelledEvent:
    """Test RunCancelledEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = RunCancelledEvent(run_id=uuid4(), group_id=uuid4(), store_name='Test Store')

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        group_id = uuid4()

        event = RunCancelledEvent(run_id=run_id, group_id=group_id, store_name='Super Market')

        assert event.run_id == run_id
        assert event.group_id == group_id
        assert event.store_name == 'Super Market'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = RunCancelledEvent(run_id=uuid4(), group_id=uuid4(), store_name='Test Store')

        assert isinstance(event, DomainEvent)


class TestMemberJoinedEvent:
    """Test MemberJoinedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = MemberJoinedEvent(group_id=uuid4(), user_id=uuid4(), user_name='John Doe')

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        group_id = uuid4()
        user_id = uuid4()

        event = MemberJoinedEvent(group_id=group_id, user_id=user_id, user_name='Jane Smith')

        assert event.group_id == group_id
        assert event.user_id == user_id
        assert event.user_name == 'Jane Smith'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = MemberJoinedEvent(group_id=uuid4(), user_id=uuid4(), user_name='Test User')

        assert isinstance(event, DomainEvent)


class TestMemberRemovedEvent:
    """Test MemberRemovedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = MemberRemovedEvent(group_id=uuid4(), user_id=uuid4(), removed_by_id=uuid4())

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        group_id = uuid4()
        user_id = uuid4()
        removed_by_id = uuid4()

        event = MemberRemovedEvent(group_id=group_id, user_id=user_id, removed_by_id=removed_by_id)

        assert event.group_id == group_id
        assert event.user_id == user_id
        assert event.removed_by_id == removed_by_id

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = MemberRemovedEvent(group_id=uuid4(), user_id=uuid4(), removed_by_id=uuid4())

        assert isinstance(event, DomainEvent)


class TestMemberLeftEvent:
    """Test MemberLeftEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = MemberLeftEvent(group_id=uuid4(), user_id=uuid4())

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        group_id = uuid4()
        user_id = uuid4()

        event = MemberLeftEvent(group_id=group_id, user_id=user_id)

        assert event.group_id == group_id
        assert event.user_id == user_id

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = MemberLeftEvent(group_id=uuid4(), user_id=uuid4())

        assert isinstance(event, DomainEvent)


class TestShoppingItemUpdatedEvent:
    """Test ShoppingItemUpdatedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = ShoppingItemUpdatedEvent(run_id=uuid4(), item_id=uuid4(), action='product_added')

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        item_id = uuid4()

        event = ShoppingItemUpdatedEvent(run_id=run_id, item_id=item_id, action='price_added')

        assert event.run_id == run_id
        assert event.item_id == item_id
        assert event.action == 'price_added'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = ShoppingItemUpdatedEvent(run_id=uuid4(), item_id=uuid4(), action='marked_purchased')

        assert isinstance(event, DomainEvent)

    def test_optional_item_id_field(self):
        """Test that item_id can be None (for product_added action)."""
        event = ShoppingItemUpdatedEvent(run_id=uuid4(), item_id=None, action='product_added')

        assert event.item_id is None
        assert event.action == 'product_added'

    @pytest.mark.parametrize(
        'action',
        [
            'product_added',
            'price_added',
            'marked_purchased',
            'added_more',
            'purchase_updated',
            'unpurchased',
        ],
    )
    def test_various_action_types(self, action):
        """Test ShoppingItemUpdatedEvent with various action types."""
        event = ShoppingItemUpdatedEvent(run_id=uuid4(), item_id=uuid4(), action=action)

        assert event.action == action


class TestDistributionUpdatedEvent:
    """Test DistributionUpdatedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = DistributionUpdatedEvent(run_id=uuid4(), bid_id=uuid4(), action='marked_picked_up')

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        bid_id = uuid4()

        event = DistributionUpdatedEvent(run_id=run_id, bid_id=bid_id, action='marked_picked_up')

        assert event.run_id == run_id
        assert event.bid_id == bid_id
        assert event.action == 'marked_picked_up'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = DistributionUpdatedEvent(run_id=uuid4(), bid_id=uuid4(), action='marked_picked_up')

        assert isinstance(event, DomainEvent)


class TestHelperToggledEvent:
    """Test HelperToggledEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = HelperToggledEvent(run_id=uuid4(), user_id=uuid4())

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()
        user_id = uuid4()

        event = HelperToggledEvent(run_id=run_id, user_id=user_id)

        assert event.run_id == run_id
        assert event.user_id == user_id

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = HelperToggledEvent(run_id=uuid4(), user_id=uuid4())

        assert isinstance(event, DomainEvent)


class TestCommentUpdatedEvent:
    """Test CommentUpdatedEvent dataclass."""

    def test_can_instantiate_with_all_required_fields(self):
        """Test instantiation with all required fields."""
        event = CommentUpdatedEvent(run_id=uuid4(), comment='Test comment')

        assert event is not None

    def test_fields_are_accessible(self):
        """Test field accessibility."""
        run_id = uuid4()

        event = CommentUpdatedEvent(run_id=run_id, comment='This is a test comment')

        assert event.run_id == run_id
        assert event.comment == 'This is a test comment'

    def test_inherits_from_domain_event(self):
        """Test inheritance from DomainEvent."""
        event = CommentUpdatedEvent(run_id=uuid4(), comment='Test')

        assert isinstance(event, DomainEvent)

    def test_optional_comment_field(self):
        """Test that comment can be None (for clearing comments)."""
        event = CommentUpdatedEvent(run_id=uuid4(), comment=None)

        assert event.comment is None


class TestEventFieldValidation:
    """Test event field validation."""

    def test_bid_placed_event_with_missing_fields_raises_type_error(self):
        """Test that missing fields raise TypeError."""
        with pytest.raises(TypeError):
            BidPlacedEvent(run_id=uuid4(), product_id=uuid4())

    def test_run_created_event_with_missing_fields_raises_type_error(self):
        """Test that missing fields raise TypeError."""
        with pytest.raises(TypeError):
            RunCreatedEvent(run_id=uuid4(), group_id=uuid4())

    def test_member_joined_event_with_missing_fields_raises_type_error(self):
        """Test that missing fields raise TypeError."""
        with pytest.raises(TypeError):
            MemberJoinedEvent(group_id=uuid4())

    def test_uuid_fields_accept_uuid_objects(self):
        """Test that UUID fields work correctly with UUID objects."""
        run_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        event = ReadyToggledEvent(run_id=run_id, user_id=user_id, is_ready=True, group_id=group_id)

        assert isinstance(event.run_id, UUID)
        assert isinstance(event.user_id, UUID)
        assert isinstance(event.group_id, UUID)

    def test_uuid_fields_from_uuid4(self):
        """Test UUID fields created with uuid4()."""
        event = MemberLeftEvent(group_id=uuid4(), user_id=uuid4())

        assert isinstance(event.group_id, UUID)
        assert isinstance(event.user_id, UUID)


class TestEventDataclassFeatures:
    """Test dataclass-specific features."""

    def test_event_equality_with_different_data(self):
        """Test that events with different data are not equal."""
        event1 = MemberLeftEvent(group_id=uuid4(), user_id=uuid4())
        event2 = MemberLeftEvent(group_id=uuid4(), user_id=uuid4())

        assert event1 != event2

    def test_event_repr_contains_class_name(self):
        """Test that repr contains the class name."""
        event = RunCancelledEvent(run_id=uuid4(), group_id=uuid4(), store_name='Test Store')

        repr_str = repr(event)
        assert 'RunCancelledEvent' in repr_str

    def test_event_is_dataclass(self):
        """Test that all events are dataclasses."""
        events = [
            BidPlacedEvent(
                run_id=uuid4(),
                product_id=uuid4(),
                user_id=uuid4(),
                user_name='Test',
                quantity=1.0,
                interested_only=False,
                new_total=10.0,
                group_id=uuid4(),
            ),
            BidRetractedEvent(
                run_id=uuid4(),
                product_id=uuid4(),
                user_id=uuid4(),
                new_total=0.0,
                group_id=uuid4(),
            ),
            ReadyToggledEvent(run_id=uuid4(), user_id=uuid4(), is_ready=True, group_id=uuid4()),
            RunStateChangedEvent(
                run_id=uuid4(),
                group_id=uuid4(),
                old_state='draft',
                new_state='active',
                store_name='Test',
            ),
            RunCreatedEvent(
                run_id=uuid4(),
                group_id=uuid4(),
                store_id=uuid4(),
                store_name='Test',
                state='draft',
                leader_name='Test',
            ),
            RunCancelledEvent(run_id=uuid4(), group_id=uuid4(), store_name='Test'),
            MemberJoinedEvent(group_id=uuid4(), user_id=uuid4(), user_name='Test'),
            MemberRemovedEvent(group_id=uuid4(), user_id=uuid4(), removed_by_id=uuid4()),
            MemberLeftEvent(group_id=uuid4(), user_id=uuid4()),
            ShoppingItemUpdatedEvent(run_id=uuid4(), item_id=uuid4(), action='product_added'),
            DistributionUpdatedEvent(run_id=uuid4(), bid_id=uuid4(), action='marked_picked_up'),
            HelperToggledEvent(run_id=uuid4(), user_id=uuid4()),
            CommentUpdatedEvent(run_id=uuid4(), comment='Test'),
        ]

        for event in events:
            assert is_dataclass(event)


class TestIntegrationWithEventBus:
    """Test domain events integration with event bus."""

    @pytest.fixture
    def bus(self):
        """Create fresh EventBus instance for each test."""
        bus = EventBus()
        yield bus
        bus.clear_handlers()

    def test_creating_event_and_emitting_through_event_bus(self, bus):
        """Test creating event and emitting through event bus."""
        from unittest.mock import AsyncMock, patch

        handler = AsyncMock()
        handler.__name__ = 'test_handler'

        bus.subscribe(BidPlacedEvent, handler)

        event = BidPlacedEvent(
            run_id=uuid4(),
            product_id=uuid4(),
            user_id=uuid4(),
            user_name='Test User',
            quantity=5.0,
            interested_only=False,
            new_total=50.0,
            group_id=uuid4(),
        )

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            assert mock_create_task.call_count == 1

    @pytest.mark.asyncio
    async def test_event_data_integrity_through_subscription_emission_cycle(self, bus):
        """Test event data integrity through subscription/emission cycle."""
        import asyncio

        received_events = []

        async def capturing_handler(event):
            received_events.append(event)

        capturing_handler.__name__ = 'capturing_handler'

        bus.subscribe(RunCreatedEvent, capturing_handler)

        original_event = RunCreatedEvent(
            run_id=uuid4(),
            group_id=uuid4(),
            store_id=uuid4(),
            store_name='Integration Test Store',
            state='draft',
            leader_name='Integration Leader',
        )

        from unittest.mock import patch

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            mock_create_task.side_effect = lambda coro, **kwargs: asyncio.create_task(coro)

            bus.emit(original_event)
            await asyncio.sleep(0.01)

        assert len(received_events) == 1
        received_event = received_events[0]

        # Verify data integrity
        assert received_event.run_id == original_event.run_id
        assert received_event.group_id == original_event.group_id
        assert received_event.store_id == original_event.store_id
        assert received_event.store_name == 'Integration Test Store'
        assert received_event.state == 'draft'
        assert received_event.leader_name == 'Integration Leader'

    @pytest.mark.parametrize(
        'event_class,event_kwargs',
        [
            (
                BidPlacedEvent,
                {
                    'run_id': uuid4(),
                    'product_id': uuid4(),
                    'user_id': uuid4(),
                    'user_name': 'Test',
                    'quantity': 1.0,
                    'interested_only': False,
                    'new_total': 10.0,
                    'group_id': uuid4(),
                },
            ),
            (
                BidRetractedEvent,
                {
                    'run_id': uuid4(),
                    'product_id': uuid4(),
                    'user_id': uuid4(),
                    'new_total': 0.0,
                    'group_id': uuid4(),
                },
            ),
            (
                ReadyToggledEvent,
                {'run_id': uuid4(), 'user_id': uuid4(), 'is_ready': True, 'group_id': uuid4()},
            ),
            (
                RunStateChangedEvent,
                {
                    'run_id': uuid4(),
                    'group_id': uuid4(),
                    'old_state': 'draft',
                    'new_state': 'active',
                    'store_name': 'Test',
                },
            ),
            (
                RunCreatedEvent,
                {
                    'run_id': uuid4(),
                    'group_id': uuid4(),
                    'store_id': uuid4(),
                    'store_name': 'Test',
                    'state': 'draft',
                    'leader_name': 'Test',
                },
            ),
            (
                RunCancelledEvent,
                {'run_id': uuid4(), 'group_id': uuid4(), 'store_name': 'Test'},
            ),
            (
                MemberJoinedEvent,
                {'group_id': uuid4(), 'user_id': uuid4(), 'user_name': 'Test'},
            ),
            (
                MemberRemovedEvent,
                {'group_id': uuid4(), 'user_id': uuid4(), 'removed_by_id': uuid4()},
            ),
            (MemberLeftEvent, {'group_id': uuid4(), 'user_id': uuid4()}),
            (
                ShoppingItemUpdatedEvent,
                {'run_id': uuid4(), 'item_id': uuid4(), 'action': 'product_added'},
            ),
            (
                DistributionUpdatedEvent,
                {'run_id': uuid4(), 'bid_id': uuid4(), 'action': 'marked_picked_up'},
            ),
            (HelperToggledEvent, {'run_id': uuid4(), 'user_id': uuid4()}),
            (CommentUpdatedEvent, {'run_id': uuid4(), 'comment': 'Test'}),
        ],
    )
    def test_all_event_types_work_with_event_bus(self, bus, event_class, event_kwargs):
        """Test that all event types can be emitted through event bus."""
        from unittest.mock import AsyncMock, patch

        handler = AsyncMock()
        handler.__name__ = 'test_handler'

        bus.subscribe(event_class, handler)
        event = event_class(**event_kwargs)

        with patch('app.events.event_bus.create_background_task') as mock_create_task:
            bus.emit(event)

            assert mock_create_task.call_count == 1
