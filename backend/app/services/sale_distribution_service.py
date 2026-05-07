"""Sale distribution service for managing seller-to-group handover."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import (
    NOT_SALE_OWNER,
    SALE_INVALID_STATE,
    SALE_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import SaleDistributionItem, User
from app.core.run_state import RunState
from app.core.sale_state import SaleState, sale_state_machine
from app.events.domain_events import SaleDistributionUpdatedEvent
from app.events.event_bus import event_bus
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_bid_repository,
    get_group_repository,
    get_product_repository,
    get_run_repository,
    get_sale_repository,
    get_seller_repository,
)

from .base_service import BaseService

logger = get_logger(__name__)


class SaleDistributionService(BaseService):
    """Service for seller distribution operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.seller_repo = get_seller_repository(db)
        self.sale_repo = get_sale_repository(db)
        self.run_repo = get_run_repository(db)
        self.bid_repo = get_bid_repository(db)
        self.group_repo = get_group_repository(db)
        self.product_repo = get_product_repository(db)

    async def _verify_sale_owner(self, sale_id: UUID, user: User):
        """Verify user owns the sale."""
        sale = await self.sale_repo.get_sale_by_id(sale_id)
        if not sale:
            raise NotFoundError(code=SALE_NOT_FOUND, message='Sale not found')
        seller = await self.seller_repo.get_seller_by_user_id(user.id)
        if not seller or sale.seller_id != seller.id:
            raise ForbiddenError(code=NOT_SALE_OWNER, message='Not the owner of this sale')
        return sale

    async def generate_distribution_items(self, sale_id: UUID) -> list[dict]:
        """Generate distribution items by aggregating bids per run per product."""
        from app.repositories.memory.storage import MemoryStorage

        runs = await self.sale_repo.get_runs_for_sale(sale_id)
        items = []

        for run in runs:
            if run.state in (RunState.CANCELLED,):
                continue

            bids = await self.bid_repo.get_bids_by_run(run.id)

            # Aggregate bids per product
            product_totals: dict[UUID, float] = {}
            for bid in bids:
                if not bid.interested_only and float(bid.quantity) > 0:
                    product_totals[bid.product_id] = product_totals.get(bid.product_id, 0) + float(
                        bid.quantity
                    )

            for product_id, quantity in product_totals.items():
                item = SaleDistributionItem(
                    id=uuid.uuid4(),
                    sale_id=sale_id,
                    run_id=run.id,
                    product_id=product_id,
                    quantity=quantity,
                    is_handed_over=False,
                )
                # Store in memory
                storage = MemoryStorage()
                storage.sale_distribution_items[item.id] = item
                items.append(item)

        return items

    async def get_sale_distribution(self, user: User, sale_id: UUID) -> dict:
        """Get distribution view: per-product, per-group breakdown."""
        sale = await self._verify_sale_owner(sale_id, user)

        if sale.state not in (SaleState.DISTRIBUTING, SaleState.COMPLETED):
            raise BadRequestError(
                code=SALE_INVALID_STATE,
                message='Distribution is only available in distributing or completed state',
            )

        from app.repositories.memory.storage import MemoryStorage

        storage = MemoryStorage()
        all_items = [
            item for item in storage.sale_distribution_items.values() if item.sale_id == sale_id
        ]

        # If no items exist yet, generate them
        if not all_items:
            all_items = await self.generate_distribution_items(sale_id)

        # Build per-product breakdown
        products_map: dict[UUID, dict] = {}
        for item in all_items:
            pid = item.product_id
            if pid not in products_map:
                product = await self.product_repo.get_product_by_id(pid)
                products_map[pid] = {
                    'product_id': str(pid),
                    'product_name': product.name if product else 'Unknown',
                    'product_unit': product.unit if product else None,
                    'total_quantity': 0,
                    'groups': [],
                }

            # Get group info for this run
            run = await self.run_repo.get_run_by_id(item.run_id)
            group = await self.group_repo.get_group_by_id(run.group_id) if run else None

            # Get leader name
            leader_name = 'Unknown'
            if run:
                participations = await self.run_repo.get_run_participations(run.id)
                leader = next((p for p in participations if p.is_leader), None)
                if leader and leader.user:
                    leader_name = leader.user.name

            products_map[pid]['total_quantity'] += float(item.quantity)
            products_map[pid]['groups'].append(
                {
                    'item_id': str(item.id),
                    'run_id': str(item.run_id),
                    'group_id': str(run.group_id) if run else '',
                    'group_name': group.name if group else 'Unknown',
                    'leader_name': leader_name,
                    'quantity': float(item.quantity),
                    'is_handed_over': item.is_handed_over,
                    'handed_over_at': item.handed_over_at.isoformat()
                    if item.handed_over_at
                    else None,
                }
            )

        total_items = len(all_items)
        handed_over_count = sum(1 for item in all_items if item.is_handed_over)

        return {
            'sale_id': str(sale_id),
            'state': sale.state,
            'products': list(products_map.values()),
            'total_items': total_items,
            'handed_over_count': handed_over_count,
        }

    async def mark_handed_over(self, user: User, sale_id: UUID, item_id: UUID) -> dict:
        """Mark a distribution item as handed over."""
        await self._verify_sale_owner(sale_id, user)

        from app.repositories.memory.storage import MemoryStorage

        storage = MemoryStorage()
        item = storage.sale_distribution_items.get(item_id)
        if not item or item.sale_id != sale_id:
            raise NotFoundError(
                code='DISTRIBUTION_ITEM_NOT_FOUND', message='Distribution item not found'
            )

        item.is_handed_over = not item.is_handed_over
        item.handed_over_at = datetime.now(UTC) if item.is_handed_over else None

        logger.info(
            'Distribution item toggled',
            extra={'item_id': str(item_id), 'is_handed_over': item.is_handed_over},
        )
        event_bus.emit(
            SaleDistributionUpdatedEvent(
                sale_id=sale_id,
                item_id=item_id,
                is_handed_over=item.is_handed_over,
            )
        )

        # Mark/unmark the corresponding shopping list item as purchased
        from app.repositories import get_sale_repository, get_shopping_repository

        shopping_repo = get_shopping_repository(self.db)
        sale_repo = get_sale_repository(self.db)
        shopping_items = await shopping_repo.get_shopping_list_items(item.run_id)
        for si in shopping_items:
            if si.product_id == item.product_id:
                if item.is_handed_over:
                    # Get sale product price
                    sale_product = await sale_repo.get_sale_product(sale_id, item.product_id)
                    price = float(sale_product.price) if sale_product and sale_product.price else 0
                    si.is_purchased = True
                    si.purchased_quantity = float(item.quantity)
                    si.purchased_price_per_unit = price
                    si.purchased_total = price * float(item.quantity)
                    si.purchased_at = datetime.now(UTC)
                else:
                    si.is_purchased = False
                    si.purchased_quantity = None
                    si.purchased_price_per_unit = None
                    si.purchased_total = None
                    si.purchased_at = None
                break

        # Check if all items for this run are handed over → transition run shopping → distributing
        run_items = [
            i
            for i in storage.sale_distribution_items.values()
            if i.sale_id == sale_id and i.run_id == item.run_id
        ]
        all_handed = all(i.is_handed_over for i in run_items)
        if all_handed:
            run = await self.run_repo.get_run_by_id(item.run_id)
            if run and run.state == RunState.SHOPPING:
                await self.run_repo.update_run_state(run.id, RunState.DISTRIBUTING)
                logger.info(
                    'Run auto-transitioned to distributing',
                    extra={'run_id': str(item.run_id), 'sale_id': str(sale_id)},
                )

        return await self.get_sale_distribution(user, sale_id)

    async def complete_sale(self, user: User, sale_id: UUID) -> dict:
        """Complete the sale (DISTRIBUTING → COMPLETED)."""
        sale = await self._verify_sale_owner(sale_id, user)

        sale_state_machine.validate_transition(
            SaleState(sale.state), SaleState.COMPLETED, str(sale_id)
        )

        now = datetime.now(UTC)
        await self.sale_repo.update_sale(sale_id, state=SaleState.COMPLETED, completed_at=now)

        logger.info('Sale completed', extra={'sale_id': str(sale_id)})

        return {'sale_id': str(sale_id), 'state': SaleState.COMPLETED}
