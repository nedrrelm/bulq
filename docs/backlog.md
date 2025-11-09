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

### Shopping List Export
**Status**: Future
**Priority**: Medium
**Affected files**: Backend routes, frontend shopping page

**Features:**
- Export shopping list as TXT format
- Export shopping list as JSON format
- Per-product view: all quantities aggregated by product
- Per-user view: breakdown showing each user's bids per product

**Implementation:**
- Add export endpoints: `/runs/{run_id}/shopping-list/export?format=txt|json&view=product|user`
- Frontend download buttons on shopping page
- TXT format: human-readable, printer-friendly
- JSON format: structured data for external tools

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

---

### UI/UX Improvements
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend components (RunPage, NotificationPanel, DistributionPage)

**Features:**
1. **Smart User Initials in Bid Circles**
   - When multiple users have same first letter, use 2 letters
   - Example: "Alice" and "Alex" → "Al" and "Ax" instead of both "A"
   - Fallback to numbers if needed: "A1", "A2"

2. **Post-Shopping Product Status Indicators**
   - On run page after shopping, show purchased vs not purchased
   - Similar to adjusting phase UI (orange highlights)
   - Visual indicators for:
     - ✅ Fully purchased (green)
     - ⚠️ Partially purchased (orange)
     - ❌ Not purchased (gray/crossed out)

3. **Mobile Notification Panel Fix**
   - Fix notification panel positioning on mobile
   - Currently shows only right half, left half off-screen
   - Make full panel visible with proper responsive layout

4. **Distribution Page Visibility & Views**
   - Show distribution page to all run participants (not just leader)
   - Everyone can see what they bought and amounts
   - Add view toggle: "By User" (default) and "By Product"
   - By Product view: group items by product showing all users' quantities
   - By User view: current behavior, items grouped per user

**Implementation:**
- Update user initial generation logic in frontend utils
- Add product status badges on RunPage after shopping state
- Fix CSS for notification panel mobile responsiveness
- Update distribution route permissions (remove leader-only check)
- Add view toggle component on DistributionPage

---

### Advanced Shopping Features
**Status**: Future
**Priority**: Medium
**Affected files**: Backend shopping service, frontend shopping page

**Features:**
1. **Additional Quantity Purchases**
   - Allow buying more of an already-purchased item
   - Update total quantity and price
   - Useful for deals/sales discovered during shopping
   - Track as separate purchase event or update existing

**Implementation:**
- Add "Add More" button on shopping page for purchased items
- Update ShoppingListItem with additional quantity tracking
- Recalculate totals and distribution

---

### Run Comments & Context
**Status**: Future
**Priority**: Medium
**Affected files**: Database schema, backend models/services, frontend RunPage

**Features:**
1. **Run Description/Comment**
   - Leader can add short description for run
   - Visible to all participants
   - Examples: "Bringing cooler", "Meeting at 2pm", "Focus on produce"
   - Editable by leader at any time

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

## 📝 Notes

- **Mobile App**: Native Kotlin Android app planned after web platform stable
