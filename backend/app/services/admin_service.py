"""Admin service for managing users, products, and stores."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.api.schemas import (
    AdminProductResponse,
    AdminStoreResponse,
    AdminUserResponse,
    VerificationToggleResponse,
)
from app.core.error_codes import (
    CANNOT_DELETE_ADMIN_USER,
    CANNOT_DELETE_OWN_ACCOUNT,
    CANNOT_MERGE_ADMIN_USER,
    CANNOT_MERGE_SAME_PRODUCT,
    CANNOT_MERGE_SAME_STORE,
    CANNOT_MERGE_SAME_USER,
    CANNOT_REMOVE_OWN_ADMIN_STATUS,
    PRODUCT_HAS_ACTIVE_BIDS,
    PRODUCT_NOT_FOUND,
    STORE_HAS_ACTIVE_RUNS,
    STORE_NOT_FOUND,
    USER_NOT_FOUND,
    USERS_HAVE_CONFLICTING_PARTICIPATIONS,
)
from app.core.exceptions import NotFoundError
from app.core.models import User
from app.core.success_codes import (
    PRODUCT_DELETED,
    PRODUCT_UNVERIFIED,
    PRODUCT_VERIFIED,
    PRODUCTS_MERGED,
    STORE_DELETED,
    STORE_UNVERIFIED,
    STORE_VERIFIED,
    STORES_MERGED,
    USER_DELETED,
    USER_UNVERIFIED,
    USER_VERIFIED,
    USERS_MERGED,
)

from .base_service import BaseService


class AdminService(BaseService):
    """Service for admin operations."""

    def get_users(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdminUserResponse]:
        """Get all users with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, username, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of user dictionaries with formatted data
        """
        users = self.repo.get_all_users()

        # Filter by search query (name, username, or ID)
        if search:
            search_lower = search.lower()
            users = [
                u
                for u in users
                if (
                    search_lower in u.name.lower()
                    or search_lower in u.username.lower()
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
            AdminUserResponse(
                id=str(u.id),
                name=u.name,
                username=u.username,
                verified=u.verified,
                is_admin=u.is_admin,
                created_at=u.created_at.isoformat() if u.created_at else None,
            )
            for u in paginated_users
        ]

    def toggle_user_verification(
        self, user_id: UUID, admin_user: User
    ) -> VerificationToggleResponse:
        """Toggle user verification status.

        Args:
            user_id: ID of user to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            VerificationToggleResponse with updated user info

        Raises:
            NotFoundError: If user not found
        """
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(code=USER_NOT_FOUND, message='User not found', user_id=str(user_id))

        # Toggle verification
        user.verified = not user.verified

        return VerificationToggleResponse(
            code=USER_VERIFIED if user.verified else USER_UNVERIFIED,
            id=str(user.id),
            verified=user.verified,
        )

    def get_products(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdminProductResponse]:
        """Get all products with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, brand, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of AdminProductResponse with formatted data
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
            AdminProductResponse(
                id=str(p.id),
                name=p.name,
                brand=p.brand,
                unit=p.unit,
                verified=p.verified if p.verified is not None else False,
                created_at=p.created_at.isoformat() if p.created_at else None,
            )
            for p in paginated_products
        ]

    def toggle_product_verification(
        self, product_id: UUID, admin_user: User
    ) -> VerificationToggleResponse:
        """Toggle product verification status.

        Args:
            product_id: ID of product to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            VerificationToggleResponse with updated product info

        Raises:
            NotFoundError: If product not found
        """
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND, message='Product not found', product_id=str(product_id)
            )

        # Toggle verification
        product.verified = not product.verified
        if product.verified:
            product.verified_by = admin_user.id
            product.verified_at = datetime.now(UTC)
        else:
            product.verified_by = None
            product.verified_at = None

        return VerificationToggleResponse(
            code=PRODUCT_VERIFIED if product.verified else PRODUCT_UNVERIFIED,
            id=str(product.id),
            verified=product.verified,
        )

    def get_stores(
        self,
        search: str | None = None,
        verified: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdminStoreResponse]:
        """Get all stores with optional search and filtering (paginated).

        Args:
            search: Optional search query for name, address, chain, or ID
            verified: Optional filter by verification status
            limit: Maximum number of results (max 100)
            offset: Number of results to skip

        Returns:
            List of AdminStoreResponse with formatted data
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
            AdminStoreResponse(
                id=str(s.id),
                name=s.name,
                address=s.address,
                chain=s.chain,
                verified=s.verified if s.verified is not None else False,
                created_at=s.created_at.isoformat() if s.created_at else None,
            )
            for s in paginated_stores
        ]

    def toggle_store_verification(
        self, store_id: UUID, admin_user: User
    ) -> VerificationToggleResponse:
        """Toggle store verification status.

        Args:
            store_id: ID of store to toggle verification for
            admin_user: Admin user performing the action

        Returns:
            VerificationToggleResponse with updated store info

        Raises:
            NotFoundError: If store not found
        """
        store = self.repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Store not found', store_id=str(store_id)
            )

        # Toggle verification
        store.verified = not store.verified
        if store.verified:
            store.verified_by = admin_user.id
            store.verified_at = datetime.now(UTC)
        else:
            store.verified_by = None
            store.verified_at = None

        return VerificationToggleResponse(
            code=STORE_VERIFIED if store.verified else STORE_UNVERIFIED,
            id=str(store.id),
            verified=store.verified,
        )

    # ==================== Update Methods ====================

    def update_product(
        self, product_id: UUID, data: dict, admin_user: User
    ) -> AdminProductResponse:
        """Update product fields.

        Args:
            product_id: ID of product to update
            data: Dictionary with fields to update (name, brand, unit)
            admin_user: Admin user performing the action

        Returns:
            AdminProductResponse with updated product info

        Raises:
            NotFoundError: If product not found
        """
        product = self.repo.update_product(product_id, **data)
        if not product:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND, message='Product not found', product_id=str(product_id)
            )

        return AdminProductResponse(
            id=str(product.id),
            name=product.name,
            brand=product.brand,
            unit=product.unit,
            verified=product.verified,
            created_at=product.created_at.isoformat() if product.created_at else None,
        )

    def update_store(self, store_id: UUID, data: dict, admin_user: User) -> AdminStoreResponse:
        """Update store fields.

        Args:
            store_id: ID of store to update
            data: Dictionary with fields to update (name, address, chain, opening_hours)
            admin_user: Admin user performing the action

        Returns:
            AdminStoreResponse with updated store info

        Raises:
            NotFoundError: If store not found
        """
        store = self.repo.update_store(store_id, **data)
        if not store:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Store not found', store_id=str(store_id)
            )

        return AdminStoreResponse(
            id=str(store.id),
            name=store.name,
            address=store.address,
            chain=store.chain,
            verified=store.verified,
            created_at=store.created_at.isoformat() if store.created_at else None,
        )

    def update_user(self, user_id: UUID, data: dict, admin_user: User) -> AdminUserResponse:
        """Update user fields.

        Args:
            user_id: ID of user to update
            data: Dictionary with fields to update (name, username, is_admin, verified)
            admin_user: Admin user performing the action

        Returns:
            AdminUserResponse with updated user info

        Raises:
            NotFoundError: If user not found
            ForbiddenError: If trying to remove own admin status
        """
        # Prevent admin from removing own admin status
        if user_id == admin_user.id and 'is_admin' in data and not data['is_admin']:
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError(
                code=CANNOT_REMOVE_OWN_ADMIN_STATUS,
                message='Cannot remove your own admin status',
                user_id=str(user_id),
            )

        user = self.repo.update_user(user_id, **data)
        if not user:
            raise NotFoundError(code=USER_NOT_FOUND, message='User not found', user_id=str(user_id))

        return AdminUserResponse(
            id=str(user.id),
            name=user.name,
            username=user.username,
            verified=user.verified,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )

    # ==================== Merge Methods ====================

    def merge_products(self, source_id: UUID, target_id: UUID, admin_user: User) -> dict[str, Any]:
        """Merge one product into another.

        All bids, availabilities, and shopping list items from source will be moved to target.
        Source product will be deleted.

        Args:
            source_id: ID of product to merge from (will be deleted)
            target_id: ID of product to merge into (will be kept)
            admin_user: Admin user performing the action

        Returns:
            MergeResponse with affected records count

        Raises:
            NotFoundError: If either product not found
            BadRequestError: If trying to merge product into itself
        """
        from app.core.exceptions import BadRequestError

        # Validate products exist
        source = self.repo.get_product_by_id(source_id)
        target = self.repo.get_product_by_id(target_id)

        if not source:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND,
                message='Source product not found',
                product_id=str(source_id),
            )
        if not target:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND,
                message='Target product not found',
                product_id=str(target_id),
            )
        if source_id == target_id:
            raise BadRequestError(
                code=CANNOT_MERGE_SAME_PRODUCT,
                message='Cannot merge product into itself',
                product_id=str(source_id),
            )

        # Move all references
        bids_count = self.repo.bulk_update_product_bids(source_id, target_id)
        avails_count = self.repo.bulk_update_product_availabilities(source_id, target_id)
        items_count = self.repo.bulk_update_shopping_list_items(source_id, target_id)

        # Delete source product
        self.repo.delete_product(source_id)

        total_affected = bids_count + avails_count + items_count

        from app.api.schemas import MergeResponse

        return MergeResponse(
            code=PRODUCTS_MERGED,
            source_id=str(source_id),
            target_id=str(target_id),
            affected_records=total_affected,
            details={'source_name': source.name, 'target_name': target.name},
        )

    def merge_stores(self, source_id: UUID, target_id: UUID, admin_user: User) -> dict[str, Any]:
        """Merge one store into another.

        All runs and product availabilities from source will be moved to target.
        Source store will be deleted.

        Args:
            source_id: ID of store to merge from (will be deleted)
            target_id: ID of store to merge into (will be kept)
            admin_user: Admin user performing the action

        Returns:
            MergeResponse with affected records count

        Raises:
            NotFoundError: If either store not found
            BadRequestError: If trying to merge store into itself
        """
        from app.core.exceptions import BadRequestError

        # Validate stores exist
        source = self.repo.get_store_by_id(source_id)
        target = self.repo.get_store_by_id(target_id)

        if not source:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Source store not found', store_id=str(source_id)
            )
        if not target:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Target store not found', store_id=str(target_id)
            )
        if source_id == target_id:
            raise BadRequestError(
                code=CANNOT_MERGE_SAME_STORE,
                message='Cannot merge store into itself',
                store_id=str(source_id),
            )

        # Move all references
        runs_count = self.repo.bulk_update_runs(source_id, target_id)
        avails_count = self.repo.bulk_update_store_availabilities(source_id, target_id)

        # Delete source store
        self.repo.delete_store(source_id)

        total_affected = runs_count + avails_count

        from app.api.schemas import MergeResponse

        return MergeResponse(
            code=STORES_MERGED,
            source_id=str(source_id),
            target_id=str(target_id),
            affected_records=total_affected,
            details={'source_name': source.name, 'target_name': target.name},
        )

    def merge_users(self, source_id: UUID, target_id: UUID, admin_user: User) -> dict[str, Any]:
        """Merge one user into another.

        All data from source will be moved to target (participations, groups, created/verified items, notifications).
        Source user will be deleted.

        Args:
            source_id: ID of user to merge from (will be deleted)
            target_id: ID of user to merge into (will be kept)
            admin_user: Admin user performing the action

        Returns:
            MergeResponse with affected records count

        Raises:
            NotFoundError: If either user not found
            BadRequestError: If trying to merge user into itself, or source is admin, or users have conflicting participations
        """
        from app.core.exceptions import BadRequestError

        # Validate users exist
        source = self.repo.get_user_by_id(source_id)
        target = self.repo.get_user_by_id(target_id)

        if not source:
            raise NotFoundError(
                code=USER_NOT_FOUND,
                message='Source user not found',
                user_id=str(source_id),
            )
        if not target:
            raise NotFoundError(
                code=USER_NOT_FOUND,
                message='Target user not found',
                user_id=str(target_id),
            )
        if source_id == target_id:
            raise BadRequestError(
                code=CANNOT_MERGE_SAME_USER,
                message='Cannot merge user into itself',
                user_id=str(source_id),
            )

        # Prevent merging admin users
        if source.is_admin:
            raise BadRequestError(
                code=CANNOT_MERGE_ADMIN_USER,
                message='Cannot merge admin users',
                user_id=str(source_id),
            )

        # Check for conflicting run participations
        overlapping_runs = self.repo.check_overlapping_run_participations(source_id, target_id)
        if overlapping_runs:
            raise BadRequestError(
                code=USERS_HAVE_CONFLICTING_PARTICIPATIONS,
                message=f'Users participate in {len(overlapping_runs)} common run(s). Cannot merge.',
                overlapping_run_count=len(overlapping_runs),
                source_user_id=str(source_id),
                target_user_id=str(target_id),
            )

        # Move all references
        participations_count = self.repo.bulk_update_run_participations(source_id, target_id)
        groups_count = self.repo.bulk_update_group_creator(source_id, target_id)
        products_created = self.repo.bulk_update_product_creator(source_id, target_id)
        products_verified = self.repo.bulk_update_product_verifier(source_id, target_id)
        stores_created = self.repo.bulk_update_store_creator(source_id, target_id)
        stores_verified = self.repo.bulk_update_store_verifier(source_id, target_id)
        availabilities_count = self.repo.bulk_update_product_availability_creator(source_id, target_id)
        notifications_count = self.repo.bulk_update_notifications(source_id, target_id)
        reassignments_from = self.repo.bulk_update_reassignment_from_user(source_id, target_id)
        reassignments_to = self.repo.bulk_update_reassignment_to_user(source_id, target_id)
        admin_status_count = self.repo.transfer_group_admin_status(source_id, target_id)

        # Delete source user (group_membership will cascade delete)
        self.repo.delete_user(source_id)

        total_affected = (
            participations_count
            + groups_count
            + products_created
            + products_verified
            + stores_created
            + stores_verified
            + availabilities_count
            + notifications_count
            + reassignments_from
            + reassignments_to
            + admin_status_count
        )

        from app.api.schemas import MergeResponse

        return MergeResponse(
            code=USERS_MERGED,
            source_id=str(source_id),
            target_id=str(target_id),
            affected_records=total_affected,
            details={'source_name': source.name, 'target_name': target.name},
        )

    # ==================== Delete Methods ====================

    def delete_product(self, product_id: UUID, admin_user: User) -> dict[str, str]:
        """Delete a product.

        Args:
            product_id: ID of product to delete
            admin_user: Admin user performing the action

        Returns:
            DeleteResponse with success message

        Raises:
            NotFoundError: If product not found
            BadRequestError: If product has bids (cannot delete)
        """
        from app.core.exceptions import BadRequestError

        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND, message='Product not found', product_id=str(product_id)
            )

        # Check if product has any bids
        bid_count = self.repo.count_product_bids(product_id)
        if bid_count > 0:
            raise BadRequestError(
                code=PRODUCT_HAS_ACTIVE_BIDS,
                message=f'Cannot delete product with {bid_count} associated bids. Consider merging instead.',
                bid_count=bid_count,
                product_id=str(product_id),
            )

        # Delete the product
        self.repo.delete_product(product_id)

        from app.api.schemas import DeleteResponse

        return DeleteResponse(
            code=PRODUCT_DELETED,
            deleted_id=str(product_id),
            details={'product_name': product.name},
        )

    def delete_store(self, store_id: UUID, admin_user: User) -> dict[str, str]:
        """Delete a store.

        Args:
            store_id: ID of store to delete
            admin_user: Admin user performing the action

        Returns:
            DeleteResponse with success message

        Raises:
            NotFoundError: If store not found
            BadRequestError: If store has runs (cannot delete)
        """
        from app.core.exceptions import BadRequestError

        store = self.repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Store not found', store_id=str(store_id)
            )

        # Check if store has any runs
        run_count = self.repo.count_store_runs(store_id)
        if run_count > 0:
            raise BadRequestError(
                code=STORE_HAS_ACTIVE_RUNS,
                message=f'Cannot delete store with {run_count} associated runs. Consider merging instead.',
                run_count=run_count,
                store_id=str(store_id),
            )

        # Delete the store
        self.repo.delete_store(store_id)

        from app.api.schemas import DeleteResponse

        return DeleteResponse(
            code=STORE_DELETED,
            deleted_id=str(store_id),
            details={'store_name': store.name},
        )

    def delete_user(self, user_id: UUID, admin_user: User) -> dict[str, str]:
        """Delete a user.

        Args:
            user_id: ID of user to delete
            admin_user: Admin user performing the action

        Returns:
            DeleteResponse with success message

        Raises:
            NotFoundError: If user not found
            ForbiddenError: If trying to delete self or another admin
        """
        from app.core.exceptions import ForbiddenError

        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(code=USER_NOT_FOUND, message='User not found', user_id=str(user_id))

        # Prevent self-deletion
        if user_id == admin_user.id:
            raise ForbiddenError(
                code=CANNOT_DELETE_OWN_ACCOUNT,
                message='Cannot delete your own account',
                user_id=str(user_id),
            )

        # Prevent deleting other admins
        if user.is_admin:
            raise ForbiddenError(
                code=CANNOT_DELETE_ADMIN_USER,
                message='Cannot delete admin users',
                user_id=str(user_id),
            )

        # Delete the user
        self.repo.delete_user(user_id)

        from app.api.schemas import DeleteResponse

        return DeleteResponse(
            code=USER_DELETED,
            deleted_id=str(user_id),
            details={'user_name': user.name},
        )
