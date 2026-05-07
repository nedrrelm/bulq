"""Tag service for handling tag-related business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    TagBriefResponse,
    TagDetailResponse,
    TagSearchResult,
)
from app.core.error_codes import (
    PRODUCT_NOT_FOUND,
    TAG_ALREADY_EXISTS,
    TAG_ALREADY_ON_PRODUCT,
    TAG_NOT_FOUND,
    TAG_NOT_ON_PRODUCT,
    TAG_TYPE_INVALID,
    TAG_VALUE_EMPTY,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import Tag
from app.core.success_codes import TAG_ADDED_TO_PRODUCT, TAG_REMOVED_FROM_PRODUCT
from app.core.tag_types import VALID_TAG_TYPES
from app.infrastructure.transaction import transactional
from app.repositories import get_product_repository, get_tag_repository

from .base_service import BaseService


class TagService(BaseService):
    """Service for tag operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.tag_repo = get_tag_repository(db)
        self.product_repo = get_product_repository(db)

    async def search_tags(
        self,
        query: str,
        tag_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TagSearchResult]:
        """Search for tags by value."""
        tags = await self.tag_repo.search_tags(query, tag_type, limit, offset)

        results = []
        for tag in tags:
            product_count = await self.tag_repo.count_tag_products(tag.id)
            results.append(
                TagSearchResult(
                    id=str(tag.id),
                    value=tag.value,
                    type=tag.type,
                    product_count=product_count,
                )
            )
        return results

    async def get_tag_details(self, tag_id: UUID) -> TagDetailResponse | None:
        """Get detailed tag information including products."""
        tag = await self.tag_repo.get_tag_by_id(tag_id)
        if not tag:
            return None

        products = await self.tag_repo.get_products_by_tag(tag_id)
        product_count = await self.tag_repo.count_tag_products(tag_id)

        product_list = []
        for product in products:
            product_list.append(
                {
                    'id': str(product.id),
                    'name': product.name,
                    'brand': product.brand,
                    'unit': product.unit,
                }
            )

        return TagDetailResponse(
            id=str(tag.id),
            value=tag.value,
            type=tag.type,
            verified=tag.verified,
            products=product_list,
            product_count=product_count,
        )

    @transactional('create tag')
    async def create_tag(
        self,
        value: str,
        tag_type: str,
        user_id: UUID | None = None,
    ) -> Tag:
        """Create a new tag."""
        if not value or not value.strip():
            raise ValidationError(code=TAG_VALUE_EMPTY, message='Tag value cannot be empty')

        if tag_type not in VALID_TAG_TYPES:
            raise ValidationError(
                code=TAG_TYPE_INVALID,
                message=f'Invalid tag type. Must be one of: {", ".join(VALID_TAG_TYPES)}',
                tag_type=tag_type,
            )

        # Check for duplicates
        existing = await self.tag_repo.get_tag_by_value_and_type(value.strip(), tag_type)
        if existing:
            raise ValidationError(
                code=TAG_ALREADY_EXISTS,
                message=f'Tag "{value}" of type "{tag_type}" already exists',
                tag_id=str(existing.id),
            )

        return await self.tag_repo.create_tag(value.strip(), tag_type, created_by=user_id)

    async def add_tag_to_product(self, product_id: UUID, tag_id: UUID) -> dict:
        """Add a tag to a product."""
        product = await self.product_repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND, message='Product not found', product_id=str(product_id)
            )

        tag = await self.tag_repo.get_tag_by_id(tag_id)
        if not tag:
            raise NotFoundError(code=TAG_NOT_FOUND, message='Tag not found', tag_id=str(tag_id))

        already_exists = await self.tag_repo.is_tag_on_product(product_id, tag_id)
        if already_exists:
            raise ValidationError(
                code=TAG_ALREADY_ON_PRODUCT,
                message='Tag is already on this product',
                product_id=str(product_id),
                tag_id=str(tag_id),
            )

        await self.tag_repo.add_tag_to_product(product_id, tag_id)

        from app.api.schemas import SuccessResponse

        return SuccessResponse(
            code=TAG_ADDED_TO_PRODUCT,
            details={
                'product_id': str(product_id),
                'tag_id': str(tag_id),
                'tag_value': tag.value,
                'tag_type': tag.type,
            },
        )

    async def remove_tag_from_product(self, product_id: UUID, tag_id: UUID) -> dict:
        """Remove a tag from a product."""
        is_on_product = await self.tag_repo.is_tag_on_product(product_id, tag_id)
        if not is_on_product:
            raise ValidationError(
                code=TAG_NOT_ON_PRODUCT,
                message='Tag is not on this product',
                product_id=str(product_id),
                tag_id=str(tag_id),
            )

        await self.tag_repo.remove_tag_from_product(product_id, tag_id)

        from app.api.schemas import SuccessResponse

        return SuccessResponse(
            code=TAG_REMOVED_FROM_PRODUCT,
            details={
                'product_id': str(product_id),
                'tag_id': str(tag_id),
            },
        )

    async def get_tags_for_product(self, product_id: UUID) -> list[TagBriefResponse]:
        """Get all tags for a product."""
        tags = await self.tag_repo.get_tags_by_product(product_id)
        return [TagBriefResponse(id=str(tag.id), value=tag.value, type=tag.type) for tag in tags]

    async def get_tag_types(self) -> list[str]:
        """Get list of valid tag types."""
        return VALID_TAG_TYPES
