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

### Session & Authentication Infrastructure
**Status**: Critical (before production)
**Affected files**: `app/auth.py`, `docker-compose.yml`

**Problem:** Sessions stored in-memory dictionary. All users logged out on server restart.

**Current code (auth.py:8):**
```python
sessions: Dict[str, dict] = {}
```

**Solution:** Use Redis for persistent session storage:
```python
import redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def create_session(user_id: str) -> str:
    session_token = secrets.token_urlsafe(32)
    redis_client.setex(
        f"session:{session_token}",
        SESSION_EXPIRY_HOURS * 3600,
        json.dumps({"user_id": user_id, ...})
    )
    return session_token
```

Add Redis service to docker-compose.yml.

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

---

### Add New Store
**Status**: Planned
**Affected files**: Frontend components, `app/routes/stores.py`

**Description:** Allow users to add new stores to the platform.

**Current state:**
- ✅ Backend route exists: `POST /stores/create`
- ✅ Service method exists: `StoreService.create_store(name)`
- ❌ No frontend UI to create stores

**Solution:**
1. Add "Add Store" button/form in frontend (possibly in Groups page or separate Stores page)
2. Form with single input field: Store name
3. Validation: Store name required, minimum 2 characters
4. On success: Add store to local store list, show success message
5. Consider: Should all users be able to add stores, or only admins?

**Considerations:**
- Should stores have additional fields (address, type, etc.)?
- How to handle duplicate store names?
- Should stores be verified/approved before appearing for all users?

---

### Add New Product
**Status**: Planned
**Affected files**: Frontend components, `app/routes/products.py` (to be created)

**Description:** Allow users to add new products to stores.

**Current state:**
- ✅ Repository method exists: `repo.create_product(store_id, name, base_price)`
- ✅ Service method exists: `ProductService.create_product(store_id, name, base_price)`
- ❌ No backend route for creating products
- ❌ No frontend UI to create products

**Solution:**

**Backend:**
1. Create `POST /products/create` route in new `app/routes/products.py`:
   ```python
   @router.post("/create")
   async def create_product(
       request: CreateProductRequest,
       current_user: User = Depends(require_auth),
       db: Session = Depends(get_db)
   ):
       repo = get_repository(db)
       service = ProductService(repo)
       product = service.create_product(
           store_id=request.store_id,
           name=request.name,
           base_price=request.base_price
       )
       return {"id": str(product.id), "name": product.name, ...}
   ```

**Frontend:**
1. Add "Add Product" button/form (possibly in product search results or store-specific page)
2. Form fields:
   - Store selection (dropdown)
   - Product name (text input)
   - Base price (number input)
3. Validation:
   - All fields required
   - Price must be positive
   - Price cannot be zero
4. On success: Product available for bidding immediately

**Considerations:**
- Should products have categories/tags?
- Should products have descriptions?
- How to handle duplicate product names in same store?
- Should there be product moderation/approval?
- Consider adding product units (e.g., "per lb", "per item")

---

### Allow Run Leader to Cancel Run at Any Stage
**Status**: Planned
**Affected files**: `app/services/run_service.py`, `app/routes/runs.py`, frontend

**Problem:** Runs can only be cancelled before the `distributing` state. Leaders have no way to cancel once in certain stages.

**Solution:**
1. Backend: Add `cancel_run` endpoint allowing leader to cancel from any state
2. Update state machine to allow transitions to `cancelled` from all states
3. Add business logic for different stages:
   - Before `shopping`: Simple state change
   - During `shopping`: Handle partial purchases
   - During `distributing`: Handle returns/refunds
4. Frontend: Add "Cancel Run" button visible only to leader
5. Add confirmation dialog with consequences based on current state
6. Consider adding `cancellation_reason` field

**State machine change in `app/run_state.py`:**
```python
# Add transitions from all states to cancelled
state_machine.add_transition('cancel', '*', 'cancelled')
```

---

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

### Product Families
**Status**: Future exploration

**Description:** Allow using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

Creates a hierarchy/grouping system for products.

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

---

## 📝 Notes

- **Repository Pattern**: Keep MemoryRepository for development/testing, but ensure DatabaseRepository is primary for production
- **WebSocket Support**: Already planned in architecture docs - implement after core features stable
- **Mobile App**: Native Kotlin Android app planned after web platform stable
