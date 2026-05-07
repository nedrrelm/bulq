"""Seller service for managing seller business logic."""

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    SellerPreviewResponse,
    SellerPublicResponse,
    SellerResponse,
    SellerSearchResult,
)
from app.core.error_codes import (
    SELLER_ALREADY_EXISTS,
    SELLER_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.models import Seller, User
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transactional
from app.repositories import get_seller_repository, get_store_repository

from .base_service import BaseService

logger = get_logger(__name__)


class SellerService(BaseService):
    """Service for seller operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.seller_repo = get_seller_repository(db)
        self.store_repo = get_store_repository(db)

    def _format_seller_response(self, seller: Seller) -> SellerResponse:
        """Format a Seller model into a SellerResponse."""
        return SellerResponse(
            id=str(seller.id),
            user_id=str(seller.user_id),
            store_id=str(seller.store_id),
            display_name=seller.display_name,
            description=seller.description,
            invite_token=seller.invite_token,
            is_joining_allowed=seller.is_joining_allowed,
            is_searchable=seller.is_searchable,
            created_at=seller.created_at.isoformat() if seller.created_at else '',
        )

    def _format_seller_public_response(self, seller: Seller) -> SellerPublicResponse:
        """Format a Seller model into a SellerPublicResponse."""
        return SellerPublicResponse(
            id=str(seller.id),
            display_name=seller.display_name,
            description=seller.description,
            is_joining_allowed=seller.is_joining_allowed,
        )

    async def create_seller(
        self, user: User, display_name: str, description: str | None = None
    ) -> SellerResponse:
        """Create a seller profile for a user, auto-creating a Store."""
        existing = await self.seller_repo.get_seller_by_user_id(user.id)
        if existing:
            raise BadRequestError(
                code=SELLER_ALREADY_EXISTS,
                message='User already has a seller profile',
                user_id=str(user.id),
            )

        # Auto-create a Store for the seller (via repo to support memory mode)
        store = await self.store_repo.create_store(display_name)

        seller = Seller(
            id=uuid.uuid4(),
            user_id=user.id,
            store_id=store.id,
            display_name=display_name.strip(),
            description=description.strip() if description else None,
            invite_token=str(uuid.uuid4()),
            is_joining_allowed=True,
            is_searchable=True,
        )
        seller = await self.seller_repo.create_seller(seller)

        logger.info(
            'Seller profile created',
            extra={
                'user_id': str(user.id),
                'seller_id': str(seller.id),
                'store_id': str(store.id),
            },
        )

        return self._format_seller_response(seller)

    async def get_my_seller_profile(self, user: User) -> SellerResponse | None:
        """Get the current user's seller profile, or None if they don't have one."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            return None
        return self._format_seller_response(seller)

    async def get_seller_by_id(self, seller_id: UUID) -> SellerPublicResponse:
        """Get a seller's public profile by ID."""
        seller = await self.seller_repo.get_seller_by_id(seller_id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller not found',
                seller_id=str(seller_id),
            )
        return self._format_seller_public_response(seller)

    async def get_seller_by_invite_token(self, invite_token: str) -> SellerPreviewResponse:
        """Get a seller preview by invite token."""
        seller = await self.seller_repo.get_seller_by_invite_token(invite_token)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller not found',
                invite_token=invite_token,
            )
        return SellerPreviewResponse(
            id=str(seller.id),
            display_name=seller.display_name,
            description=seller.description,
            is_joining_allowed=seller.is_joining_allowed,
        )

    @transactional('update seller')
    async def update_seller(
        self,
        user: User,
        display_name: str | None = None,
        description: str | None = None,
    ) -> SellerResponse:
        """Update the current user's seller profile."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )

        fields = {}
        if display_name is not None:
            fields['display_name'] = display_name.strip()
        if description is not None:
            fields['description'] = description.strip() if description else None

        if fields:
            seller = await self.seller_repo.update_seller(seller.id, **fields)

        logger.info(
            'Seller profile updated',
            extra={'user_id': str(user.id), 'seller_id': str(seller.id)},
        )

        return self._format_seller_response(seller)

    @transactional('toggle seller joining')
    async def toggle_joining_allowed(self, user: User) -> SellerResponse:
        """Toggle whether new groups can follow this seller."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )

        new_value = not seller.is_joining_allowed
        seller = await self.seller_repo.update_seller(seller.id, is_joining_allowed=new_value)

        logger.info(
            'Seller joining toggled',
            extra={
                'seller_id': str(seller.id),
                'is_joining_allowed': new_value,
            },
        )

        return self._format_seller_response(seller)

    @transactional('toggle seller searchable')
    async def toggle_searchable(self, user: User) -> SellerResponse:
        """Toggle whether this seller appears in search results."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )

        new_value = not seller.is_searchable
        seller = await self.seller_repo.update_seller(seller.id, is_searchable=new_value)

        logger.info(
            'Seller searchable toggled',
            extra={
                'seller_id': str(seller.id),
                'is_searchable': new_value,
            },
        )

        return self._format_seller_response(seller)

    async def search_sellers(self, query: str) -> list[SellerSearchResult]:
        """Search for sellers by display name."""
        if not query or len(query.strip()) < 2:
            return []

        sellers = await self.seller_repo.search_sellers(query.strip())
        return [
            SellerSearchResult(
                id=str(s.id),
                display_name=s.display_name,
                description=s.description,
            )
            for s in sellers
        ]

    @transactional('regenerate seller invite token')
    async def regenerate_invite_token(self, user: User) -> SellerResponse:
        """Regenerate the seller's invite token."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )

        new_token = str(uuid.uuid4())
        seller = await self.seller_repo.update_seller(seller.id, invite_token=new_token)

        logger.info(
            'Seller invite token regenerated',
            extra={'seller_id': str(seller.id)},
        )

        return self._format_seller_response(seller)
