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

## 🔴 Frontend: Critical Issues

**All critical issues have been resolved! ✅**

---

## 🟠 Frontend: High Priority (Architecture)

Major architectural issues and code smells requiring significant refactoring.

---


### 8. Large Component Files
**Status**: High Priority (maintainability)
**Affected files**:
- `RunPage.tsx` (839 lines)
- `ShoppingPage.tsx` (609 lines)
- `Groups.tsx` (278 lines)

**Problem:** Components doing too much - managing state, WebSocket connections, UI rendering, and business logic all in one file. Violates single responsibility principle.

**Impact:** Hard to test, hard to maintain, hard to understand.

**Fix:** Break down into smaller components:
- Extract `ProductItem` components
- Extract form popups into separate files
- Extract business logic into custom hooks
- Create smaller, focused components

---

### 9. Inconsistent State Management Patterns
**Status**: Medium-High (architecture)
**Affected files**: `NotificationContext.tsx` (Context) vs React Query hooks (everywhere else)

**Problem:** Notifications use Context Provider with manual state management, while everything else uses React Query. Two different patterns in same app.

**Impact:** Inconsistent patterns, increased complexity, confusion for developers.

**Fix:** Either migrate notifications to React Query OR document why Context is needed for notifications specifically.

---

## 🟡 Frontend: Medium Priority (Code Quality)

Refactoring opportunities and maintainability improvements.

---

### 15. No Loading States During Mutations
**Status**: Medium (UX)
**Affected files**: Multiple components using mutations

**Problem:** When users perform actions (place bid, mark purchased, etc.), no loading indicator shows action is in progress.

**Impact:** Poor UX, users may click multiple times causing duplicate requests.

**Fix:** Show loading state during mutations using React Query's `isLoading` state.

---

### 16. Inconsistent Error Display
**Status**: Medium (UX consistency)
**Affected files**: Throughout codebase

**Problem:** Some components show errors with `<Toast>`, others with `<ErrorAlert>`, others with inline messages.

**Impact:** Inconsistent UX, confusing for users.

**Fix:** Standardize on one pattern (Toast for transient errors, inline for form validation).

---

### 17. Manual Query Invalidation Pattern
**Status**: Medium (consistency)
**Affected files**: `Groups.tsx`, `ShoppingPage.tsx`, others

**Problem:** Manual API calls followed by manual invalidation instead of using mutation hooks:
```typescript
await shoppingApi.updateAvailabilityPrice(runId, selectedItem.id, { price, notes })
queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
```

**Impact:** Bypasses React Query benefits, inconsistent patterns.

**Fix:** Use mutation hooks consistently (some components already do this correctly).

---

### 18. Duplicate Toast/Confirm Hook Patterns
**Status**: Medium (DRY violation)
**Affected files**: Nearly every page component

**Problem:** Every page declares:
```typescript
const { toast, showToast, hideToast } = useToast()
const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
```
And renders same JSX at bottom.

**Impact:** Code duplication, maintenance burden (~50+ duplicate lines).

**Fix:** Create `<PageLayout>` wrapper component that includes Toast and ConfirmDialog, or use global toast manager.

---

### 19. Hard-coded String Values and Magic Numbers
**Status**: Medium (maintainability)
**Affected files**: Throughout codebase

**Examples:**
- `ShoppingPage.tsx` line 324: `MAX_NOTES_LENGTH = 200`
- `RunPage.tsx` line 81: State ordering object
- Various component class names as strings

**Impact:** Hard to maintain, no single source of truth, difficult to change values globally.

**Fix:** Extract to constants file: `src/constants/index.ts`

---

### 20. Missing Optimistic Updates
**Status**: Medium (UX)
**Affected files**: Most mutation hooks

**Problem:** Only `useToggleReady` implements optimistic updates. Other user actions don't provide instant feedback.

**Impact:** Slower feeling UX, perceived lag.

**Fix:** Implement optimistic updates for frequent user actions (placing bids, marking items).

---

### 21. Complex Memoization Logic
**Status**: Medium (maintainability)
**Affected files**: `RunPage.tsx:200-213`

**Problem:** Custom memo comparison function is complex and fragile. Adding new fields requires updating comparison.

**Impact:** Maintenance burden, easy to forget updates, potential bugs.

**Fix:** Use simpler comparison or rely on React's default shallow comparison.

---

### 22. Inline Styles Mixed with CSS Classes
**Status**: Medium (consistency)
**Affected files**: `NotificationBadge.tsx`, `App.tsx`

**Problem:** Inconsistent styling approach - some use CSS files, others inline styles.

**Impact:** Inconsistent patterns, harder to maintain, violates project guidelines.

**Fix:** Standardize on CSS files with utility classes per project guidelines.

---

### 23. Missing Accessibility Features
**Status**: Medium (accessibility)
**Affected files**: Multiple components

**Issues:**
- Many buttons lack `aria-label` attributes
- Form inputs sometimes missing associated labels
- Modal dialogs missing proper ARIA roles
- Missing `aria-live` regions for dynamic content
- Form errors not announced to screen readers
- Potential color contrast issues

**Impact:** Poor accessibility, WCAG non-compliance, screen reader users have poor experience.

**Fix:**
- Add proper ARIA labels
- Add `aria-live="polite"` regions for dynamic content
- Add `aria-describedby` linking inputs to error messages
- Ensure keyboard navigation works properly
- Audit colors for WCAG AA compliance

---

### 24. Error Boundary Uses Hard Reload
**Status**: Medium (UX)
**Affected files**: `ErrorBoundary.tsx:34`

**Problem:** Error boundary reloads entire page instead of resetting state:
```typescript
handleReload = () => {
  window.location.href = '/'
}
```

**Impact:** Poor recovery UX, losing user data.

**Fix:** Implement state reset without full page reload when possible.

---

### 25. Unused Code and Dead Imports
**Status**: Medium (bundle size)
**Affected files**: Throughout

**Examples:**
- `useApi.ts` - Not used anywhere but still in codebase
- Various unused imports

**Impact:** Increases bundle size, confuses developers.

**Fix:** Remove unused code using `eslint-plugin-unused-imports`.

---

### 26. Missing Debouncing on Expensive Operations
**Status**: Medium (performance)
**Affected files**: Various components

**Problem:** Search is debounced (good!), but other expensive operations aren't.

**Impact:** Potential performance issues with rapid user interactions.

**Fix:** Review and add debouncing where needed (form validation, API calls on input change).

---

## 🟢 Frontend: Low Priority (Polish)

Minor improvements and style issues.

---

### 27. Inconsistent Import Ordering
**Status**: Low (code organization)
**Affected files**: Throughout

**Problem:** No consistent pattern for organizing imports (React, third-party, local, types).

**Impact:** Minor code organization issue.

**Fix:** Use ESLint with import sorting rules (`eslint-plugin-import`).

---

### 28. Console Statements in Production Code
**Status**: Low (debugging)
**Affected files**: Throughout

**Problem:** Production code contains console.log/error statements.

**Impact:** Cluttered console in production, potential information leakage.

**Fix:** Use proper logging library or wrap console calls in development-only utility.

---

### 29. Inconsistent Function Declaration Styles
**Status**: Low (style)
**Affected files**: Throughout

**Problem:** Mix of arrow functions, function declarations, and function expressions.

**Impact:** Style inconsistency.

**Fix:** Pick one style (recommend arrow functions for consistency) and enforce with ESLint.

---

### 30. Missing JSDoc Comments
**Status**: Low (documentation)
**Affected files**: Throughout

**Problem:** Complex functions lack documentation explaining parameters, return values, behavior.

**Impact:** Harder to understand code, no IDE hover documentation.

**Fix:** Add JSDoc comments to public functions and complex logic.

---

### 31. Generic Variable Names
**Status**: Low (readability)
**Affected files**: Throughout

**Examples:** `data`, `err`, `e`, `item`

**Problem:** Non-descriptive variable names make code harder to understand.

**Impact:** Readability issues.

**Fix:** Use descriptive names: `userData`, `apiError`, `clickEvent`, `shoppingListItem`.

---

### 32. No Loading Skeleton States
**Status**: Low (UX polish)
**Affected files**: Components showing "Loading..." text

**Problem:** Plain text loading states feel unpolished compared to skeleton loaders.

**Impact:** Perceived performance, UX polish.

**Fix:** Implement skeleton loading states for better perceived performance.

---

### 33. Deprecated React Query Property
**Status**: Low (deprecation)
**Affected files**: `main.tsx:14`

**Problem:** Uses deprecated `cacheTime` property:
```typescript
cacheTime: 300000, // Cache kept for 5 minutes
```

**Impact:** Deprecation warning in console.

**Fix:** Update to `gcTime` if using React Query v5.

---

### 34. Inconsistent Loading Component Usage
**Status**: Low (consistency)
**Affected files**: Various

**Problem:** Some use `<LoadingSpinner />`, others use inline "Loading..." text, others show nothing.

**Impact:** UX inconsistency.

**Fix:** Use `<LoadingSpinner />` consistently everywhere.

---

### 35. Magic Numbers in setTimeout
**Status**: Low (clarity)
**Affected files**: `Groups.tsx:129`, `useWebSocket.ts:4-7`

**Problem:** setTimeout delays like 100ms, 1500ms lack explanation.

**Impact:** Unclear intent, hard to adjust timing.

**Fix:** Extract to named constants with comments explaining why:
```typescript
const WEBSOCKET_RECONNECT_DELAY_MS = 1500 // Wait before reconnecting after disconnect
```

---

### 36. No Environment-specific Configuration Validation
**Status**: Low (configuration)
**Affected files**: `config.ts`

**Problem:** Simple config without environment-specific overrides or validation.

**Impact:** Configuration flexibility, potential runtime errors.

**Fix:** Add environment validation and type-safe config with Zod.

---

## ⚡ Frontend: Performance Issues

---

### 37. Unnecessary Re-renders
**Status**: Medium (performance)
**Affected files**: `Groups.tsx`, other list components

**Problem:** Lists re-render entirely when only one item changes.

**Impact:** Performance degradation with large lists.

**Fix:** Use `React.memo` on list item components, ensure key props are stable.

---

### 38. No Code Splitting Beyond Route Level
**Status**: Low-Medium (bundle size)
**Affected files**: `App.tsx`

**Problem:** Only route-level code splitting via `lazy()`. Large components and modals aren't split.

**Impact:** Larger initial bundle size.

**Fix:** Consider splitting large modals/popups with lazy loading.

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

### 43. Untestable Code Patterns
**Status**: Medium (testability)
**Affected files**: Large components with mixed concerns

**Problem:** Components too large and coupled to test effectively.

**Impact:** Testing difficulty, low test coverage even if tests added.

**Fix:** Refactor into smaller, testable units (see issue #10).

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
