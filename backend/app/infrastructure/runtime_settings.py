"""Runtime application settings stored in database."""

from sqlalchemy.orm import Session

from app.core.models import AppSettings


def get_setting(db: Session, key: str, default: str = None) -> str | None:
    """Get a runtime setting value from database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else default


def set_setting(db: Session, key: str, value: str) -> None:
    """Set a runtime setting value in database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSettings(key=key, value=value)
        db.add(setting)
    db.commit()


def is_registration_allowed(db: Session) -> bool:
    """Check if user registration is allowed."""
    value = get_setting(db, 'allow_registration', 'true')
    return value.lower() == 'true'


def set_registration_allowed(db: Session, allowed: bool) -> None:
    """Enable or disable user registration."""
    set_setting(db, 'allow_registration', 'true' if allowed else 'false')


def initialize_default_settings(db: Session) -> None:
    """Initialize default settings if they don't exist."""
    # Only set if not already set
    if get_setting(db, 'allow_registration') is None:
        set_setting(db, 'allow_registration', 'true')  # Default to true
