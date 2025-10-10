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

## 🧹 Last Pass: Code Quality & Technical Debt

Technical debt and code quality improvements to address before production deployment.

---

### 3. Hardcoded Secure Cookie Setting
**Status**: High Priority (security)
**Affected files**: `app/routes/auth.py:89, 124`

**Problem:** Security-critical `secure` flag is hardcoded to `False` instead of being environment-based.
```python
secure=False,  # Set to True in production with HTTPS
```

**Risk:** Easy to forget to enable in production, leaving sessions vulnerable to interception.

**Fix:**
```python
secure=os.getenv("ENVIRONMENT") == "production"
# or
secure=os.getenv("SECURE_COOKIES", "False").lower() == "true"
```

---

### 4. Inconsistent Exception Handling in Routes
**Status**: ✅ COMPLETED
**Affected files**: All route files (`runs.py`, `groups.py`, `shopping.py`, `distribution.py`, `notifications.py`, `stores.py`)

**Problem:** Routes were manually converting custom exceptions to HTTPException, defeating the purpose of global exception handlers.

**Fix Applied:**
1. Removed all unnecessary try-except blocks from routes. Custom exceptions now propagate directly to global handlers in `error_handlers.py`.
2. Refactored legacy `retract_bid` endpoint - moved business logic from route handler to `RunService.retract_bid()` method.

**Results:**
- **Removed ~160 lines** of duplicate code (70 from exception handling + 90 from retract_bid refactor)
- **Simplified 29 route handlers** across 6 files:
  - runs.py: 11 handlers cleaned (including retract_bid refactor)
  - groups.py: 6 handlers cleaned
  - shopping.py: 4 handlers cleaned
  - distribution.py: 3 handlers cleaned
  - notifications.py: 4 handlers cleaned
  - stores.py: 1 handler cleaned
- Error responses now consistently use `ErrorResponse` model from global handlers
- **Eliminated all repository implementation leakage** from routes (no more `hasattr(repo, '_runs')` checks)
- Proper separation of concerns: routes handle HTTP, services handle business logic
- Maintained HTTPException only for UUID validation errors (ValueError)

---

### 5. Repository Implementation Leakage in Services
**Status**: High Priority (architecture)
**Affected files**: `app/services/run_service.py:114`

**Problem:** Service layer checks repository implementation details with `hasattr(self.repo, '_runs')`.
```python
if hasattr(self.repo, '_runs'):  # Memory mode
```

**Impact:** Violates repository pattern abstraction, tight coupling, makes testing harder.

**Fix:** Use polymorphism - implement methods differently in each repository class, not conditionals in service layer.

---

### 6. Magic Numbers in Business Logic
**Status**: Medium Priority (maintainability)
**Affected files**: `app/services/run_service.py:67`

**Problem:** Hardcoded limits with no configuration.
```python
if len(active_runs) >= 100:
```

**Fix:** Move to config:
```python
# config.py
MAX_ACTIVE_RUNS_PER_GROUP = int(os.getenv("MAX_ACTIVE_RUNS", "100"))
```

---

### 7. Deprecated datetime.utcnow()
**Status**: High Priority (Python 3.12+ compatibility)
**Affected files**: `app/auth.py:24, 29, 42`

**Problem:** `datetime.utcnow()` is deprecated in Python 3.12+.
```python
expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
```

**Fix:** Replace all instances with:
```python
from datetime import timezone
expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRY_HOURS)
```

---

### 9. Inconsistent UUID Parsing
**Status**: Low Priority (code consistency)
**Affected files**: Multiple service and route files

**Problem:** Mixing `uuid.UUID()` and `UUID()` imports throughout codebase.

**Fix:** Standardize on one import style:
```python
from uuid import UUID
# Always use: UUID(string_value)
```

---

### 10. Pydantic v2 Validator Deprecation
**Status**: Medium Priority (Pydantic upgrade path)
**Affected files**: `app/routes/runs.py:181`

**Problem:** Using Pydantic v1 `@validator` syntax.
```python
@validator('quantity')
def validate_quantity(cls, v):
```

**Fix:** Migrate to Pydantic v2 syntax:
```python
from pydantic import field_validator

@field_validator('quantity')
def validate_quantity(cls, v):
```

---

### 11. Database URL Contains Password
**Status**: Medium Priority (security)
**Affected files**: `app/database.py:7`

**Problem:** Default DATABASE_URL includes hardcoded password visible in code.
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bulq:bulq_dev_pass@localhost:5432/bulq")
```

**Fix:** Use clearly dev-only default or remove default entirely:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bulq:CHANGE_ME_DEV_ONLY@localhost:5432/bulq")
```

---

### 12. No Session Cleanup
**Status**: High Priority (memory leak)
**Affected files**: `app/auth.py:55`

**Problem:** `cleanup_expired_sessions()` function exists but is never invoked.

**Impact:** Memory leak - expired sessions accumulate forever in the global `sessions` dict.

**Fix:** Add periodic cleanup with background task or call on each session operation:
```python
# In main.py startup event or use APScheduler
import asyncio

@app.on_event("startup")
async def start_cleanup_task():
    async def cleanup_loop():
        while True:
            await asyncio.sleep(3600)  # Every hour
            cleanup_expired_sessions()
    asyncio.create_task(cleanup_loop())
```

---

### 13. Redundant Config Function
**Status**: Low Priority (code cleanliness)
**Affected files**: `app/config.py:23`

**Problem:** Trivial wrapper function adds no value.
```python
def get_repo_mode() -> str:
    return REPO_MODE
```

**Fix:** Remove function and use `REPO_MODE` constant directly everywhere.

---

### 14. Inconsistent Response Model Pattern
**Status**: Medium Priority (type safety)
**Affected files**: Multiple route files

**Problem:** Mixing dict returns with typed Pydantic responses.
```python
return {"id": str(run.id), ...}  # dict
return CreateRunResponse(...)     # model
```

**Fix:** Standardize on Pydantic response models throughout for better type safety and automatic validation.

---

### 15. Missing Type Hints
**Status**: Low Priority (type safety)
**Affected files**: Various files throughout codebase

**Problem:** Some functions lack complete type hints for parameters and returns.

**Fix:** Add comprehensive type hints throughout, especially in service layer methods.

---

### 16. Long Service Methods
**Status**: Medium Priority (maintainability)
**Affected files**: `app/services/run_service.py:91-200`

**Problem:** Methods like `get_run_details()` exceed 100 lines, violating Single Responsibility Principle.

**Impact:** Hard to test, understand, and maintain.

**Fix:** Extract helper methods:
- `_get_participants_data()`
- `_get_products_data()`
- `_calculate_product_statistics()`

---

### 17. Inconsistent Logging Styles
**Status**: Medium Priority (observability)
**Affected files**: Multiple service and route files

**Problem:** Not all logs include structured `extra` context dictionary.
```python
# Inconsistent:
logger.info(f"Message")
logger.info(f"Message", extra={...})
```

**Fix:** Always use `extra` dict for structured logging to enable better querying in production:
```python
logger.info(
    "Run created",
    extra={"user_id": str(user.id), "run_id": str(run.id)}
)
```

---

### 18. String State Comparisons
**Status**: Medium Priority (type safety)
**Affected files**: Multiple service files

**Problem:** Uses string literals instead of `RunState` enum for comparisons.
```python
if run.state == 'adjusting':  # string literal
```

**Impact:** Typos not caught by type checker or linter.

**Fix:** Use enum everywhere:
```python
if run.state == RunState.ADJUSTING:
```

---

### 19. No Request ID Propagation
**Status**: Medium Priority (observability)
**Affected files**: `app/middleware.py:27`

**Problem:** Request ID generated but not consistently attached to request context or all log calls.

**Impact:** Harder to trace requests through distributed logs.

**Fix:**
1. Add to request state: `request.state.request_id = request_id`
2. Extract in logging calls throughout handlers
3. Consider using contextvars for thread-safe propagation

---

### 20. Missing Database Indexes
**Status**: High Priority (performance)
**Affected files**: `app/models.py`

**Problem:** Not all frequently-queried columns have explicit indexes.

**Impact:** Slow queries as data grows, especially on foreign key lookups without indexes.

**Fix:**
1. Audit query patterns in services
2. Add indexes for common lookups (user_id, run_id, state combinations)
3. Consider composite indexes for common query filters
4. Document in migration when implementing Alembic

---

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
