# Backlog

### Bugs

1. sometimes users can't edit during adjusting (possibly when they pressed ready during planning)

### Features
1. distribution groups for each run (split total into multiple pickup points)
2. Allow leaders to set a fee for the run
3. Create buyers clubs and sellers clubs

Feature backlog and technical debt for Bulq development.

## 🚀 Critical: Production Readiness

These items must be completed before production deployment.

---

### Security & Infrastructure
**Status**: Partially Complete
**Affected files**: `app/main.py`, `app/routes/auth.py`, `Caddyfile`, `docker-compose.yml`

**Still TODO:**

1. **Rate Limiting** - Use `slowapi` middleware:

   - Login/registration: 5 requests/minute
   - Bid placement: 20 requests/minute
   - General API: 100 requests/minute

4. **Add CSRF protection** (1 day)
   - No CSRF tokens in cookie-based auth
   - Tool: `fastapi-csrf-protect` or SameSite=Strict cookies
   - Impact: Vulnerable to CSRF attacks

5. **Add database indices** (1 day)
   - Tables: Run (group_id, state), RunParticipation (run_id, user_id), ProductBid (participation_id)
   - Impact: Slow queries, N+1 problems


9. **Test DatabaseRepository** (2 days) - **CRITICAL**
   - DatabaseRepository used in production but has NO tests
   - Only MemoryRepository is tested
   - File: `tests/test_repository.py:228-239` has placeholder

---

## 🔧 Technical Debt & Code Quality

### Frontend Code Duplication

**Priority**: High
**Impact**: 20-25% code reduction (~3,000-4,000 lines)


8. **Reorganize component structure** (1-2 days)
   - 40+ components in flat directory
   - Solution: Group by feature (common/, popups/, pages/, layout/)
   - Improves: Navigation, maintainability, imports

---

### Infrastructure & CI/CD

**Priority**: High
**Impact**: Automated quality gates, security scanning

1. **Add GitHub Actions CI pipeline** (30 minutes) ⚡ **QUICK WIN**
   - No CI/CD detected (`.github/workflows/` missing)
   - Need: Backend tests, frontend lint/build, Docker builds
   - Impact: Automated testing on every push/PR
   - File: `.github/workflows/ci.yml`

2. **Add Dependabot** (10 minutes) ⚡ **QUICK WIN**
   - No automated dependency updates
   - Security vulnerabilities may go unnoticed
   - File: `.github/dependabot.yml`

3. **Add security scanning** (15 minutes) ⚡ **QUICK WIN**
   - No Trivy or similar scanning for Docker images
   - Add to GitHub Actions workflow
   - Scans: Python dependencies, npm packages, Docker base images

4. **Add healthchecks to services** (15 minutes) ⚡ **QUICK WIN**
   - Only DB has healthcheck in `docker-compose.yml`
   - Backend and frontend missing
   - Impact: Better orchestration, reliability

5. **Optimize Docker builds** (1 day)
   - Enable BuildKit cache mounts
   - Multi-stage build for backend
   - Backend image: 344MB → target <200MB
   - Frontend already optimized at 61MB

6. **Add resource limits** (30 minutes)
   - No CPU/memory limits in docker-compose
   - Risk: Service could consume all host resources
   - File: `deployment/docker-compose.prod.yml`

7. **Fix pre-commit hooks** (1 hour)
   - Frontend hooks depend on running Docker containers
   - Fails with unclear error if Docker not running
   - Solution: Run locally or add fallback
   - File: `.pre-commit-config.yaml`

---

### Performance Optimization

**Priority**: Medium
**Impact**: 40-60% reduced DB load, faster response times

1. **Implement caching layer with Redis** (2-3 days)
   - Already in backlog above, but worth repeating
   - Cache: store list, product details, user groups
   - Impact: Reduce DB load by 40-60%

2. **Add monitoring and metrics** (2 days)
   - No Prometheus metrics
   - No application performance monitoring
   - Solution: Add `prometheus-fastapi-instrumentator`
   - Endpoints: `/metrics` for Prometheus scraping

3. **Database connection pool monitoring** (2 hours)
   - Logs every checkout/checkin at DEBUG level
   - Could impact performance under load
   - Solution: Add sampling or periodic stats
   - File: `app/infrastructure/database.py:38-97`

4. **Parallelize WebSocket broadcasting** (1 day)
   - Broadcasts to room connections sequentially
   - Could be parallelized for large rooms
   - File: `app/api/websocket_manager.py:30-49`

5. **Optimize frontend bundle size** (1 day)
   - Review and implement code splitting
   - Lazy load routes
   - Analyze with `vite-bundle-visualizer`

---

### API & Documentation

**Priority**: Medium

1. **Add API versioning** (1 day)
   - All routes at `/api/*` with no version
   - Risk: Breaking changes require coordinated deployments
   - Solution: Add `/api/v1/` prefix
   - File: `app/main.py:50-61`

2. **Add pagination to all list endpoints** (1 day)
   - Some routes support limit/offset, others don't
   - Inconsistent API design
   - Target: All list endpoints

3. **Enhance OpenAPI documentation** (1-2 days)
   - No custom examples or descriptions
   - Add comprehensive docstrings and examples
   - Add response examples for all endpoints

4. **Add audit logging for admin actions** (1 day)
   - Admin operations not specifically logged
   - Security best practice for compliance
   - Log: Who, what, when, IP address
   - File: `app/api/routes/admin.py`

5. **Generate frontend types from OpenAPI** (1 day)
   - Currently manually duplicating types
   - Risk: Type drift between backend/frontend
   - Solution: Use OpenAPI generator or `openapi-typescript`

---

### Code Quality & Documentation

**Priority**: Low to Medium

1. **Improve docstring coverage** (1-2 days)
   - Repository methods often lack docstrings
   - Some route handlers have minimal docs
   - Target: All public methods

2. **Standardize logging in frontend** (1 day)
   - 9 occurrences of `console.log`/`error`/`warn`
   - Logger utility exists but not consistently used
   - Solution: Add ESLint rule to enforce
   - Files: Login.tsx, i18n/config.ts, RunProductItem.tsx, etc.

3. **Add architecture documentation** (2 days)
   - No ADR (Architecture Decision Records)
   - No system diagrams
   - Create `docs/architecture.md` with:
     - Service dependency graph
     - Network topology
     - Data flow diagrams

4. **Update deprecated datetime usage** (1 hour) ⚡ **QUICK WIN**
   - `datetime.utcnow()` used in `errors/models.py:33`
   - Should use `datetime.now(UTC)`
   - Deprecated in Python 3.12+

5. **Remove database error type from client responses** (30 minutes)
   - `app/errors/handlers.py:126-133` exposes `error_type`
   - Could reveal database schema
   - Remove from production responses

6. **Add SBOM generation** (1 day)
   - No Software Bill of Materials for dependency tracking
   - Use `syft` or built-in tools
   - Important for supply chain security

---

## 🔧 Future Enhancements

---

### UI/UX Improvements
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend components, run pages

**Features:**

9. **Leader Can Modify User Bids**
   - Leader has ability to edit other users' bids (not just force equal distribution)
   - Makes price division and quantity adjustments easier
   - Useful during adjusting stage for fine-tuning allocations
   - Note: This needs more design work to determine exact workflow and permissions

10. Let leader change back from confirmed to active

---

### Product Management Enhancements
**Status**: Future
**Priority**: Medium
**Affected files**: Database schema, backend models, frontend components, admin panel

**Features:**

1. **Product Tag System**
   - Tag dimensions: category, subcategory, generic items, brands, etc.
   - Users manually create and apply tags to products
   - Admins verify tags through admin panel
   - Add tag management table to admin panel

2. **Product Aliases (Multi-language Support)**
   - Allow multiple names per product for localization
   - Support for en, ru, sr languages
   - Prepare infrastructure for future i18n

---

### Caching & Performance
**Status**: Future
**Priority**: Medium
**Affected files**: Backend services, infrastructure

**Backend:**
- Cache store lists (rarely change)
- Cache product lists per store
- Use Redis with TTL and invalidation on updates

---

### Savings Tracking & Price Comparison
**Status**: Future
**Priority**: Medium
**Affected files**: Database schema, backend services, frontend run pages, price tracking models

**Features:**
- Track regular supermarket prices for products
- Calculate total savings per run by comparing bulk purchase prices vs regular retail prices
- Display savings summary at run completion
- Historical savings trends per group/user
- Price comparison with multiple regular retailers

**Schema Changes:**
- Add `regular_retail_price` field to ProductAvailability or new PriceComparison table
- Track price source (which regular supermarket)
- Store price observation timestamps
- Link retail prices to bulk purchase prices for comparison

**Implementation:**
- Admin/user interface to input regular supermarket prices
- Automatic savings calculation: `(regular_price - bulk_price) * quantity`
- Savings summary card on completed runs showing:
  - Total amount spent (bulk purchase)
  - Estimated regular retail cost
  - Total savings amount and percentage
- Per-product savings breakdown
- Group-level and user-level savings statistics over time
- Optional: price scraping integration for automated retail price updates

**UI Components:**
- Savings badge on completed runs
- Detailed savings breakdown modal
- Historical savings chart on group/profile pages
- "You saved X% compared to regular prices" messaging

---

### Seller Group Type
**Status**: Future
**Priority**: Low
**Affected files**: Database schema, backend models/services, frontend group management

**Features:**
- New group type: "Seller" (vs current "Buyer" groups)
- Seller posts products they're selling with available quantities
- Users bid on available inventory (reverse auction model)
- Use case: Local farmers, bulk resellers, group organizers

**Schema Changes:**
- Add `group_type` enum to Group table: 'buyer' | 'seller'
- Seller-specific fields on Run:
  - Inventory limits per product
  - First-come-first-served vs allocation logic

**Implementation:**
- Seller UI for posting inventory
- Buyer UI for bidding on limited stock
- Allocation algorithm when demand exceeds supply
- Separate workflows for seller vs buyer groups

---
