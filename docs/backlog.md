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

### UI/UX Improvements
**Status**: Future
**Priority**: Medium
**Affected files**: Frontend components, run pages

**Features:**

1. **User Breakdown Across All States**
   - Currently only shown during distribution state
   - Show breakdown by user in all run states (planning, active, confirmed, shopping, adjusting)
   - Display each user's requested quantities and totals per user
   - Note: Per-product breakdown already exists (shopping list items)

2. **Total Run Price Display**
   - **Before shopping stage**: Show estimated total price with clear indication it's an estimate
   - **During shopping stage**: Show two values:
     - Current total for purchased items
     - Estimated total for remaining items
   - **After shopping**: Show final total
   - Update in real-time as items are purchased
   - Prominent placement in run header or summary card

3. **Currency Symbol Localization**
   - Fix hardcoded dollar signs ($) in various UI components
   - Use currency symbol from configuration or user locale
   - Support for multiple currencies (RSD, EUR, USD, etc.)
   - Centralize currency formatting logic

4. **Adjusting State: Allow Complete Bid Removal**
   - Current bug: Cannot remove bid completely during adjusting state
   - Should allow removing bid if it would match purchased quantity exactly
   - Investigate minimum quantity validation logic in adjusting state
   - Update BidPopup component to allow 0 quantity when appropriate

5. **Manual State Transition: Active to Confirmed**
   - Currently auto-transitions when all users mark ready
   - Change to require leader to click "Proceed to Confirmed" button
   - Similar to shopping stage transition (leader explicitly starts shopping)
   - Prevents premature state changes

6. **Decimal Rounding**
   - Round all decimal values to 2 decimal points throughout the app
   - Apply to quantities, prices, totals
   - Ensure consistent display formatting

7. **Edit Purchased Items**
   - Allow modifying purchased quantity and price after marking as purchased
   - Use same purchase popup with prefilled values
   - Use case: Correcting errors during shopping
   - Update totals and calculations accordingly

8. **Add Products During Shopping**
   - Leader can add new products/bids/shopping list items during shopping stage
   - Supports adding forgotten items or opportunistic purchases
   - Automatically add to shopping list
   - Track as new shopping list item

9. **Leader Can Modify User Bids**
   - Leader has ability to edit other users' bids (not just force equal distribution)
   - Makes price division and quantity adjustments easier
   - Useful during adjusting stage for fine-tuning allocations
   - Note: This needs more design work to determine exact workflow and permissions

---

### Invite Link Flow for Unauthenticated Users
**Status**: Future
**Priority**: High
**Affected files**: Frontend routing, auth flow, invite link handler

**Features:**
- Detect when unauthenticated user clicks invite link
- Store invite link/token temporarily (sessionStorage or URL param)
- Redirect to registration page with context
- After successful registration/login, redirect to original invite link
- Auto-join group using stored invite token

**Implementation:**
- Add redirect parameter to registration/login pages
- Store invite token in sessionStorage during redirect
- Update auth success handler to check for pending invite
- Automatically process group join after authentication
- Clear stored invite data after successful join
- Handle edge cases: expired tokens, invalid invites, already member

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
