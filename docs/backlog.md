# Backlog

Feature backlog and technical debt for Bulq development.

## Technical Debt / Code Quality

---

### Add transaction management
**Status**: High Priority
**Affected files**: `app/repository.py`

**Problem:** No explicit transaction boundaries. Multi-step operations (e.g., create run + create participation) can leave inconsistent data on failure.

**Solution:** Implement transaction management within repository methods:
- Wrap multi-step operations in try/commit/rollback blocks
- Consider adding repository-level transaction context manager

---

### Add input validation
**Status**: Medium Priority
**Affected files**: `app/routes/*.py`

**Items to validate:**
- Quantity cannot be negative (Pydantic validator)
- Price cannot be negative (Pydantic validator)
- Other validations can wait

**Solution:** Add Pydantic validators to request models:
```python
@validator('quantity')
def quantity_non_negative(cls, v):
    if v < 0:
        raise ValueError('Quantity cannot be negative')
    return v
```

---

### Implement proper FastAPI error handling
**Status**: Medium Priority
**Affected files**: `app/main.py`, all route files

**Problem:** Inconsistent error responses, no global exception handler.

**Solution:** Add exception handlers in `main.py`:
- `@app.exception_handler(HTTPException)`
- `@app.exception_handler(Exception)` for unexpected errors
- Standardized error response format with timestamp

---

### Add comprehensive logging
**Status**: Medium Priority
**Affected files**: All backend files

**Problem:** Zero logging throughout application - debugging production issues will be impossible.

**Solution:** Add Python logging with appropriate severity levels:
- **DEBUG**: Detailed info for debugging (SQL queries, internal flow)
- **INFO**: Key operations (user login, run creation, state transitions)
- **WARNING**: Recoverable issues (retry attempts, deprecation warnings)
- **ERROR**: Operation failures that need attention
- **CRITICAL**: System-level failures

Configure structured logging with context (user_id, run_id, etc.).

---

### Create RunState enum and state machine
**Status**: Medium Priority
**Affected files**: `app/models.py`, `app/routes/runs.py`, `app/routes/shopping.py`

**Problem:** State transitions scattered with hardcoded strings ("planning", "active", etc.). No centralized validation.

**Solution:**
1. Create `RunState` enum inheriting from both `str` and `Enum`:
```python
from enum import Enum

class RunState(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    SHOPPING = "shopping"
    ADJUSTING = "adjusting"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

2. Create `RunStateMachine` class with validation:
```python
class RunStateMachine:
    VALID_TRANSITIONS = {
        RunState.PLANNING: [RunState.ACTIVE, RunState.CANCELLED],
        RunState.ACTIVE: [RunState.CONFIRMED, RunState.PLANNING, RunState.CANCELLED],
        # ...
    }

    def can_transition(self, from_state: RunState, to_state: RunState) -> bool:
        return to_state in self.VALID_TRANSITIONS.get(from_state, [])
```

---

### Database migrations with Alembic
**Status**: Future (before production)
**Affected files**: New `alembic/` directory, `app/main.py`

**Problem:** Using `create_tables()` which can't handle schema changes. No migration history.

**Current limitations:**
- Can't add/remove/modify columns safely
- Can't track what schema version is deployed
- Can't roll back changes
- Breaks when models change in production

**Solution:** Set up Alembic for database migrations:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Workflow:**
1. Modify models in `models.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply: `alembic upgrade head`
5. Rollback if needed: `alembic downgrade -1`

Remove `create_tables()` call from `main.py` once migrations are in place.

---

### Introduce Service Pattern
**Status**: Medium Priority - Future
**Affected files**: New `app/services/` directory, all route files

**Problem:** Business logic is scattered across route handlers, making it:
- Hard to test (coupled to HTTP concerns)
- Difficult to reuse (when Android app is added)
- Mixed with authorization, validation, and response formatting
- Complex operations span 100+ lines in routes

**Current examples of complex route logic:**
- `place_bid()` in runs.py (264-421): 157 lines with validation, state checks, auto-transitions
- `complete_shopping()` in shopping.py (179-287): Shortage detection, distribution logic
- `finish_adjusting()` in runs.py (671-777): Quantity matching, distribution updates

**Solution:** Introduce service layer incrementally:

**Architecture:**
```
Routes → Services → Repository → Database/Memory
```

**Start with RunService first** (most complex domain logic):
```python
# app/services/run_service.py
class RunService:
    def __init__(self, repo: AbstractRepository):
        self.repo = repo
        self.state_machine = RunStateMachine()

    def place_bid(self, user_id, run_id, product_id, quantity, interested_only):
        """Handle bid placement logic, validation, and state transitions."""
        # All business logic here

    def transition_to_shopping(self, user_id, run_id):
        """Generate shopping list and transition state."""
        # Shopping list generation logic

    def complete_shopping(self, user_id, run_id):
        """Handle shopping completion, shortage detection, distribution."""
        # Shopping completion logic
```

**Then routes become thin:**
```python
@router.post("/{run_id}/bids")
async def place_bid(...):
    service = RunService(get_repository(db))
    result = await service.place_bid(...)
    await manager.broadcast(...)
    return {"message": "Success"}
```

**Implementation order:**
1. **RunService** - Most complex, highest value (state machine, bid logic, shopping)
2. **GroupService** - Group creation, membership, invite management
3. **DistributionService** - Distribution tracking and pickup management
4. **ProductService** - Product search, price history

**Benefits:**
- Testable business logic (no HTTP mocking needed)
- Reusable across HTTP API and future Android app
- Centralized transaction management
- Clearer separation of concerns
- Easier to reason about complex operations

**When to implement:**
- After completing high-priority repository cleanup
- When routes exceed ~150 lines
- Before starting Android app development
- When you need to share logic between platforms

---

## Future Enhancements

### Comprehensive test suite
**Status**: Future
**Affected files**: `backend/tests/`

**Problem:** Minimal or no tests currently. Need comprehensive coverage.

**Solution:** Implement:
- Unit tests for repository methods
- Integration tests for API endpoints
- Test fixtures for common scenarios
- WebSocket connection tests
- State machine transition tests
- Use pytest with fixtures and parametrize

---

### Secure password hashing (bcrypt)
**Status**: Future (critical before production)
**Affected files**: `app/auth.py`

**Problem:** Currently using SHA-256 for password hashing, which is extremely insecure (fast = vulnerable to brute force).

**Current code (auth.py:14-26):**
```python
def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"
```

**Solution:** Use bcrypt (designed to be slow for security):
```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

Also fix hardcoded SECRET_KEY fallback (auth.py:12) - should fail if not set:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set!")
```

---

### Add database indexes
**Status**: Future (before production)
**Affected files**: `app/models.py`

**Problem:** No indexes defined on frequently queried fields, will cause slow queries at scale.

**Solution:** Add indexes on:
- Foreign keys: `group_id`, `store_id`, `user_id`, `run_id`, `product_id`, `participation_id`
- Unique lookups: `email`, `invite_token`
- Filtered queries: `state` (in Run model)

Example:
```python
class User(Base):
    email = Column(String, unique=True, nullable=False, index=True)

class Run(Base):
    state = Column(String, nullable=False, default="planning", index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False, index=True)
```

---

### Implement caching
**Status**: Future
**Affected files**: Multiple

**Problem:** Store lists, product lists fetched on every request - inefficient.

**Solution:**
- Use Redis for caching
- Cache store list (rarely changes)
- Cache product lists per store
- Cache with TTL (time-to-live)
- Invalidate on updates

---

### Add pagination
**Status**: Future
**Affected files**: `app/routes/*.py`

**Problem:** Endpoints like `get_my_groups`, `get_shopping_list`, `get_group_runs` will break with large datasets.

**Solution:** Add pagination parameters:
```python
@router.get("/items")
async def get_items(skip: int = 0, limit: int = 100):
    return repo.get_items(skip=skip, limit=limit)
```

Implement in repository methods with `OFFSET` and `LIMIT`.

---

### Rate limiting
**Status**: Future (before production)
**Affected files**: `app/main.py`, `app/routes/auth.py`

**Problem:** No protection against abuse - login, registration, bid placement all unprotected.

**Solution:** Use `slowapi` middleware:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
```

Apply to:
- Login/registration: 5 requests/minute
- Bid placement: 20 requests/minute
- General API: 100 requests/minute

---

## Product Discovery

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.
