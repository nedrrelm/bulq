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

## 🐛 Bugs

---

### Product Bidding Issues
**Status**: To Investigate
**Priority**: High
**Affected files**: `backend/app/services/bid_service.py`, `backend/app/api/routes/runs.py`

**Issues:**
1. **Adding products to a run which don't have a store listed doesn't work**
   - Error: "Product not found" (404)
   - Log: `timestamp=2025-11-07T08:31:39.383720Z level=WARNING logger=app.errors.handlers message="Application error: Product not found" request_id=97537890-0f56-4106-962c-fc99c757322d path=/runs/02fb2b17-818e-47e2-bca5-c3752e15d6ed/bids method=POST status_code=404`
   - Need to allow bidding on products without store availability

2. **Admin page for products shows store as always empty**
   - Store field not displaying correctly on admin products page
   - Need to investigate product-store relationship display

---

## 🔧 Future Enhancements

---

### Admin Panel Improvements
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend admin pages, backend routes

**Features:**
- Allow modifying products (name, brand, unit, etc.)
- Allow modifying stores (name, address, chain, opening hours)
- Admin CRUD operations for all entities

---

### Product Management Enhancements
**Status**: Future
**Priority**: Medium
**Affected files**: Database schema, backend models, frontend components

**Features:**
1. **Multiple Product Names** (Aliases/Translations)
   - Allow products to have multiple names for search/display
   - Support different languages/regional names
   - Examples: "Soda" vs "Pop", "Chips" vs "Crisps"

2. **Product Categories**
   - Hierarchical category system (e.g., Food > Dairy > Milk)
   - Filter products by category
   - Category-based organization in UI

3. **Product Families**
   - Group related products (e.g., different sizes of same item)
   - Family-level pricing comparison
   - Bulk family operations

4. **Product Connections**
   - Separate entity for flexible product relationships
   - Connection types:
     - "type of" (hierarchy/taxonomy)
     - "good pairing with" (recommendations)
     - "alternative" (substitutes)
     - "complementary" (often bought together)
   - Bidirectional connections with optional metadata
   - Use for smart recommendations and discovery

**Schema Changes:**
- `ProductName` table (product_id, name, language, is_primary)
- `Category` table (id, name, parent_id)
- `ProductCategory` junction table
- `ProductFamily` table (id, name, description)
- `ProductConnection` table (product_a_id, product_b_id, connection_type, metadata)

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

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
