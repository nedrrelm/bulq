# Backlog

Feature backlog and technical debt for Bulq development.

## Technical Debt / Code Quality

---

### Redis session storage
**Status**: Critical (before production)
**Affected files**: `app/auth.py`

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

Add Redis to docker-compose.yml.

---

### Add transaction management
**Status**: High Priority
**Affected files**: `app/repository.py`

**Problem:** No explicit transaction boundaries. Multi-step operations (e.g., create run + create participation) can leave inconsistent data on failure.

**Solution:** Implement transaction management within repository methods:
- Wrap multi-step operations in try/commit/rollback blocks
- Consider adding repository-level transaction context manager

---

### Switch from in-memory to database repository
**Status**: Critical (before production)
**Affected files**: `app/repository.py`, `app/config.py`

**Problem:** Currently using `MemoryRepository` with test data in development. Need to switch to `DatabaseRepository` for production.

**Current setup:**
- `REPO_MODE` in `app/config.py` determines which repository implementation to use
- Memory mode has hardcoded test data
- Database mode uses PostgreSQL

**Solution:**
1. Ensure `REPO_MODE=database` in production environment
2. Remove or disable memory mode in production builds
3. Verify all repository methods work correctly with DatabaseRepository
4. Test data migrations from memory to database if needed

---

### Database migrations with Alembic
**Status**: Critical (before production)
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

### Add database indexes
**Status**: Important (before production)
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
**Status**: Critical (before production)
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

### HTTPS/SSL configuration with Caddy
**Status**: Critical (before production)
**Affected files**: New `Caddyfile`, `docker-compose.yml`

**Problem:** No SSL/HTTPS configured. Passwords and session tokens sent in plaintext.

**Solution:** Set up Caddy as reverse proxy:
1. Create Caddyfile:
```
yourdomain.com {
    reverse_proxy backend:8000
}
```
2. Add Caddy service to docker-compose
3. Configure automatic Let's Encrypt certificates
4. Update CORS settings for production domain

---

### Production CORS configuration
**Status**: Critical (before production)
**Affected files**: `app/main.py`

**Problem:** CORS currently only allows localhost:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
]
```

**Solution:** Add production domain and configure properly:
```python
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not origins:
    raise RuntimeError("ALLOWED_ORIGINS must be set in production!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Database connection pooling
**Status**: Important (before production)
**Affected files**: `app/database.py`

**Problem:** Using default SQLAlchemy settings which may not be suitable for production load.

**Solution:** Configure connection pool:
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Number of connections to maintain
    max_overflow=10,        # Extra connections if pool exhausted
    pool_timeout=30,        # Seconds to wait for connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True      # Verify connections before use
)
```

---

### Production logging configuration
**Status**: Important (before production)
**Affected files**: `app/logging_config.py`, `app/main.py`

**Problem:** Basic logging setup needs production-grade configuration.

**Solution:**
1. Structured JSON logging for log aggregation
2. Log to files with rotation
3. Different log levels for different environments
4. Consider integrating error tracking (Sentry)
```python
if os.getenv("ENV") == "production":
    # JSON structured logging
    # File rotation
    # Error tracking integration
```

---

### Build and serve static frontend files
**Status**: Critical (before production)
**Affected files**: `frontend/Dockerfile`, `docker-compose.yml`, `Caddyfile`

**Problem:** Frontend currently served by Vite dev server, not suitable for production.

**Solution:**
1. Update frontend Dockerfile to build static files:
```dockerfile
# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage - serve with Caddy
FROM caddy:2
COPY --from=builder /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile
```
2. Configure Caddy to serve static files and proxy API

---

### Database backup strategy
**Status**: Important (before production)
**Affected files**: New backup scripts

**Problem:** No automated database backups. Risk of data loss.

**Solution:**
1. Automated daily backups using pg_dump
2. Store backups in separate location (S3, separate volume)
3. Test restore procedure
4. Retention policy (e.g., keep daily for 7 days, weekly for 4 weeks)

Example backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h db -U bulq bulq | gzip > /backups/bulq_$DATE.sql.gz
# Upload to S3 or other storage
# Clean old backups
```

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

## Feature Requests

### Allow run leader to cancel run at any stage
**Status**: Planned
**Affected files**: `app/services/run_service.py`, `app/routes/runs.py`, `frontend/src/components/RunPage.tsx`

**Problem:** Currently, runs can only be cancelled before the `distributing` state (per state machine rules). Leaders have no way to cancel a run once it reaches certain stages, even if needed.

**Solution:**
1. Backend: Add `cancel_run` endpoint that allows the leader to cancel a run from any state
2. Update state machine to allow transitions to `cancelled` from all states (not just before `distributing`)
3. Add business logic to handle cancellation at different stages:
   - Before `shopping`: Simple state change
   - During `shopping`: May need to handle partial purchases
   - During `distributing`: May need to handle returns/refunds
4. Frontend: Add "Cancel Run" button visible only to leader
5. Add confirmation dialog explaining consequences based on current state
6. Consider adding a `cancellation_reason` field for tracking

**State machine change in `app/run_state.py`:**
```python
# Add transitions from all states to cancelled
state_machine.add_transition('cancel', '*', 'cancelled')
```

**API endpoint:**
```python
@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify user is leader
    # Cancel run
    # Notify participants via WebSocket
```

---

## Product Discovery

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.
