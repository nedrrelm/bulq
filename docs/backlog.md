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

### Authentication & User Management
**Status**: Future
**Priority**: High
**Affected files**: Backend auth routes, config, frontend registration

**Features:**
1. **Global Account Creation Flag**
   - Environment variable to enable/disable new registrations
   - Allow admin to close registration after initial users join
   - Existing users can still login when disabled
   - Clear message on registration page when disabled

2. **Remove Email, Username-Only Login**
   - Remove email field from User model
   - Use only username for authentication
   - Update registration/login forms
   - Migrate existing users (generate usernames from emails)

**Schema Changes:**
- Remove `email` column from User table
- Make `username` non-nullable and required
- Add unique constraint on username

**Configuration:**
- `ALLOW_REGISTRATION=true|false` environment variable

3. **User Profile Management**
   - Allow users to change their username
   - Allow users to change their password
   - Require current password for authentication before changes
   - Username uniqueness validation
   - Password strength requirements

**Implementation:**
- Add `/auth/change-username` endpoint (requires current password)
- Add `/auth/change-password` endpoint (requires current password + new password)
- Frontend profile/settings page with change forms
- Validation: username availability, password strength
- Update session after username change

---

### Run Comments & Context
**Status**: Future
**Priority**: Medium
**Affected files**: Database schema, backend models/services, frontend RunPage

**Features:**

2. **Product Bid Comments**
   - Each user can add notes to their bids
   - Examples: "Granny Smith apples", "Organic preferred", "Any brand fine"
   - Visible to all participants and leader during shopping
   - Helps shopper make better choices

**Schema Changes:**
- Add `description` text field to Run table (nullable)
- Add `comment` text field to ProductBid table (nullable)

**Implementation:**
- Add description field to run creation/edit form
- Show description prominently on run page
- Add comment textarea to BidPopup component
- Display bid comments on shopping page and run detail view

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
