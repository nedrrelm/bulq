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

---

## 🧪 Frontend: Testing

---

### 42. No Test Files
**Status**: HIGH (quality assurance)
**Affected files**: Entire frontend

**Problem:** No `.test.tsx` or `.spec.tsx` files found in codebase.

**Impact:** No automated testing, higher risk of regressions, harder to refactor confidently.

**Fix:** Add comprehensive test suite:
- Unit tests for hooks (`@testing-library/react-hooks`)
- Component tests (`@testing-library/react`)
- Integration tests for key flows
- E2E tests for critical paths (Playwright/Cypress)

---

## 🛠️ Frontend: Tooling & Infrastructure

---

### 45. Enable TypeScript Strict Mode
**Status**: Medium (type safety)
**Affected files**: `tsconfig.json`, `tsconfig.app.json`

**Problem:** TypeScript strict mode not fully enabled, missing some type safety checks.

**Impact:** Missing type safety, potential runtime errors.

**Fix:** Enable stricter TypeScript options:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
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

---

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
