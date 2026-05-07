"""Seller routes for managing seller profiles."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import SellerServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateSellerRequest,
    SellerPreviewResponse,
    SellerPublicResponse,
    SellerResponse,
    SellerSearchResult,
    UpdateSellerRequest,
)
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/sellers', tags=['sellers'])


@router.post('', response_model=SellerResponse)
async def create_seller(
    request: CreateSellerRequest,
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a seller profile for the current user."""
    return await service.create_seller(current_user, request.display_name, request.description)


@router.get('/me', response_model=SellerResponse | None)
async def get_my_seller_profile(
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get the current user's seller profile."""
    return await service.get_my_seller_profile(current_user)


@router.patch('/me', response_model=SellerResponse)
async def update_my_seller_profile(
    request: UpdateSellerRequest,
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update the current user's seller profile."""
    return await service.update_seller(current_user, request.display_name, request.description)


@router.patch('/me/joining', response_model=SellerResponse)
async def toggle_joining_allowed(
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Toggle whether new groups can follow this seller."""
    return await service.toggle_joining_allowed(current_user)


@router.patch('/me/searchable', response_model=SellerResponse)
async def toggle_searchable(
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Toggle whether this seller appears in search results."""
    return await service.toggle_searchable(current_user)


@router.post('/me/regenerate-token', response_model=SellerResponse)
async def regenerate_invite_token(
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Regenerate the seller's invite token."""
    return await service.regenerate_invite_token(current_user)


@router.get('/search', response_model=list[SellerSearchResult])
async def search_sellers(
    service: SellerServiceDep,
    q: str = Query(..., min_length=2, description='Search query'),
    current_user: User = Depends(require_auth),
):
    """Search for sellers by name."""
    return await service.search_sellers(q)


@router.get('/invite/{invite_token}', response_model=SellerPreviewResponse)
async def get_seller_by_invite_token(
    invite_token: str,
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Preview a seller by invite token."""
    return await service.get_seller_by_invite_token(invite_token)


@router.get('/{seller_id}', response_model=SellerPublicResponse)
async def get_seller(
    seller_id: str,
    service: SellerServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get a seller's public profile."""
    seller_uuid = validate_uuid(seller_id, 'Seller')
    return await service.get_seller_by_id(seller_uuid)
