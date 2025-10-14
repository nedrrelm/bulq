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
**Status**: Partially Complete
**Affected files**: `app/main.py`, `app/routes/auth.py`, `Caddyfile`, `docker-compose.yml`

**Completed:**

✅ **HTTPS/SSL with Caddy** - Reverse proxy configured with automatic Let's Encrypt certificates
   - Development: Serves on port 3000
   - Production: Automatic HTTPS when `DOMAIN` environment variable is set
   - Security headers included (HSTS, X-Frame-Options, etc.)

✅ **Production CORS** - Environment-based configuration with validation
   - `ALLOWED_ORIGINS` required in production mode
   - Development defaults provided
   - Runtime validation prevents insecure configuration

✅ **Static Frontend Build** - Caddy serves optimized Vite build
   - Multi-stage Docker build (build + serve)
   - Gzip compression enabled
   - SPA routing with try_files

✅ **Production Environment Validation** - Strict checks for production mode
   - Secure cookies required with HTTPS
   - Database URL validation
   - Strong secret key enforcement

**Still TODO:**

1. **Rate Limiting** - Use `slowapi` middleware:

   - Login/registration: 5 requests/minute
   - Bid placement: 20 requests/minute
   - General API: 100 requests/minute

2. **Database Backups** - Automated daily backups with pg_dump, S3 storage, retention policy
   - Manual backup script documented
   - Need automated backup to cloud storage
   - Need monitoring/alerting for backup failures

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
