"""Runtime application settings stored in database."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AppSettings
from sqlalchemy import select, insert


async def get_setting(db: AsyncSession, key: str, default: str = None) -> str | None:
    """Get a runtime setting value from database."""
    setting = (await db.execute(select(AppSettings).filter(AppSettings.key == key))).scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    """Set a runtime setting value in database."""
    result= await db.execute(insert(AppSettings).values(key=key, value=value).on_conflict_do_update(index_elements=[AppSettings.key], set_= {"key":key, "value":value}))
    await db.commit()


async def is_registration_allowed(db: AsyncSession) -> bool:
    """Check if user registration is allowed."""
    value = await get_setting(db, 'allow_registration', 'true')
    return value.lower() == 'true'


async def set_registration_allowed(db: AsyncSession, allowed: bool) -> None:
    """Enable or disable user registration."""
    await set_setting(db, 'allow_registration', 'true' if allowed else 'false')


async def initialize_default_settings(db: AsyncSession) -> None:
    """Initialize default settings if they don't exist."""
    # Only set if not already set
    if await get_setting(db, 'allow_registration') is None:
        await set_setting(db, 'allow_registration', 'true')  # Default to true
