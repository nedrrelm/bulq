# Backlog

Feature backlog and technical debt for Bulq development.

## 🚀 Critical: Production Readiness

These items must be completed before production deployment.

---

### Database Migrations with Alembic
**Status**: Critical (before production)
**Affected files**: New `alembic/` directory, `app/main.py`

**Problem:** Using `create_tables()` which can't handle schema changes. No migration history.

**Current limitations:**
- Can't add/remove/modify columns safely
- Can't track what schema version is deployed
- Can't roll back changes

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

### Security & Infrastructure
**Status**: Critical (before production)
**Affected files**: `app/main.py`, `app/routes/auth.py`, `Caddyfile`, `docker-compose.yml`

**Items:**

1. **Rate Limiting** - Use `slowapi` middleware:
   - Login/registration: 5 requests/minute
   - Bid placement: 20 requests/minute
   - General API: 100 requests/minute

2. **HTTPS/SSL with Caddy** - Set up reverse proxy:
   ```
   yourdomain.com {
       reverse_proxy backend:8000
   }
   ```
   Configure automatic Let's Encrypt certificates.

3. **Production CORS** - Configure allowed origins:
   ```python
   origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
   if not origins:
       raise RuntimeError("ALLOWED_ORIGINS must be set in production!")
   ```

4. **Static Frontend Build** - Build and serve optimized frontend files with Caddy

5. **Database Backups** - Automated daily backups with pg_dump, S3 storage, retention policy

## 🔧 Future Enhancements

---

### Caching & Performance
**Status**: Future
**Affected files**: Multiple

**Backend:**
- Cache store lists (rarely change)
- Cache product lists per store
- Use Redis with TTL and invalidation on updates

---

---

## 🧹 Code Quality & Technical Debt

Code smells and refactoring opportunities identified during backend review.

---

### 5. Centralize WebSocket Broadcasting
**Status**: High Priority (architecture)
**Affected files**: `app/routes/runs.py`, `app/routes/groups.py`, multiple routes

**Problem:** Routes manually broadcast WebSocket messages, duplicating logic across handlers.
```python
# Repeated in multiple route handlers:
await manager.broadcast(f"run:{result.run_id}", {
    "type": "bid_updated",
    "data": {...}
})
```

**Impact:** Code duplication, inconsistent message formats, hard to test.

**Fix:** Move broadcasting to service layer with event system or observer pattern.

---

### 14. Decouple WebSocket Manager
**Status**: Low Priority (testability)
**Affected files**: Services importing `websocket_manager.manager`

**Problem:** Services directly import global `manager` singleton.

**Impact:** Hard to test, tight coupling.

**Fix:** Use dependency injection for WebSocket manager.

---

### 15. Add Transaction Management
**Status**: Low Priority (data integrity)
**Affected files**: `app/services/group_service.py` (member removal)

**Problem:** Multi-step operations not wrapped in transactions.

**Impact:** Could leave database in inconsistent state on partial failures.

**Fix:** Wrap multi-step operations in database transactions.

---

### 19. Inconsistent Return Types in Services
**Status**: Medium Priority (consistency)
**Affected files**: `app/services/group_service.py:91`

**Problem:** Some service methods return Pydantic models, others construct data inline.
```python
# Inconsistent - creating datetime.now() but not in model:
created_at=datetime.now().isoformat()  # Not in actual model
```

**Impact:** Confusing API contract, may return data that doesn't match actual model.

**Fix:** Always return proper Pydantic response models, don't fabricate fields.

---

### 20. Verbose Exception Construction
**Status**: Low Priority (style)
**Affected files**: `app/exceptions.py`

**Problem:** Exception classes have verbose `__init__` methods that could be simplified.

**Impact:** Minor - slightly more code to maintain.

**Fix:** Consider using dataclasses or attrs to reduce boilerplate.

---

### 21. Mixed Responsibilities in Route Handlers
**Status**: High Priority (architecture)
**Affected files**: `app/routes/runs.py`, `app/routes/groups.py`

**Problem:** Route handlers doing WebSocket broadcasting in addition to calling services.
```python
# Routes doing too much:
result = service.create_run(...)
await manager.broadcast(...)  # Should be in service
```

**Impact:** Business logic leaking into presentation layer, hard to test.

**Fix:** Move all WebSocket broadcasting into service layer, routes should only handle HTTP.

---

### 22. Tight Coupling to WebSocket Manager Singleton
**Status**: Medium Priority (testability)
**Affected files**: `app/services/run_service.py`, `app/services/group_service.py`

**Problem:** Services directly import and use global `manager` singleton.
```python
from ..websocket_manager import manager  # Global singleton
# ...
asyncio.create_task(manager.broadcast(...))
```

**Impact:**
- Makes unit testing harder (need to mock global)
- Violates dependency injection principle
- Can't swap implementations

**Fix:** Inject WebSocket manager as dependency in service constructors.

---

### 23. No Circuit Breaker for WebSocket Broadcasting
**Status**: Low Priority (reliability)
**Affected files**: `app/services/run_service.py:1110-1118`

**Problem:** WebSocket broadcast failures logged but no circuit breaker or retry logic.
```python
try:
    asyncio.create_task(manager.broadcast(...))
except Exception as e:
    logger.warning("Failed to broadcast...")
    # Then what? No alerting, no retry
```

**Impact:** Could accumulate errors silently without alerting operators.

**Fix:**
- Implement circuit breaker pattern
- Add metrics for broadcast failures
- Alert on high failure rates

---

### 24. Duplicate State Validation Logic
**Status**: Medium Priority (DRY)
**Affected files**: `app/services/run_service.py`, multiple methods

**Problem:** State checking logic duplicated instead of using state machine consistently.
```python
# Checking states manually instead of using state machine:
if run.state not in [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]:
    raise BadRequestError("Bidding not allowed in current run state")
```

**Impact:** State transition rules spread across codebase, hard to maintain.

**Fix:** Centralize state validation in state machine, services should ask state machine "can I do X?"

---

### 25. Missing Database Transaction Context
**Status**: Medium Priority (data integrity)
**Affected files**: `app/services/group_service.py:599-626`, `app/services/run_service.py`

**Problem:** Multi-step database operations not wrapped in explicit transactions.
```python
# Multiple DB operations without transaction:
self.repo.remove_group_member(...)
for run in runs:
    # Cancel runs
    # Update participations
# If one fails, partial state changes persist
```

**Impact:** Database could be left in inconsistent state if operation fails halfway.

**Fix:**
- Wrap multi-step operations in `db.begin()` / `db.commit()` blocks
- Add explicit transaction management to repository
- Use SQLAlchemy session properly

---

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
