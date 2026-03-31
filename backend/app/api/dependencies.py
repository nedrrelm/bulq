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
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.services import (
    AdminService,
    BidService,
    DistributionService,
    GroupService,
    NotificationService,
    ProductService,
    ReassignmentService,
    RunNotificationService,
    RunService,
    RunStateService,
    ShoppingService,
    StoreService,
)

# =============================================================================
# Service Dependency Providers
# =============================================================================


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """Provide AdminService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        AdminService instance
    """
    return AdminService(db)


def get_bid_service(db: Session = Depends(get_db)) -> BidService:
    """Provide BidService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        BidService instance
    """
    return BidService(db)


def get_run_notification_service(db: Session = Depends(get_db)) -> RunNotificationService:
    """Provide RunNotificationService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        RunNotificationService instance
    """
    return RunNotificationService(db)


def get_run_state_service(
    db: Session = Depends(get_db),
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


def get_run_service(
    db: Session = Depends(get_db),
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


def get_group_service(db: Session = Depends(get_db)) -> GroupService:
    """Provide GroupService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        GroupService instance
    """
    return GroupService(db)


def get_shopping_service(db: Session = Depends(get_db)) -> ShoppingService:
    """Provide ShoppingService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ShoppingService instance
    """
    return ShoppingService(db)


def get_reassignment_service(db: Session = Depends(get_db)) -> ReassignmentService:
    """Provide ReassignmentService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ReassignmentService instance
    """
    return ReassignmentService(db)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """Provide NotificationService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        NotificationService instance
    """
    return NotificationService(db)


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Provide ProductService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        ProductService instance
    """
    return ProductService(db)


def get_store_service(db: Session = Depends(get_db)) -> StoreService:
    """Provide StoreService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        StoreService instance
    """
    return StoreService(db)


def get_distribution_service(db: Session = Depends(get_db)) -> DistributionService:
    """Provide DistributionService instance with injected database session.

    Args:
        db: Database session injected by FastAPI

    Returns:
        DistributionService instance
    """
    return DistributionService(db)


# =============================================================================
# Type Aliases for Cleaner Route Signatures
# =============================================================================

# These type aliases use Annotated to combine the type and Depends() for cleaner route signatures.
# Instead of: service: AdminService = Depends(get_admin_service)
# Use: service: AdminServiceDep

AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
BidServiceDep = Annotated[BidService, Depends(get_bid_service)]
RunNotificationServiceDep = Annotated[RunNotificationService, Depends(get_run_notification_service)]
RunStateServiceDep = Annotated[RunStateService, Depends(get_run_state_service)]
RunServiceDep = Annotated[RunService, Depends(get_run_service)]
GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
ShoppingServiceDep = Annotated[ShoppingService, Depends(get_shopping_service)]
ReassignmentServiceDep = Annotated[ReassignmentService, Depends(get_reassignment_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
StoreServiceDep = Annotated[StoreService, Depends(get_store_service)]
DistributionServiceDep = Annotated[DistributionService, Depends(get_distribution_service)]
