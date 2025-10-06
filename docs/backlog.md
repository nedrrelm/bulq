# Backlog

Feature backlog for Bulq development.

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

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.
