"""Shared storage for memory repositories - Singleton pattern."""

from uuid import UUID

from app.core.models import (
    DistributionGroup,
    Group,
    LeaderReassignmentRequest,
    Notification,
    Product,
    ProductAvailability,
    ProductBid,
    Run,
    RunParticipation,
    Sale,
    SaleDistributionItem,
    SaleProduct,
    Seller,
    SellerFollower,
    ShoppingListItem,
    Store,
    Tag,
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
        self._distribution_groups: dict[UUID, DistributionGroup] = {}
        self._tags: dict[UUID, Tag] = {}
        self._product_tags: dict[tuple[UUID, UUID], bool] = {}  # (product_id, tag_id) -> True
        self._sellers: dict[UUID, Seller] = {}
        self._seller_followers: dict[UUID, SellerFollower] = {}
        self._sales: dict[UUID, Sale] = {}
        self._sale_products: dict[UUID, SaleProduct] = {}
        self._sale_distribution_items: dict[UUID, SaleDistributionItem] = {}

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

    @property
    def distribution_groups(self) -> dict[UUID, DistributionGroup]:
        return self._distribution_groups

    @property
    def tags(self) -> dict[UUID, Tag]:
        return self._tags

    @property
    def product_tags(self) -> dict[tuple[UUID, UUID], bool]:
        return self._product_tags

    @property
    def sellers(self) -> dict[UUID, Seller]:
        return self._sellers

    @property
    def seller_followers(self) -> dict[UUID, SellerFollower]:
        return self._seller_followers

    @property
    def sales(self) -> dict[UUID, Sale]:
        return self._sales

    @property
    def sale_products(self) -> dict[UUID, SaleProduct]:
        return self._sale_products

    @property
    def sale_distribution_items(self) -> dict[UUID, SaleDistributionItem]:
        return self._sale_distribution_items
