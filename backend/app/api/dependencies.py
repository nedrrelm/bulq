"""Dependency injection providers for services.

This module provides FastAPI dependency injection functions for all service classes.
Using Depends() with these providers eliminates duplicate service instantiation code
across route handlers and improves testability.

Usage in routes:
    from app.api.dependencies import AdminServiceDep

    @router.get('/users')
    async def get_users(service: AdminServiceDep):
        return service.get_users()
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.services import (
    AdminService,
    BidService,
    DistributionGroupService,
    DistributionService,
    GroupInviteService,
    GroupManagementService,
    GroupMembershipService,
    GroupQueryService,
    NotificationService,
    ProductService,
    ReassignmentService,
    RunNotificationService,
    RunService,
    RunStateService,
    ShoppingService,
    StoreService,
    TagService,
)

# =============================================================================
# Service Dependency Providers
# =============================================================================


async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Provide AdminService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        AdminService instance
    """
    return AdminService(db)


async def get_bid_service(db: AsyncSession = Depends(get_db)) -> BidService:
    """Provide BidService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        BidService instance
    """
    return BidService(db)


async def get_run_notification_service(
    db: AsyncSession = Depends(get_db),
) -> RunNotificationService:
    """Provide RunNotificationService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        RunNotificationService instance
    """
    return RunNotificationService(db)


async def get_run_state_service(
    db: AsyncSession = Depends(get_db),
    notification_service: RunNotificationService = Depends(get_run_notification_service),
) -> RunStateService:
    """Provide RunStateService instance with injected database session and notification service.

    Args:
        db: Database session injected by FastAPI
        notification_service: RunNotificationService injected by FastAPI

    Returns:
        RunStateService instance
    """
    return RunStateService(db, notification_service)


async def get_run_service(
    db: AsyncSession = Depends(get_db),
    bid_service: BidService = Depends(get_bid_service),
    notification_service: RunNotificationService = Depends(get_run_notification_service),
    state_service: RunStateService = Depends(get_run_state_service),
) -> RunService:
    """Provide RunService instance with injected database session and sub-services.

    Args:
        db: Database session injected by FastAPI
        bid_service: BidService injected by FastAPI
        notification_service: RunNotificationService injected by FastAPI
        state_service: RunStateService injected by FastAPI

    Returns:
        RunService instance
    """
    return RunService(db, bid_service, notification_service, state_service)


async def get_group_query_service(db: AsyncSession = Depends(get_db)) -> GroupQueryService:
    """Provide GroupQueryService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        GroupQueryService instance
    """
    return GroupQueryService(db)


async def get_group_management_service(
    db: AsyncSession = Depends(get_db),
) -> GroupManagementService:
    """Provide GroupManagementService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        GroupManagementService instance
    """
    return GroupManagementService(db)


async def get_group_invite_service(db: AsyncSession = Depends(get_db)) -> GroupInviteService:
    """Provide GroupInviteService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        GroupInviteService instance
    """
    return GroupInviteService(db)


async def get_group_membership_service(
    db: AsyncSession = Depends(get_db),
) -> GroupMembershipService:
    """Provide GroupMembershipService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        GroupMembershipService instance
    """
    return GroupMembershipService(db)


async def get_shopping_service(db: AsyncSession = Depends(get_db)) -> ShoppingService:
    """Provide ShoppingService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ShoppingService instance
    """
    return ShoppingService(db)


async def get_reassignment_service(db: AsyncSession = Depends(get_db)) -> ReassignmentService:
    """Provide ReassignmentService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ReassignmentService instance
    """
    return ReassignmentService(db)


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Provide NotificationService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        NotificationService instance
    """
    return NotificationService(db)


async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Provide ProductService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ProductService instance
    """
    return ProductService(db)


async def get_store_service(db: AsyncSession = Depends(get_db)) -> StoreService:
    """Provide StoreService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        StoreService instance
    """
    return StoreService(db)


async def get_distribution_service(db: AsyncSession = Depends(get_db)) -> DistributionService:
    """Provide DistributionService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        DistributionService instance
    """
    return DistributionService(db)


async def get_tag_service(db: AsyncSession = Depends(get_db)) -> TagService:
    """Provide TagService instance with injected database session."""
    return TagService(db)


async def get_distribution_group_service(
    db: AsyncSession = Depends(get_db),
) -> DistributionGroupService:
    """Provide DistributionGroupService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        DistributionGroupService instance
    """
    return DistributionGroupService(db)


# =============================================================================
# Type Aliases for Cleaner Route Signatures
# =============================================================================

# These type aliases use Annotated to combine the type and Depends() for cleaner route signatures.
# Instead of: service: AdminService = Depends(get_admin_service)
# Use: service: AdminServiceDep

AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
BidServiceDep = Annotated[BidService, Depends(get_bid_service)]
DistributionGroupServiceDep = Annotated[
    DistributionGroupService, Depends(get_distribution_group_service)
]
DistributionServiceDep = Annotated[DistributionService, Depends(get_distribution_service)]
GroupQueryServiceDep = Annotated[GroupQueryService, Depends(get_group_query_service)]
GroupManagementServiceDep = Annotated[GroupManagementService, Depends(get_group_management_service)]
GroupInviteServiceDep = Annotated[GroupInviteService, Depends(get_group_invite_service)]
GroupMembershipServiceDep = Annotated[GroupMembershipService, Depends(get_group_membership_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
ReassignmentServiceDep = Annotated[ReassignmentService, Depends(get_reassignment_service)]
RunNotificationServiceDep = Annotated[RunNotificationService, Depends(get_run_notification_service)]
RunServiceDep = Annotated[RunService, Depends(get_run_service)]
RunStateServiceDep = Annotated[RunStateService, Depends(get_run_state_service)]
ShoppingServiceDep = Annotated[ShoppingService, Depends(get_shopping_service)]
StoreServiceDep = Annotated[StoreService, Depends(get_store_service)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
