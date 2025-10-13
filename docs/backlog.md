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

## ⚡ Frontend: Performance Issues

---

### 39. WebSocket Reconnection Storms
**Status**: Medium (reliability)
**Affected files**: `useWebSocket.ts`

**Problem:** If multiple WebSocket connections fail, they all retry simultaneously, potentially overwhelming server.

**Impact:** Server load spikes, connection issues.

**Fix:** Implement exponential backoff and jitter for reconnection attempts.

---

## 🔒 Frontend: Security Issues

---

### 40. No CSRF Token Handling
**Status**: Medium (security)
**Affected files**: API client

**Problem:** No visible CSRF token handling in requests.

**Impact:** Depends on backend implementation, potential CSRF vulnerability.

**Fix:** Verify backend handles CSRF, add token handling if needed.

---

### 41. SessionStorage for Auth Flags
**Status**: Low (security)
**Affected files**: `AuthContext.tsx:30`

**Problem:** Using sessionStorage for auth-related flags:
```typescript
sessionStorage.setItem('just_logged_out', 'true')
```

**Impact:** Limited risk but could be exploited.

**Fix:** Consider using memory-only state or evaluate if flag is necessary.

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

### 44. Enhanced Linting Configuration Needed
**Status**: Medium (code quality)
**Affected files**: `eslint.config.js`, `package.json`

**Current state:** Basic ESLint config with react-hooks and typescript plugins.

**Recommended additions:**

**Option 1: Stay with ESLint (add plugins)**
```bash
npm install --save-dev \
  eslint-plugin-jsx-a11y \
  eslint-plugin-import \
  eslint-plugin-react \
  eslint-plugin-unused-imports \
  @tanstack/eslint-plugin-query \
  prettier \
  eslint-config-prettier
```

Plugins provide:
- `jsx-a11y`: Accessibility linting (catch issues #23)
- `import`: Import order, unused imports (fix issues #27, #25)
- `react`: Additional React rules
- `unused-imports`: Find dead code (fix issue #25)
- `@tanstack/eslint-plugin-query`: React Query best practices
- `prettier`: Code formatting (like Black for Python)

**Option 2: Switch to Biome (Modern all-in-one tool)**
```bash
npm install --save-dev @biomejs/biome
```

Benefits of Biome:
- 100x faster than ESLint + Prettier
- Linter + Formatter in one tool (like Ruff for Python)
- Drop-in ESLint/Prettier replacement
- Better error messages
- Zero config for most cases

**Option 3: Hybrid (ESLint + Biome formatter)**
Use Biome for formatting, ESLint for linting.

**Recommendation:** Try Biome first (closest to Ruff experience), fall back to enhanced ESLint if needed.

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

### 46. Add Pre-commit Hooks
**Status**: Medium (code quality)
**Affected files**: New `.husky/` directory, `package.json`

**Problem:** No pre-commit hooks to enforce linting/formatting before commits.

**Impact:** Inconsistent code style, linting errors in commits.

**Fix:** Add Husky + lint-staged:
```bash
npm install --save-dev husky lint-staged
npx husky init
```

Configure to run linting and formatting on staged files before commit.

---

### 47. Bundle Size Analysis
**Status**: Low (monitoring)
**Affected files**: Build configuration

**Problem:** No bundle size monitoring or analysis.

**Impact:** Can't track bundle size growth, potential performance issues.

**Fix:** Add bundle analyzer:
```bash
npm install --save-dev rollup-plugin-visualizer
```

---

## 📊 Frontend Code Review Summary

**Total Issues Identified:** 47

### By Priority:
- 🔴 **Critical:** 6 issues (must fix before production)
- 🟠 **High Priority:** 8 issues (architectural, significant refactoring)
- 🟡 **Medium Priority:** 18 issues (code quality, maintainability)
- 🟢 **Low Priority:** 10 issues (polish, style)
- ⚡ **Performance:** 3 issues
- 🔒 **Security:** 3 issues (including critical #1)
- 🧪 **Testing:** 2 issues
- 🛠️ **Tooling:** 4 issues

### Positive Aspects:
- ✅ Good use of React Query for most data fetching
- ✅ TypeScript throughout for type safety
- ✅ Centralized API client with error handling (mostly)
- ✅ Zod validation on API responses
- ✅ Custom hooks for reusable logic
- ✅ Code splitting at route level
- ✅ WebSocket integration for real-time updates
- ✅ Error boundaries implemented
- ✅ Modern React patterns (hooks, functional components)

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
