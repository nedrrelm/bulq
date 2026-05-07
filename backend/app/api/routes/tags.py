"""Tag routes for managing product tags."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import TagServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateTagRequest,
    SuccessResponse,
    TagBriefResponse,
    TagDetailResponse,
    TagResponse,
    TagSearchResult,
)
from app.core.error_codes import TAG_NOT_FOUND
from app.core.exceptions import NotFoundError
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/tags', tags=['tags'])


@router.get('/types', response_model=list[str])
async def get_tag_types(
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get list of valid tag types."""
    return await service.get_tag_types()


@router.get('/search', response_model=list[TagSearchResult])
async def search_tags(
    service: TagServiceDep,
    q: str = Query(..., min_length=1, description='Search query'),
    type: str | None = Query(None, description='Filter by tag type'),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
):
    """Search for tags by value."""
    return await service.search_tags(q, type, limit, offset)


@router.post('/create', response_model=TagResponse)
async def create_tag(
    request: CreateTagRequest,
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new tag."""
    tag = await service.create_tag(
        value=request.value,
        tag_type=request.type,
        user_id=current_user.id,
    )

    return TagResponse(
        id=str(tag.id),
        value=tag.value,
        type=tag.type,
        verified=tag.verified,
        created_at=tag.created_at.isoformat() if tag.created_at else None,
    )


@router.get('/{tag_id}', response_model=TagDetailResponse)
async def get_tag_details(
    tag_id: str,
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get detailed tag information including products."""
    result = await service.get_tag_details(validate_uuid(tag_id, 'Tag'))
    if not result:
        raise NotFoundError(code=TAG_NOT_FOUND, message='Tag not found', tag_id=tag_id)
    return result


@router.post('/{tag_id}/products/{product_id}', response_model=SuccessResponse)
async def add_tag_to_product(
    tag_id: str,
    product_id: str,
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Add a tag to a product."""
    return await service.add_tag_to_product(
        validate_uuid(product_id, 'Product'),
        validate_uuid(tag_id, 'Tag'),
    )


@router.delete('/{tag_id}/products/{product_id}', response_model=SuccessResponse)
async def remove_tag_from_product(
    tag_id: str,
    product_id: str,
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Remove a tag from a product."""
    return await service.remove_tag_from_product(
        validate_uuid(product_id, 'Product'),
        validate_uuid(tag_id, 'Tag'),
    )


@router.get('/product/{product_id}', response_model=list[TagBriefResponse])
async def get_product_tags(
    product_id: str,
    service: TagServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get all tags for a product."""
    return await service.get_tags_for_product(validate_uuid(product_id, 'Product'))
