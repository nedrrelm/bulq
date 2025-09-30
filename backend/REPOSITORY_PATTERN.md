# Repository Pattern Implementation

This document explains how to use the repository pattern in the Bulq backend for data access abstraction.

## Overview

The repository pattern provides:
- **Separation of concerns**: Business logic separated from data access
- **Testability**: Easy to mock/stub data access for unit tests
- **Flexibility**: Switch between different data sources (real DB, in-memory, test fixtures)
- **Maintainability**: Changes to data access logic centralized

## Quick Start

### Switching Between Database and Memory Mode

To switch modes, simply edit the configuration in code:

**Edit `app/config.py`:**
```python
# Repository mode configuration - Change this line to switch modes
REPO_MODE: Literal["database", "memory"] = "database"  # Change to "memory" for test data
```

**For database mode (default):**
```python
REPO_MODE: Literal["database", "memory"] = "database"
```

**For test data mode:**
```python
REPO_MODE: Literal["database", "memory"] = "memory"
```

Then restart the backend:
```bash
docker compose restart backend
```

## Architecture

### Repository Interfaces (`app/repositories/interfaces.py`)
- `UserRepository`: User CRUD operations
- `GroupRepository`: Group and membership operations
- `StoreRepository`: Store operations
- `RunRepository`: Shopping run operations
- `ProductRepository`: Product operations
- `ProductBidRepository`: Bid operations

### Implementations

#### SQLAlchemy Implementation (`app/repositories/sqlalchemy_repos.py`)
- Uses real PostgreSQL database
- Production implementation
- Handles transactions and relationships

#### In-Memory Implementation (`app/repositories/memory_repos.py`)
- Stores data in Python dictionaries
- Pre-populated with test data
- Perfect for unit tests and demos

### Dependency Injection (`app/repositories/factory.py`)
- `RepositoryContainer`: Manages repository instances
- Automatic mode switching based on `REPO_MODE` environment variable
- Singleton pattern for in-memory repositories

## Usage in Routes

### Before (Direct Database Access)
```python
@router.get("/my-groups")
async def get_my_groups(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    groups = db.query(Group).filter(Group.members.contains(current_user)).all()
    return groups
```

### After (Repository Pattern)
```python
@router.get("/my-groups")
async def get_my_groups(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    group_repo = get_group_repo(db)
    groups = group_repo.get_user_groups(current_user)
    return groups
```

## Test Data (Memory Mode)

When using `REPO_MODE=memory`, the system comes with pre-populated test data:

### Test Users
- `alice@test.com` - Alice Johnson
- `bob@test.com` - Bob Smith
- `carol@test.com` - Carol Davis

### Test Groups
- **Test Friends**: Alice, Bob, Carol
- **Work Lunch**: Bob, Carol

### Test Stores & Products
- **Test Costco**: Olive Oil ($24.99), Quinoa ($18.99)
- **Test Sam's Club**: Detergent ($16.98)

### Test Runs
- Active Costco run for Test Friends group
- Planning Sam's Club run for Work Lunch group

## Testing

### Unit Tests with Memory Repositories
```python
import pytest
from app.repositories.memory_repos import create_test_repositories

def test_user_groups():
    repos = create_test_repositories()
    user_repo = repos['user']
    group_repo = repos['group']

    alice = user_repo.get_by_email("alice@test.com")
    groups = group_repo.get_user_groups(alice)

    assert len(groups) == 1
    assert groups[0].name == "Test Friends"
```

### Integration Tests with Real Database
```python
def test_user_groups_integration(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    group_repo = SQLAlchemyGroupRepository(db_session)

    # Test with real database...
```

## Environment Setup

### Development (Database Mode)
1. Set `REPO_MODE = "database"` in `app/config.py`
2. Start the application:
```bash
docker compose up -d
```

### Testing (Memory Mode)
1. Set `REPO_MODE = "memory"` in `app/config.py`
2. Restart the backend:
```bash
docker compose restart backend
```

### Demo with Test Data
1. Set `REPO_MODE = "memory"` in `app/config.py`
2. Restart the backend
3. Login with `alice@test.com` (any password works in memory mode)
4. You'll see pre-populated test groups and data

## Adding New Repository Methods

### 1. Add to Interface
```python
# In interfaces.py
@runtime_checkable
class UserRepository(Protocol):
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        ...
```

### 2. Implement in SQLAlchemy
```python
# In sqlalchemy_repos.py
class SQLAlchemyUserRepository:
    def get_active_users(self) -> List[User]:
        return self.db.query(User).filter(User.is_active == True).all()
```

### 3. Implement in Memory
```python
# In memory_repos.py
class InMemoryUserRepository:
    def get_active_users(self) -> List[User]:
        return [user for user in self._users.values() if user.is_active]
```

## Benefits

1. **Fast Testing**: Memory repositories eliminate database setup time
2. **Reliable Tests**: Tests don't depend on database state
3. **Easy Mocking**: Repository interfaces are easy to mock
4. **Development Flexibility**: Switch data sources without code changes
5. **Demo Ready**: Pre-populated test data for demos

## Usage

The repository pattern is now implemented! To switch between modes:

1. **Edit `app/config.py`** and change the `REPO_MODE` value
2. **Restart the backend**: `docker compose restart backend`

**Database mode** (default): Uses your real PostgreSQL database
**Memory mode**: Uses pre-populated test data, perfect for development and demos