"""Domain event definitions for the event bus."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    pass


@dataclass
class BidPlacedEvent(DomainEvent):
    """Event emitted when a user places or updates a bid."""

    run_id: UUID
    product_id: UUID
    user_id: UUID
    user_name: str
    quantity: float
    interested_only: bool
    new_total: float
    group_id: UUID


@dataclass
class BidRetractedEvent(DomainEvent):
    """Event emitted when a user retracts a bid."""

    run_id: UUID
    product_id: UUID
    user_id: UUID
    new_total: float
    group_id: UUID


@dataclass
class ReadyToggledEvent(DomainEvent):
    """Event emitted when a user toggles their ready status."""

    run_id: UUID
    user_id: UUID
    is_ready: bool
    group_id: UUID


@dataclass
class RunStateChangedEvent(DomainEvent):
    """Event emitted when a run's state changes."""

    run_id: UUID
    group_id: UUID
    old_state: str
    new_state: str
    store_name: str


@dataclass
class RunCreatedEvent(DomainEvent):
    """Event emitted when a new run is created."""

    run_id: UUID
    group_id: UUID
    store_id: UUID
    store_name: str
    state: str
    leader_name: str


@dataclass
class RunCancelledEvent(DomainEvent):
    """Event emitted when a run is cancelled."""

    run_id: UUID
    group_id: UUID
    store_name: str


@dataclass
class MemberJoinedEvent(DomainEvent):
    """Event emitted when a user joins a group."""

    group_id: UUID
    user_id: UUID
    user_name: str


@dataclass
class MemberRemovedEvent(DomainEvent):
    """Event emitted when a user is removed from a group."""

    group_id: UUID
    user_id: UUID
    removed_by_id: UUID


@dataclass
class MemberLeftEvent(DomainEvent):
    """Event emitted when a user leaves a group."""

    group_id: UUID
    user_id: UUID
