# Backlog

Feature backlog and technical debt for Bulq development.

## 🚀 Critical: Production Readiness

These items must be completed before production deployment.

---

### Database Repository Implementation
**Status**: Critical (before production)
**Affected files**: `app/repository.py`

**Problem:** Currently using `MemoryRepository` with test data. `DatabaseRepository` exists but is not implemented.

**Solution:**
1. Implement all methods in `DatabaseRepository` using SQLAlchemy queries
2. Add transaction management (try/commit/rollback blocks)
3. Test all repository methods work correctly
4. Set `REPO_MODE=database` in production environment

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

---

## ✨ Feature Requests 

## Expand entities with necessary fields:

- Product:
  - brand
  - unit
  - product category (rice > basmati rice, jasmin rice) - separate entity
  - allow multiple stores
  - price not mandatory, only estimate
  - verified
  - created at
  - created by
  - verified at
  - verified by
- Store:
  - address
  - chain
  - opening hours
  - verified
  - created at
  - created by
  - verified at
  - verified by
- User:
  - is_admin
  - username (will eventually replace email)
  - verified
  - created at
- Group:
  - created at
- GroupMembership:
  - is_group_admin
- Run:
  - adjusted_at
  - state to enum (necessary?)
- Run participation:
  - joined_at
- ProductBid:
  - picked_up_at
- ShoppingListItem:
  - encountered_price to separate entity
  - remove updated_encountered_at (since encountered price will become separate entity)
  - purchased_at

- verified field in the store and product allows admins to confirm a separate entity exists, this avoids duplicates



## Admin console

Allow verifying users, stores and products

## Add Store page:

Show available products

## Group admins:

Can remove users from group

## Consolidate search bar

Allow for searching for products, stores and groups

## 🔧 Future Enhancements

---

### Caching & Performance
**Status**: Future
**Affected files**: Multiple

**Backend:**
- Cache store lists (rarely change)
- Cache product lists per store
- Use Redis with TTL and invalidation on updates

**Frontend:**
- Request deduplication (React Query/SWR)
- Optimize SVG graph rendering (use charting library or memoization)

---

### Pagination
**Status**: Future
**Affected files**: `app/routes/*.py`

**Problem:** Endpoints like `get_my_groups`, `get_shopping_list`, `get_group_runs` will break with large datasets.

**Solution:** Add pagination parameters:
```python
@router.get("/items")
async def get_items(skip: int = 0, limit: int = 100):
    return repo.get_items(skip=skip, limit=limit)
```

---

## 🎨 Code Quality Improvements

---

### Frontend Type Safety
**Status**: Low Priority
**Affected files**: All components

**Items:**
- Add runtime validation with Zod
- Validate API responses match expected shape
- Validate UUIDs before API calls



## Separate css and tsx on frontend



---

## 📝 Notes

- **Repository Pattern**: Keep MemoryRepository for development/testing, but ensure DatabaseRepository is primary for production
- **Mobile App**: Native Kotlin Android app planned after web platform stable
