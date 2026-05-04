# Backlog

### Bugs

1. sometimes users can't edit during adjusting (possibly when they pressed ready during planning)

### Features
1. distribution groups for each run (split total into multiple pickup points)
3. Create buyers clubs and sellers clubs
9. **Leader Can Modify User Bids**
   - Leader has ability to edit other users' bids (not just force equal distribution)
   - Makes price division and quantity adjustments easier
   - Useful during adjusting stage for fine-tuning allocations
   - Note: This needs more design work to determine exact workflow and permissions


### Security & Infrastructure


9. **Test DatabaseRepository** (2 days) - **CRITICAL**
   - DatabaseRepository used in production but has NO tests
   - Only MemoryRepository is tested
   - File: `tests/test_repository.py:228-239` has placeholder


10. **Auth library evaluation** — fastapi-users (email-only, maintenance mode), fastapi-login (JWT-only, no server-side sessions), authlib (OAuth only) all evaluated and rejected. Current custom auth (username + cookie + Redis sessions) is more capable than any available library. Consider targeted improvements instead: rate limiting on login, session invalidation on password change, session rotation.

11. Convert to async

---

## 🔧 Technical Debt & Code Quality

### Performance Optimization

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


## 🔧 Future Enhancements


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
