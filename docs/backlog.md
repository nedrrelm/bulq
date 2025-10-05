# Backlog

Feature backlog for Bulq development.

## Run Management

### Handle insufficient quantities during distribution
**Status**: Planned

When purchased quantity is less than requested, allow run leader to adjust distribution.

**Current behavior:**
- Assumes purchased quantity equals requested quantity for all users
- Works fine when everything was available

**Needed enhancement:**
- Detect when purchased < total requested
- Allow leader to adjust individual user allocations
- Show warnings/indicators for affected products
- Maintain fairness tracking (who got less this time)

**Implementation approach:**
- Add `allocated_quantity` field to distribution tracking
- Default to requested quantity
- Allow leader to edit allocations when total doesn't match
- Show visual diff between requested vs allocated

### Real-time updates with WebSockets
**Status**: Planned

Implement WebSocket connections for real-time updates during runs.

**Features:**
- Instant updates when users place/modify bids
- Live participant ready status changes
- Automatic UI refresh when run state transitions
- No need for manual page refresh to see others' changes

**Implementation approach:**
- Backend: Add WebSocket endpoint `/ws/runs/{run_id}` using FastAPI WebSocket support
- Track connected clients per run and broadcast updates
- Frontend: Connect to WebSocket on RunPage mount, listen for updates
- Message types: `bid_placed`, `bid_retracted`, `ready_toggled`, `state_changed`
- Handle reconnection and connection errors gracefully

**Benefits:**
- Better user experience for collaborative ordering
- Immediate feedback when teammates make changes
- Reduces confusion from stale data

## Product Discovery

### Product page and search
**Status**: Planned

Shows comparable products in different stores, allowing users to:
- Search for products
- Compare prices across stores
- View product details

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.

## Price Tracking

### Product price history
**Status**: Planned

Every time someone visits a store they can note the current price of a product.

**Features**:
- Track prices over time
- Support multiple values per product (for cases like markets where different sellers price differently)
- Show a graph over time of price changes
