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

**Still TODO:**

1. **Rate Limiting** - Use `slowapi` middleware:

   - Login/registration: 5 requests/minute
   - Bid placement: 20 requests/minute
   - General API: 100 requests/minute

2. **Database Backups** - Automated daily backups with pg_dump, S3 storage, retention policy
   - Manual backup script documented
   - Need automated backup to cloud storage
   - Need monitoring/alerting for backup failures
3. **Cache layer with redis**

---

## 🔧 Future Enhancements

---

### Mobile Web Responsiveness
**Status**: Not Started
**Priority**: High (user experience improvement)
**Affected files**: CSS files across frontend

**Problem:** App works great on desktop but has poor mobile experience. Fixed layouts, oversized typography, non-responsive modals, and touch targets too small.

**Current Issues:**
- Header not mobile-friendly (search bar layout breaks, buttons overflow)
- Modal widths are fixed (`min-width: 300px-400px`) causing horizontal scroll
- Button groups don't wrap on small screens
- Typography too large (h1 at `3.2em`)
- Grid layouts need mobile adjustments (some `minmax()` values too large)
- Form rows don't stack (two-column grids need to collapse)
- Page containers need responsive padding
- Touch targets may be too small (need 44px minimum)
- Complex breadcrumb/navigation needs simplification

**Implementation Plan:**

1. **Global Mobile Foundations** (`frontend/src/index.css`, `frontend/src/styles/utilities.css`)
   - Add mobile-friendly typography scales (reduce h1 from 3.2em)
   - Add responsive spacing utilities
   - Make modals responsive (remove fixed min-widths, add mobile-friendly max-widths with calc)
   - Update page container padding for mobile (reduce from 2rem to 1rem on small screens)
   - Make form rows stack on mobile (`.form-row` grid → single column at <768px)

2. **Header/Navigation** (`frontend/src/styles/App.css`)
   - Make header stack vertically on mobile (<768px)
   - Hide or collapse search bar on very small screens (<480px)
   - Make header buttons wrap or scroll horizontally
   - Reduce header padding on mobile (from 1.5rem to 1rem)
   - Make logout/admin buttons more touch-friendly (min 44px height)

3. **Component-Specific Updates**
   - **RunPage.css:**
     - Make product grid single column on mobile (<768px)
     - Stack run header elements vertically
     - Make participant lists more compact
     - Reduce info-grid to single column on mobile
   - **Groups.css:**
     - Ensure group cards stack nicely
     - Make header buttons stack or wrap on mobile
   - **Login.css:**
     - Minor padding adjustments for very small screens
   - **Modal Components (BidPopup, AddProductPopup, NewRunPopup, etc.):**
     - Remove fixed modal min-widths
     - Add mobile padding adjustments (reduce from 24px to 16px)
     - Ensure modals don't exceed viewport width

4. **Touch-Friendly Interactions**
   - Increase button min-height to 44px (iOS recommendation) for primary actions
   - Add more spacing between interactive elements in lists
   - Larger tap targets for icon buttons (edit, retract, etc.)
   - Increase padding on clickable cards

5. **Testing Breakpoints**
   - 320px: Small phones (minimum)
   - 375px: iPhone SE, common minimum
   - 480px: Larger phones
   - 768px: Tablets (existing breakpoint)
   - 1024px: Large tablets/small laptops

**Estimated Effort:** 2-4 hours (CSS-only changes, no component restructuring)
**Risk Level:** Low (CSS-only, easily reversible, no backend changes)
**Dependencies:** None

**Implementation Approach:**
- Mobile-first media queries where appropriate
- Use `@media (max-width: 768px)` and `@media (max-width: 480px)` breakpoints
- Update existing desktop styles progressively
- Test on real devices or browser dev tools
- No JavaScript changes needed
- Maintain existing utility-first CSS approach

---

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
