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

### 19. No Request ID Propagation
**Status**: Medium Priority (observability)
**Affected files**: `app/middleware.py:27`

**Problem:** Request ID generated but not consistently attached to request context or all log calls.

**Impact:** Harder to trace requests through distributed logs.

**Fix:**
1. Add to request state: `request.state.request_id = request_id`
2. Extract in logging calls throughout handlers
3. Consider using contextvars for thread-safe propagation

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
