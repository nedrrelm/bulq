"""Abstract repository interfaces."""

from app.repositories.abstract.bid import AbstractBidRepository
from app.repositories.abstract.group import AbstractGroupRepository
from app.repositories.abstract.notification import AbstractNotificationRepository
from app.repositories.abstract.product import AbstractProductRepository
from app.repositories.abstract.reassignment import AbstractReassignmentRepository
from app.repositories.abstract.run import AbstractRunRepository
from app.repositories.abstract.shopping import AbstractShoppingRepository
from app.repositories.abstract.store import AbstractStoreRepository
from app.repositories.abstract.user import AbstractUserRepository

__all__ = [
    'AbstractBidRepository',
    'AbstractGroupRepository',
    'AbstractNotificationRepository',
    'AbstractProductRepository',
    'AbstractReassignmentRepository',
    'AbstractRunRepository',
    'AbstractShoppingRepository',
    'AbstractStoreRepository',
    'AbstractUserRepository',
]
