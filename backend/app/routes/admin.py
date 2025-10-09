"""Admin routes for managing users, products, and stores."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..exceptions import ForbiddenError

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_admin:
        raise ForbiddenError("Admin access required")
    return current_user


@router.get("/users")
async def get_users(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all users with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    users = repo.get_all_users()

    # Filter by search query (name, email, or ID)
    if search:
        search_lower = search.lower()
        users = [u for u in users if (
            search_lower in u.name.lower() or
            search_lower in u.email.lower() or
            search_lower in str(u.id).lower()
        )]

    # Filter by verification status
    if verified is not None:
        users = [u for u in users if u.verified == verified]

    # Sort by created_at (most recent first) or by name if no created_at
    users.sort(key=lambda u: u.created_at if u.created_at else datetime.min, reverse=True)

    # Apply pagination
    paginated_users = users[offset:offset + limit]

    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "verified": u.verified,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in paginated_users
    ]


@router.post("/users/{user_id}/verify")
async def toggle_user_verification(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Toggle user verification status."""
    repo = get_repository(db)
    user = repo.get_user_by_id(UUID(user_id))

    if not user:
        from ..exceptions import NotFoundError
        raise NotFoundError("User", user_id)

    # Toggle verification
    user.verified = not user.verified

    return {
        "id": str(user.id),
        "name": user.name,
        "verified": user.verified
    }


@router.get("/products")
async def get_products(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all products with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    products = repo.get_all_products()

    # Filter by search query (name, brand, or ID)
    if search:
        search_lower = search.lower()
        products = [p for p in products if (
            search_lower in p.name.lower() or
            (p.brand and search_lower in p.brand.lower()) or
            search_lower in str(p.id).lower()
        )]

    # Filter by verification status
    if verified is not None:
        products = [p for p in products if p.verified == verified]

    # Sort by created_at (most recent first) or by name if no created_at
    products.sort(key=lambda p: p.created_at if p.created_at else datetime.min, reverse=True)

    # Apply pagination
    paginated_products = products[offset:offset + limit]

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "brand": p.brand,
            "store_name": p.store.name if p.store else None,
            "verified": p.verified,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in paginated_products
    ]


@router.post("/products/{product_id}/verify")
async def toggle_product_verification(
    product_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Toggle product verification status."""
    repo = get_repository(db)
    product = repo.get_product_by_id(UUID(product_id))

    if not product:
        from ..exceptions import NotFoundError
        raise NotFoundError("Product", product_id)

    # Toggle verification
    product.verified = not product.verified
    if product.verified:
        product.verified_by = admin_user.id
        product.verified_at = datetime.utcnow()
    else:
        product.verified_by = None
        product.verified_at = None

    return {
        "id": str(product.id),
        "name": product.name,
        "verified": product.verified
    }


@router.get("/stores")
async def get_stores(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all stores with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    stores = repo.get_all_stores()

    # Filter by search query (name, address, chain, or ID)
    if search:
        search_lower = search.lower()
        stores = [s for s in stores if (
            search_lower in s.name.lower() or
            (s.address and search_lower in s.address.lower()) or
            (s.chain and search_lower in s.chain.lower()) or
            search_lower in str(s.id).lower()
        )]

    # Filter by verification status
    if verified is not None:
        stores = [s for s in stores if s.verified == verified]

    # Sort by created_at (most recent first) or by name if no created_at
    stores.sort(key=lambda s: s.created_at if s.created_at else datetime.min, reverse=True)

    # Apply pagination
    paginated_stores = stores[offset:offset + limit]

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "address": s.address,
            "chain": s.chain,
            "verified": s.verified,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in paginated_stores
    ]


@router.post("/stores/{store_id}/verify")
async def toggle_store_verification(
    store_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Toggle store verification status."""
    repo = get_repository(db)
    store = repo.get_store_by_id(UUID(store_id))

    if not store:
        from ..exceptions import NotFoundError
        raise NotFoundError("Store", store_id)

    # Toggle verification
    store.verified = not store.verified
    if store.verified:
        store.verified_by = admin_user.id
        store.verified_at = datetime.utcnow()
    else:
        store.verified_by = None
        store.verified_at = None

    return {
        "id": str(store.id),
        "name": store.name,
        "verified": store.verified
    }
