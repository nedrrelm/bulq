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

## Frontend Technical Debt / Code Quality

---

### 🟡 MEDIUM: No Request Deduplication
**Status**: Medium Priority - Performance
**Affected files**: App.tsx, Groups.tsx, RunPage.tsx

**Problem:** Multiple components can trigger the same fetch simultaneously:
- Product search in App.tsx header
- Product search in Groups.tsx
- Run details fetched by RunPage when navigating

**Solution:** Implement a simple request cache or use a library like React Query/SWR.

---

### 🟢 LOW: Missing PropTypes/Runtime Validation
**Status**: Low Priority - Type Safety
**Affected files**: All components

**Problem:** TypeScript interfaces are defined, but no runtime validation:
- No validation that `runId` is a valid UUID
- No validation that API responses match expected shape

**Solution:** Consider adding runtime validation with Zod or similar.

---

## Frontend Performance

---

### SVG Graph Rendering Performance
**Status**: Low Priority
**Affected files**: ProductPage.tsx:30-149

**Problem:** SVG graphs rendered inline can be expensive with many price points.

**Solution:** Consider using a charting library (Chart.js, Recharts) or memoize the graph component.

---

## Frontend Architecture Improvements

---

## Product Discovery

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.
