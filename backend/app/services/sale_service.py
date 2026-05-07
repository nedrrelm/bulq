"""Sale service for managing sale business logic."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.sale_schemas import (
    SaleDetailResponse,
    SaleProductResponse,
    SaleResponse,
)
from app.core.error_codes import (
    NOT_SALE_OWNER,
    SALE_INVALID_STATE,
    SALE_NO_PRODUCTS,
    SALE_NOT_FOUND,
    SALE_PRODUCT_ALREADY_EXISTS,
    SALE_PRODUCT_NOT_FOUND,
    SELLER_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Sale, SaleProduct, User
from app.core.sale_state import SaleState, sale_state_machine
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_product_repository,
    get_sale_repository,
    get_seller_follower_repository,
    get_seller_repository,
    get_user_repository,
)

from .base_service import BaseService

logger = get_logger(__name__)


class SaleService(BaseService):
    """Service for sale operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.seller_repo = get_seller_repository(db)
        self.seller_follower_repo = get_seller_follower_repository(db)
        self.sale_repo = get_sale_repository(db)
        self.product_repo = get_product_repository(db)
        self.user_repo = get_user_repository(db)

    async def _get_seller_for_user(self, user: User):
        """Get seller profile for user, raise if not a seller."""
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller:
            raise NotFoundError(
                code=SELLER_NOT_FOUND,
                message='Seller profile not found',
                user_id=str(user.id),
            )
        return seller

    async def _get_sale_owned_by(self, sale_id: UUID, user: User) -> Sale:
        """Get a sale and verify the user owns it."""
        sale = await self.sale_repo.get_sale_by_id(sale_id)
        if not sale:
            raise NotFoundError(code=SALE_NOT_FOUND, message='Sale not found', sale_id=str(sale_id))
        seller = await self._get_seller_for_user(user)
        if sale.seller_id != seller.id:
            raise ForbiddenError(code=NOT_SALE_OWNER, message='Not the owner of this sale')
        return sale

    def _format_timestamp(self, dt) -> str | None:
        return dt.isoformat() if dt else None

    async def _format_sale_product(self, sp: SaleProduct) -> SaleProductResponse:
        product = sp.product
        if not product:
            product = await self.product_repo.get_product_by_id(sp.product_id)
        return SaleProductResponse(
            id=str(sp.id),
            product_id=str(sp.product_id),
            product_name=product.name if product else 'Unknown',
            product_brand=product.brand if product else None,
            product_unit=product.unit if product else None,
            price=str(sp.price) if sp.price is not None else None,
            available_quantity=str(sp.available_quantity)
            if sp.available_quantity is not None
            else None,
        )

    def _format_sale_response(
        self, sale: Sale, product_count: int = 0, seller_name: str | None = None
    ) -> SaleResponse:
        return SaleResponse(
            id=str(sale.id),
            seller_id=str(sale.seller_id),
            seller_name=seller_name,
            title=sale.title,
            description=sale.description,
            state=sale.state,
            product_count=product_count,
            created_at=self._format_timestamp(sale.created_at) or '',
        )

    def _format_sale_detail(
        self, sale: Sale, products: list[SaleProductResponse]
    ) -> SaleDetailResponse:
        seller_name = ''
        if sale.seller:
            seller_name = sale.seller.display_name
        return SaleDetailResponse(
            id=str(sale.id),
            seller_id=str(sale.seller_id),
            seller_name=seller_name,
            title=sale.title,
            description=sale.description,
            state=sale.state,
            invite_token=sale.invite_token,
            products=products,
            planning_at=self._format_timestamp(sale.planning_at),
            active_at=self._format_timestamp(sale.active_at),
            confirmed_at=self._format_timestamp(sale.confirmed_at),
            shopping_at=self._format_timestamp(sale.shopping_at),
            distributing_at=self._format_timestamp(sale.distributing_at),
            completed_at=self._format_timestamp(sale.completed_at),
            cancelled_at=self._format_timestamp(sale.cancelled_at),
            created_at=self._format_timestamp(sale.created_at) or '',
        )

    async def create_sale(
        self, user: User, title: str, description: str | None = None
    ) -> SaleResponse:
        """Create a new sale."""
        seller = await self._get_seller_for_user(user)

        sale = Sale(
            id=uuid.uuid4(),
            seller_id=seller.id,
            title=title.strip(),
            description=description.strip() if description else None,
            state=SaleState.PLANNING,
            invite_token=str(uuid.uuid4()),
        )
        sale = await self.sale_repo.create_sale(sale)

        logger.info(
            'Sale created',
            extra={'user_id': str(user.id), 'sale_id': str(sale.id), 'seller_id': str(seller.id)},
        )

        return self._format_sale_response(sale, product_count=0)

    async def get_my_sales(self, user: User) -> list[SaleResponse]:
        """Get all sales for the current seller."""
        seller = await self._get_seller_for_user(user)
        sales = await self.sale_repo.get_sales_by_seller(seller.id)

        result = []
        for sale in sales:
            products = await self.sale_repo.get_sale_products(sale.id)
            result.append(self._format_sale_response(sale, product_count=len(products)))
        return result

    async def get_active_sales_for_group(self, user: User, group_id: UUID) -> list[SaleResponse]:
        """Get active sales from all sellers a group follows."""
        # Verify membership
        user_groups = await self.user_repo.get_user_groups(user)
        if not any(g.id == group_id for g in user_groups):
            return []

        followers = await self.seller_follower_repo.get_followed_sellers_by_group(group_id)
        result = []
        for f in followers:
            seller = f.seller if f.seller else await self.seller_repo.get_seller_by_id(f.seller_id)
            seller_name = seller.display_name if seller else 'Unknown'
            sales = await self.sale_repo.get_sales_by_seller(f.seller_id)
            for sale in sales:
                if sale.state == SaleState.ACTIVE:
                    products = await self.sale_repo.get_sale_products(sale.id)
                    result.append(
                        self._format_sale_response(
                            sale, product_count=len(products), seller_name=seller_name
                        )
                    )
        return result

    async def get_sale_details(self, sale_id: UUID) -> SaleDetailResponse:
        """Get full sale details with products."""
        sale = await self.sale_repo.get_sale_by_id(sale_id)
        if not sale:
            raise NotFoundError(code=SALE_NOT_FOUND, message='Sale not found', sale_id=str(sale_id))

        sale_products = await self.sale_repo.get_sale_products(sale_id)
        products = [await self._format_sale_product(sp) for sp in sale_products]

        return self._format_sale_detail(sale, products)

    async def update_sale(
        self, user: User, sale_id: UUID, title: str | None = None, description: str | None = None
    ) -> SaleDetailResponse:
        """Update sale title/description (only in PLANNING state)."""
        sale = await self._get_sale_owned_by(sale_id, user)

        if not sale_state_machine.can_edit_products(SaleState(sale.state)):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Can only edit sale in planning state',
                current_state=sale.state,
            )

        fields = {}
        if title is not None:
            fields['title'] = title.strip()
        if description is not None:
            fields['description'] = description.strip() if description else None
        if fields:
            await self.sale_repo.update_sale(sale_id, **fields)

        return await self.get_sale_details(sale_id)

    async def add_product_to_sale(
        self,
        user: User,
        sale_id: UUID,
        product_id: UUID,
        price: float | None = None,
        available_quantity: float | None = None,
    ) -> SaleDetailResponse:
        """Add a product to a sale."""
        sale = await self._get_sale_owned_by(sale_id, user)

        if not sale_state_machine.can_edit_products(SaleState(sale.state)):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Can only add products in planning state',
                current_state=sale.state,
            )

        # Check product exists
        product = await self.product_repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundError(code='PRODUCT_NOT_FOUND', message='Product not found')

        # Check not already in sale
        existing = await self.sale_repo.get_sale_product(sale_id, product_id)
        if existing:
            raise BadRequestError(
                code=SALE_PRODUCT_ALREADY_EXISTS,
                message='Product already in this sale',
            )

        sp = SaleProduct(
            id=uuid.uuid4(),
            sale_id=sale_id,
            product_id=product_id,
            price=price,
            available_quantity=available_quantity,
        )
        await self.sale_repo.add_sale_product(sp)

        logger.info(
            'Product added to sale',
            extra={'sale_id': str(sale_id), 'product_id': str(product_id)},
        )

        return await self.get_sale_details(sale_id)

    async def update_sale_product(
        self,
        user: User,
        sale_id: UUID,
        product_id: UUID,
        price: float | None = None,
        available_quantity: float | None = None,
    ) -> SaleDetailResponse:
        """Update a sale product's price/quantity."""
        sale = await self._get_sale_owned_by(sale_id, user)

        if not sale_state_machine.can_edit_products(SaleState(sale.state)):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Can only edit products in planning state',
                current_state=sale.state,
            )

        sp = await self.sale_repo.get_sale_product(sale_id, product_id)
        if not sp:
            raise NotFoundError(code=SALE_PRODUCT_NOT_FOUND, message='Product not in this sale')

        fields = {}
        if price is not None:
            fields['price'] = price
        if available_quantity is not None:
            fields['available_quantity'] = available_quantity
        if fields:
            await self.sale_repo.update_sale_product(sp.id, **fields)

        return await self.get_sale_details(sale_id)

    async def remove_product_from_sale(
        self, user: User, sale_id: UUID, product_id: UUID
    ) -> SaleDetailResponse:
        """Remove a product from a sale."""
        sale = await self._get_sale_owned_by(sale_id, user)

        if not sale_state_machine.can_edit_products(SaleState(sale.state)):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Can only remove products in planning state',
                current_state=sale.state,
            )

        deleted = await self.sale_repo.delete_sale_product(sale_id, product_id)
        if not deleted:
            raise NotFoundError(code=SALE_PRODUCT_NOT_FOUND, message='Product not in this sale')

        logger.info(
            'Product removed from sale',
            extra={'sale_id': str(sale_id), 'product_id': str(product_id)},
        )

        return await self.get_sale_details(sale_id)

    async def activate_sale(self, user: User, sale_id: UUID) -> SaleDetailResponse:
        """Activate a sale (PLANNING → ACTIVE). Must have at least 1 product."""
        sale = await self._get_sale_owned_by(sale_id, user)

        sale_state_machine.validate_transition(
            SaleState(sale.state), SaleState.ACTIVE, str(sale_id)
        )

        products = await self.sale_repo.get_sale_products(sale_id)
        if not products:
            raise BadRequestError(
                code=SALE_NO_PRODUCTS,
                message='Cannot activate sale with no products',
            )

        now = datetime.now(UTC)
        await self.sale_repo.update_sale(sale_id, state=SaleState.ACTIVE, active_at=now)

        logger.info('Sale activated', extra={'sale_id': str(sale_id)})

        return await self.get_sale_details(sale_id)

    async def deactivate_sale(self, user: User, sale_id: UUID) -> SaleDetailResponse:
        """Deactivate a sale (ACTIVE → PLANNING)."""
        sale = await self._get_sale_owned_by(sale_id, user)

        sale_state_machine.validate_transition(
            SaleState(sale.state), SaleState.PLANNING, str(sale_id)
        )

        await self.sale_repo.update_sale(sale_id, state=SaleState.PLANNING)

        logger.info('Sale deactivated', extra={'sale_id': str(sale_id)})

        return await self.get_sale_details(sale_id)

    async def cancel_sale(self, user: User, sale_id: UUID) -> SaleDetailResponse:
        """Cancel a sale."""
        sale = await self._get_sale_owned_by(sale_id, user)

        if not sale_state_machine.can_cancel(SaleState(sale.state)):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Cannot cancel sale in current state',
                current_state=sale.state,
            )

        now = datetime.now(UTC)
        await self.sale_repo.update_sale(sale_id, state=SaleState.CANCELLED, cancelled_at=now)

        # Cancel all linked runs too
        from app.core.run_state import RunState
        from app.repositories import get_run_repository

        run_repo = get_run_repository(self.db)
        runs = await self.sale_repo.get_runs_for_sale(sale_id)
        for run in runs:
            if run.state not in (RunState.COMPLETED, RunState.CANCELLED):
                await run_repo.update_run_state(run.id, RunState.CANCELLED)

        logger.info('Sale cancelled', extra={'sale_id': str(sale_id)})

        return await self.get_sale_details(sale_id)

    async def confirm_sale(self, user: User, sale_id: UUID) -> SaleDetailResponse:
        """Confirm a sale. Cascades confirmation to all linked group runs."""
        from app.core.run_state import RunState
        from app.repositories import get_run_repository

        sale = await self._get_sale_owned_by(sale_id, user)

        sale_state_machine.validate_transition(
            SaleState(sale.state), SaleState.CONFIRMED, str(sale_id)
        )

        now = datetime.now(UTC)
        await self.sale_repo.update_sale(sale_id, state=SaleState.CONFIRMED, confirmed_at=now)

        # Cascade: confirm all linked runs that are in planning or active state
        run_repo = get_run_repository(self.db)
        runs = await self.sale_repo.get_runs_for_sale(sale_id)
        for run in runs:
            if run.state in (RunState.PLANNING, RunState.ACTIVE):
                await run_repo.update_run_state(run.id, RunState.CONFIRMED)
                logger.info(
                    'Run confirmed by sale cascade',
                    extra={'run_id': str(run.id), 'sale_id': str(sale_id)},
                )

        logger.info('Sale confirmed', extra={'sale_id': str(sale_id)})

        return await self.get_sale_details(sale_id)

    async def start_distributing(self, user: User, sale_id: UUID) -> SaleDetailResponse:
        """Start distributing (CONFIRMED → DISTRIBUTING)."""
        sale = await self._get_sale_owned_by(sale_id, user)

        sale_state_machine.validate_transition(
            SaleState(sale.state), SaleState.DISTRIBUTING, str(sale_id)
        )

        now = datetime.now(UTC)
        await self.sale_repo.update_sale(sale_id, state=SaleState.DISTRIBUTING, distributing_at=now)

        # Transition connected runs to shopping and create shopping list items
        from app.core.run_state import RunState
        from app.repositories import get_bid_repository, get_run_repository, get_shopping_repository

        run_repo = get_run_repository(self.db)
        bid_repo = get_bid_repository(self.db)
        shopping_repo = get_shopping_repository(self.db)
        runs = await self.sale_repo.get_runs_for_sale(sale_id)
        for run in runs:
            if run.state == RunState.CONFIRMED:
                await run_repo.update_run_state(run.id, RunState.SHOPPING)
                logger.info(
                    'Run transitioned to shopping by sale',
                    extra={'run_id': str(run.id), 'sale_id': str(sale_id)},
                )

                # Create shopping list items for each product with bids
                bids = await bid_repo.get_bids_by_run(run.id)
                product_totals: dict[UUID, float] = {}
                for bid in bids:
                    if not bid.interested_only and float(bid.quantity) > 0:
                        product_totals[bid.product_id] = product_totals.get(
                            bid.product_id, 0
                        ) + float(bid.quantity)
                for product_id, qty in product_totals.items():
                    await shopping_repo.create_shopping_list_item(run.id, product_id, qty)

        # Auto-generate distribution items
        from .sale_distribution_service import SaleDistributionService

        dist_service = SaleDistributionService(self.db)
        await dist_service.generate_distribution_items(sale_id)

        logger.info('Sale distributing started', extra={'sale_id': str(sale_id)})

        return await self.get_sale_details(sale_id)

    async def get_sale_runs(self, user: User, sale_id: UUID) -> list[dict]:
        """Get all group runs for a sale with aggregated info (seller view)."""
        from app.repositories import get_group_repository, get_run_repository

        await self._get_sale_owned_by(sale_id, user)

        runs = await self.sale_repo.get_runs_for_sale(sale_id)
        group_repo = get_group_repository(self.db)
        run_repo = get_run_repository(self.db)

        result = []
        for run in runs:
            group = await group_repo.get_group_by_id(run.group_id)
            participations = await run_repo.get_run_participations(run.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else 'Unknown'

            # Aggregate bids per product for this run
            from app.repositories import get_bid_repository

            bid_repo = get_bid_repository(self.db)
            bids = await bid_repo.get_bids_by_run(run.id)

            product_totals = {}
            for bid in bids:
                if not bid.interested_only:
                    pid = str(bid.product_id)
                    product_totals[pid] = product_totals.get(pid, 0) + float(bid.quantity)

            result.append(
                {
                    'run_id': str(run.id),
                    'group_id': str(run.group_id),
                    'group_name': group.name if group else 'Unknown',
                    'leader_name': leader_name,
                    'state': run.state,
                    'product_totals': product_totals,
                }
            )

        return result
