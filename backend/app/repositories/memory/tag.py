"""Memory tag repository implementation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.models import Tag
from app.repositories.abstract.tag import AbstractTagRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryTagRepository(AbstractTagRepository):
    """Memory implementation of tag repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def get_tag_by_id(self, tag_id: UUID) -> Tag | None:
        return self.storage.tags.get(tag_id)

    async def get_all_tags(self) -> list[Tag]:
        return sorted(
            self.storage.tags.values(),
            key=lambda t: (t.type or '', t.value or ''),
        )

    async def search_tags(
        self,
        query: str,
        tag_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Tag]:
        query_lower = query.lower()
        results = [
            tag
            for tag in self.storage.tags.values()
            if query_lower in tag.value.lower() and (tag_type is None or tag.type == tag_type)
        ]
        return results[offset : offset + limit]

    async def get_tag_by_value_and_type(self, value: str, tag_type: str) -> Tag | None:
        for tag in self.storage.tags.values():
            if tag.value == value and tag.type == tag_type:
                return tag
        return None

    async def create_tag(
        self,
        value: str,
        tag_type: str,
        created_by: UUID | None = None,
    ) -> Tag:
        tag = Tag(
            id=uuid4(),
            value=value,
            type=tag_type,
            verified=False,
            created_at=datetime.now(UTC),
            created_by=created_by,
        )
        self.storage.tags[tag.id] = tag
        return tag

    async def update_tag(self, tag_id: UUID, **fields) -> Tag | None:
        tag = self.storage.tags.get(tag_id)
        if not tag:
            return None

        for key, value in fields.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        return tag

    async def delete_tag(self, tag_id: UUID) -> bool:
        if tag_id not in self.storage.tags:
            return False

        # Remove all product-tag links
        to_remove = [key for key in self.storage.product_tags if key[1] == tag_id]
        for key in to_remove:
            del self.storage.product_tags[key]

        del self.storage.tags[tag_id]
        return True

    async def get_tags_by_product(self, product_id: UUID) -> list[Tag]:
        tag_ids = [tag_id for (pid, tag_id) in self.storage.product_tags if pid == product_id]
        tags = [self.storage.tags[tid] for tid in tag_ids if tid in self.storage.tags]
        return sorted(tags, key=lambda t: (t.type or '', t.value or ''))

    async def add_tag_to_product(self, product_id: UUID, tag_id: UUID) -> None:
        self.storage.product_tags[(product_id, tag_id)] = True

    async def remove_tag_from_product(self, product_id: UUID, tag_id: UUID) -> None:
        self.storage.product_tags.pop((product_id, tag_id), None)

    async def is_tag_on_product(self, product_id: UUID, tag_id: UUID) -> bool:
        return (product_id, tag_id) in self.storage.product_tags

    async def get_products_by_tag(self, tag_id: UUID, limit: int = 50, offset: int = 0) -> list:
        product_ids = [pid for (pid, tid) in self.storage.product_tags if tid == tag_id]
        products = [
            self.storage.products[pid] for pid in product_ids if pid in self.storage.products
        ]
        products.sort(key=lambda p: p.name or '')
        return products[offset : offset + limit]

    async def bulk_update_product_tags(self, old_tag_id: UUID, new_tag_id: UUID) -> int:
        to_move = [(pid, tid) for (pid, tid) in self.storage.product_tags if tid == old_tag_id]
        count = 0
        for pid, _ in to_move:
            del self.storage.product_tags[(pid, old_tag_id)]
            if (pid, new_tag_id) not in self.storage.product_tags:
                self.storage.product_tags[(pid, new_tag_id)] = True
                count += 1
        return count

    async def count_tag_products(self, tag_id: UUID) -> int:
        return sum(1 for (_, tid) in self.storage.product_tags if tid == tag_id)
