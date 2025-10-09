import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bulq:bulq_dev_pass@localhost:5432/bulq")

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,           # Number of connections to maintain
    max_overflow=MAX_OVERFLOW,      # Extra connections if pool exhausted
    pool_timeout=POOL_TIMEOUT,      # Seconds to wait for connection
    pool_recycle=POOL_RECYCLE,      # Recycle connections after 1 hour
    pool_pre_ping=True              # Verify connections before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()