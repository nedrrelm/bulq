"""Seller follower service for managing seller following relationships."""

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.seller_follower_schemas import (
    FollowedSellerResponse,
    SellerFollowerResponse,
)
from app.core.error_codes import (
    ALREADY_FOLLOWING_SELLER,
    NOT_FOLLOWING_SELLER,
    SELLER_JOINING_DISABLED,
    SELLER_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.models import SellerFollower, User
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_group_repository,
    get_seller_follower_repository,
    get_seller_repository,
    get_user_repository,
)

from .base_service import BaseService

logger = get_logger(__name__)


class SellerFollowerService(BaseService):
    """Service for seller following operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.seller_repo = get_seller_repository(db)
        self.seller_follower_repo = get_seller_follower_repository(db)
        self.group_repo = get_group_repository(db)
        self.user_repo = get_user_repository(db)

    async def follow_seller(
        self, user: User, seller_id: UUID, group_id: UUID
    ) -> SellerFollowerResponse:
        """Follow a seller with a group."""
        # Verify user is member of the group
        await self._verify_group_membership(user, group_id)

        # Get seller and verify joining is allowed
        seller = await self.seller_repo.get_seller_by_id(seller_id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller not found',
                seller_id=str(seller_id),
            )

        if not seller.is_joining_allowed:
            raise BadRequestError(
                code=SELLER_JOINING_DISABLED,
                message='This seller is not accepting new followers',
                seller_id=str(seller_id),
            )

        # Check not already following
        existing = await self.seller_follower_repo.get_follower(seller_id, group_id)
        if existing:
            raise BadRequestError(
                code=ALREADY_FOLLOWING_SELLER,
                message='Group is already following this seller',
                seller_id=str(seller_id),
                group_id=str(group_id),
            )

        # Create follower record
        follower = SellerFollower(
            id=uuid.uuid4(),
            seller_id=seller_id,
            group_id=group_id,
        )
        follower = await self.seller_follower_repo.create_follower(follower)

        # Get group info for response
        group = await self.group_repo.get_group_by_id(group_id)
        members = await self.group_repo.get_group_members_with_admin_status(group_id)

        logger.info(
            'Group followed seller',
            extra={
                'user_id': str(user.id),
                'seller_id': str(seller_id),
                'group_id': str(group_id),
            },
        )

        return SellerFollowerResponse(
            id=str(follower.id),
            seller_id=str(follower.seller_id),
            group_id=str(follower.group_id),
            group_name=group.name if group else 'Unknown',
            member_count=len(members) if members else 0,
            created_at=follower.created_at.isoformat() if follower.created_at else '',
        )

    async def follow_by_invite_token(
        self, user: User, invite_token: str, group_id: UUID
    ) -> SellerFollowerResponse:
        """Follow a seller via invite token."""
        seller = await self.seller_repo.get_seller_by_invite_token(invite_token)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller not found',
                invite_token=invite_token,
            )

        return await self.follow_seller(user, seller.id, group_id)

    async def unfollow_seller(self, user: User, seller_id: UUID, group_id: UUID) -> None:
        """Unfollow a seller."""
        # Verify user is member of the group
        await self._verify_group_membership(user, group_id)

        deleted = await self.seller_follower_repo.delete_follower(seller_id, group_id)
        if not deleted:
            raise NotFoundError(
                code=NOT_FOLLOWING_SELLER,
                message='Group is not following this seller',
                seller_id=str(seller_id),
                group_id=str(group_id),
            )

        logger.info(
            'Group unfollowed seller',
            extra={
                'user_id': str(user.id),
                'seller_id': str(seller_id),
                'group_id': str(group_id),
            },
        )

    async def get_seller_followers(self, user: User) -> list[SellerFollowerResponse]:
        """Get all groups following the current user's seller profile."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )

        followers = await self.seller_follower_repo.get_followers_by_seller(seller.id)

        result = []
        for f in followers:
            group = f.group if f.group else await self.group_repo.get_group_by_id(f.group_id)
            members = await self.group_repo.get_group_members_with_admin_status(f.group_id)
            result.append(
                SellerFollowerResponse(
                    id=str(f.id),
                    seller_id=str(f.seller_id),
                    group_id=str(f.group_id),
                    group_name=group.name if group else 'Unknown',
                    member_count=len(members) if members else 0,
                    created_at=f.created_at.isoformat() if f.created_at else '',
                )
            )

        return result

    async def get_my_following_groups(
        self, user: User, seller_id: UUID
    ) -> list[SellerFollowerResponse]:
        """Get which of the current user's groups follow a given seller."""
        user_groups = await self.user_repo.get_user_groups(user)
        all_followers = await self.seller_follower_repo.get_followers_by_seller(seller_id)

        user_group_ids = {g.id for g in user_groups}
        my_followers = [f for f in all_followers if f.group_id in user_group_ids]

        result = []
        for f in my_followers:
            group = f.group if f.group else await self.group_repo.get_group_by_id(f.group_id)
            members = await self.group_repo.get_group_members_with_admin_status(f.group_id)
            result.append(
                SellerFollowerResponse(
                    id=str(f.id),
                    seller_id=str(f.seller_id),
                    group_id=str(f.group_id),
                    group_name=group.name if group else 'Unknown',
                    member_count=len(members) if members else 0,
                    created_at=f.created_at.isoformat() if f.created_at else '',
                )
            )

        return result

    async def get_followed_sellers(
        self, user: User, group_id: UUID
    ) -> list[FollowedSellerResponse]:
        """Get all sellers followed by a group."""
        await self._verify_group_membership(user, group_id)

        followed = await self.seller_follower_repo.get_followed_sellers_by_group(group_id)

        result = []
        for f in followed:
            seller = f.seller if f.seller else await self.seller_repo.get_seller_by_id(f.seller_id)
            if seller:
                result.append(
                    FollowedSellerResponse(
                        seller_id=str(seller.id),
                        display_name=seller.display_name,
                        description=seller.description,
                        is_joining_allowed=seller.is_joining_allowed,
                    )
                )

        return result
