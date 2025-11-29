"""Shared storage for memory repositories - Singleton pattern."""

from uuid import UUID

from app.core.models import (
    Group,
    LeaderReassignmentRequest,
    Notification,
    Product,
    ProductAvailability,
    ProductBid,
    Run,
    RunParticipation,
    ShoppingListItem,
    Store,
    User,
)


class MemoryStorage:
    """Singleton storage for in-memory repositories."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_storage()
        return cls._instance

    def _init_storage(self):
        """Initialize storage dictionaries. Called once by __new__."""
        # Storage dictionaries
        self._users: dict[UUID, User] = {}
        self._users_by_username: dict[str, User] = {}
        self._groups: dict[UUID, Group] = {}
        self._group_memberships: dict[UUID, list[UUID]] = {}  # group_id -> [user_ids]
        self._group_admin_status: dict[tuple, bool] = {}  # (group_id, user_id) -> is_admin
        self._stores: dict[UUID, Store] = {}
        self._runs: dict[UUID, Run] = {}
        self._products: dict[UUID, Product] = {}
        self._participations: dict[UUID, RunParticipation] = {}
        self._bids: dict[UUID, ProductBid] = {}
        self._shopping_list_items: dict[UUID, ShoppingListItem] = {}
        self._product_availabilities: dict[UUID, ProductAvailability] = {}
        self._notifications: dict[UUID, Notification] = {}
        self._reassignment_requests: dict[UUID, LeaderReassignmentRequest] = {}

        MemoryStorage._initialized = True

    @property
    def users(self) -> dict[UUID, User]:
        return self._users

    @property
    def users_by_username(self) -> dict[str, User]:
        return self._users_by_username

    @property
    def groups(self) -> dict[UUID, Group]:
        return self._groups

    @property
    def group_memberships(self) -> dict[UUID, list[UUID]]:
        return self._group_memberships

    @property
    def group_admin_status(self) -> dict[tuple, bool]:
        return self._group_admin_status

    @property
    def stores(self) -> dict[UUID, Store]:
        return self._stores

    @property
    def runs(self) -> dict[UUID, Run]:
        return self._runs

    @property
    def products(self) -> dict[UUID, Product]:
        return self._products

    @property
    def participations(self) -> dict[UUID, RunParticipation]:
        return self._participations

    @property
    def bids(self) -> dict[UUID, ProductBid]:
        return self._bids

    @property
    def shopping_list_items(self) -> dict[UUID, ShoppingListItem]:
        return self._shopping_list_items

    @property
    def product_availabilities(self) -> dict[UUID, ProductAvailability]:
        return self._product_availabilities

    @property
    def notifications(self) -> dict[UUID, Notification]:
        return self._notifications

    @property
    def reassignment_requests(self) -> dict[UUID, LeaderReassignmentRequest]:
        return self._reassignment_requests
