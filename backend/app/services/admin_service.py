"""Admin service for managing users, products, and stores."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ..exceptions import NotFoundError
from ..models import User
from .base_service import BaseService


class AdminService(BaseService):
    """Service for admin operations."""

    def get_users(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get all users with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, email, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of user dictionaries with formatted data
        """
        users = self.repo.get_all_users()

        # Filter by search query (name, email, or ID)
        if search:
            search_lower = search.lower()
            users = [
                u
                for u in users
                if (
                    search_lower in u.name.lower()
                    or search_lower in u.email.lower()
                    or search_lower in str(u.id).lower()
                )
            ]

        # Filter by verification status
        if verified is not None:
            users = [u for u in users if u.verified == verified]

        # Sort by created_at (most recent first) or by name if no created_at
        users.sort(key=lambda u: u.created_at if u.created_at else datetime.min, reverse=True)

        # Apply pagination
        paginated_users = users[offset : offset + limit]

        return [
            {
                'id': str(u.id),
                'name': u.name,
                'email': u.email,
                'verified': u.verified,
                'is_admin': u.is_admin,
                'created_at': u.created_at.isoformat() if u.created_at else None,
            }
            for u in paginated_users
        ]

    def toggle_user_verification(self, user_id: UUID, admin_user: User) -> dict[str, Any]:
        """
        Toggle user verification status.

        Args:
            user_id: ID of user to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            Dict with updated user info

        Raises:
            NotFoundError: If user not found
        """
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError('User', str(user_id))

        # Toggle verification
        user.verified = not user.verified

        return {
            'id': str(user.id),
            'verified': user.verified,
            'message': f'User verification {"enabled" if user.verified else "disabled"}',
        }

    def get_products(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get all products with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, brand, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of product dictionaries with formatted data
        """
        products = self.repo.get_all_products()

        # Filter by search query (name, brand, or ID)
        if search:
            search_lower = search.lower()
            products = [
                p
                for p in products
                if (
                    search_lower in p.name.lower()
                    or (p.brand and search_lower in p.brand.lower())
                    or search_lower in str(p.id).lower()
                )
            ]

        # Filter by verification status
        if verified is not None:
            products = [p for p in products if p.verified == verified]

        # Sort by created_at (most recent first) or by name if no created_at
        products.sort(key=lambda p: p.created_at if p.created_at else datetime.min, reverse=True)

        # Apply pagination
        paginated_products = products[offset : offset + limit]

        return [
            {
                'id': str(p.id),
                'name': p.name,
                'brand': p.brand,
                'store_name': p.store.name if p.store else None,
                'verified': p.verified,
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }
            for p in paginated_products
        ]

    def toggle_product_verification(self, product_id: UUID, admin_user: User) -> dict[str, Any]:
        """
        Toggle product verification status.

        Args:
            product_id: ID of product to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            Dict with updated product info

        Raises:
            NotFoundError: If product not found
        """
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundError('Product', str(product_id))

        # Toggle verification
        product.verified = not product.verified
        if product.verified:
            product.verified_by = admin_user.id
            product.verified_at = datetime.now(UTC)
        else:
            product.verified_by = None
            product.verified_at = None

        return {
            'id': str(product.id),
            'verified': product.verified,
            'message': f'Product verification {"enabled" if product.verified else "disabled"}',
        }

    def get_stores(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get all stores with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, address, chain, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of store dictionaries with formatted data
        """
        stores = self.repo.get_all_stores()

        # Filter by search query (name, address, chain, or ID)
        if search:
            search_lower = search.lower()
            stores = [
                s
                for s in stores
                if (
                    search_lower in s.name.lower()
                    or (s.address and search_lower in s.address.lower())
                    or (s.chain and search_lower in s.chain.lower())
                    or search_lower in str(s.id).lower()
                )
            ]

        # Filter by verification status
        if verified is not None:
            stores = [s for s in stores if s.verified == verified]

        # Sort by created_at (most recent first) or by name if no created_at
        stores.sort(key=lambda s: s.created_at if s.created_at else datetime.min, reverse=True)

        # Apply pagination
        paginated_stores = stores[offset : offset + limit]

        return [
            {
                'id': str(s.id),
                'name': s.name,
                'address': s.address,
                'chain': s.chain,
                'verified': s.verified,
                'created_at': s.created_at.isoformat() if s.created_at else None,
            }
            for s in paginated_stores
        ]

    def toggle_store_verification(self, store_id: UUID, admin_user: User) -> dict[str, Any]:
        """
        Toggle store verification status.

        Args:
            store_id: ID of store to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            Dict with updated store info

        Raises:
            NotFoundError: If store not found
        """
        store = self.repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError('Store', str(store_id))

        # Toggle verification
        store.verified = not store.verified
        if store.verified:
            store.verified_by = admin_user.id
            store.verified_at = datetime.now(UTC)
        else:
            store.verified_by = None
            store.verified_at = None

        return {
            'id': str(store.id),
            'verified': store.verified,
            'message': f'Store verification {"enabled" if store.verified else "disabled"}',
        }
