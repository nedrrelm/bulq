"""Abstract sale repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Sale, SaleProduct


class AbstractSaleRepository(ABC):
    """Abstract base class for sale repository operations."""

    @abstractmethod
    async def create_sale(self, sale: Sale) -> Sale:
        raise NotImplementedError

    @abstractmethod
    async def get_sale_by_id(self, sale_id: UUID) -> Sale | None:
        raise NotImplementedError

    @abstractmethod
    async def get_sale_by_invite_token(self, invite_token: str) -> Sale | None:
        raise NotImplementedError

    @abstractmethod
    async def get_sales_by_seller(self, seller_id: UUID) -> list[Sale]:
        raise NotImplementedError

    @abstractmethod
    async def update_sale(self, sale_id: UUID, **fields) -> Sale | None:
        raise NotImplementedError

    @abstractmethod
    async def add_sale_product(self, sale_product: SaleProduct) -> SaleProduct:
        raise NotImplementedError

    @abstractmethod
    async def get_sale_product(self, sale_id: UUID, product_id: UUID) -> SaleProduct | None:
        raise NotImplementedError

    @abstractmethod
    async def get_sale_products(self, sale_id: UUID) -> list[SaleProduct]:
        raise NotImplementedError

    @abstractmethod
    async def update_sale_product(self, sale_product_id: UUID, **fields) -> SaleProduct | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_sale_product(self, sale_id: UUID, product_id: UUID) -> bool:
        raise NotImplementedError
