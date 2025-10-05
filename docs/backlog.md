# Backlog

Feature backlog for Bulq development.

## Run Management

### Allow users to progress a run
**Status**: In Progress

Runs should be progressable through states (planning → active → confirmed → shopping → distributing → completed).

**Implementation details:**
- Run leader (user who created the run) can manually control state transitions
- Automatic transitions when conditions are met (e.g., planning → active when others bid)
- Users mark themselves as "ready" during active state
- Automatic transition to confirmed when all bidders are ready
- Distribution tracking before final completion

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

## Run Pages

### Active run page
**Status**: Planned

Show shopping list with detailed tracking:
- Each item on the list
- Track prices for each item (can be multiple)
- Amount bought
- Price paid

### Completed run page
**Status**: Planned

Post-run settlement view showing:
- Who is supposed to get how much of what
- Who picked up their part
- Who paid how much
