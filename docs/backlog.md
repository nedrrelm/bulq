# Backlog

### Seller Group Type
**Status**: Future
**Priority**: Low
**Affected files**: Database schema, backend models/services, frontend group management


## 🔧 Future Enhancements


### Product Aliases (Multi-language Support)
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
