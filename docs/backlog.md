# Backlog

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

2. **Database Backups** - Automated daily backups with pg_dump, S3 storage, retention policy
   - Manual backup script documented
   - Need automated backup to cloud storage
   - Need monitoring/alerting for backup failures
3. **Cache layer with redis**

---

## 🔧 Future Enhancements

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

### Localization
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend i18n, backend translations, database

**Languages:**
- English (en)
- Russian (ru)
- Serbian (sr)

**Implementation:**
- Use i18next or similar library for frontend
- Store user language preference
- Translate UI strings, labels, messages
- Consider product name translations (via multiple names feature)

---

### Progressive Web App (PWA)
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend build config, service worker, manifest

**Features:**
- Offline support with service workers
- Install prompt for mobile devices
- App-like experience on mobile
- Push notifications for run updates
- Cache static assets for faster loading
- Background sync for bid updates

**Implementation:**
- Add `manifest.json` with app metadata
- Configure Vite PWA plugin
- Implement service worker for caching strategy
- Add offline fallback pages
- Test install flow on iOS/Android

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
