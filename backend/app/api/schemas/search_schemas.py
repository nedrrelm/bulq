"""Schemas for search-related requests and responses."""

from pydantic import BaseModel

from .product_schemas import ProductSearchResult
from .tag_schemas import TagSearchResult


class StoreSearchResult(BaseModel):
    """Search result for a store."""

    id: str
    name: str
    address: str | None


class GroupSearchResult(BaseModel):
    """Search result for a group."""

    id: str
    name: str
    member_count: int


class SellerSearchResultBrief(BaseModel):
    """Search result for a seller."""

    id: str
    store_id: str
    display_name: str
    description: str | None


class SearchResponse(BaseModel):
    """Response model for global search."""

    products: list[ProductSearchResult]
    stores: list[StoreSearchResult]
    groups: list[GroupSearchResult]
    tags: list[TagSearchResult] = []
    sellers: list[SellerSearchResultBrief] = []
