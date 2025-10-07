# Backlog

Feature backlog and technical debt for Bulq development.

## Technical Debt / Code Quality

---

### Add transaction management
**Status**: High Priority
**Affected files**: `app/repository.py`

**Problem:** No explicit transaction boundaries. Multi-step operations (e.g., create run + create participation) can leave inconsistent data on failure.

**Solution:** Implement transaction management within repository methods:
- Wrap multi-step operations in try/commit/rollback blocks
- Consider adding repository-level transaction context manager

---

### Add input validation
**Status**: Medium Priority
**Affected files**: `app/routes/*.py`

**Items to validate:**
- Quantity cannot be negative (Pydantic validator)
- Price cannot be negative (Pydantic validator)
- Other validations can wait

**Solution:** Add Pydantic validators to request models:
```python
@validator('quantity')
def quantity_non_negative(cls, v):
    if v < 0:
        raise ValueError('Quantity cannot be negative')
    return v
```

---

### Database migrations with Alembic
**Status**: Future (before production)
**Affected files**: New `alembic/` directory, `app/main.py`

**Problem:** Using `create_tables()` which can't handle schema changes. No migration history.

**Current limitations:**
- Can't add/remove/modify columns safely
- Can't track what schema version is deployed
- Can't roll back changes
- Breaks when models change in production

**Solution:** Set up Alembic for database migrations:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Workflow:**
1. Modify models in `models.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply: `alembic upgrade head`
5. Rollback if needed: `alembic downgrade -1`

Remove `create_tables()` call from `main.py` once migrations are in place.

---

### Introduce Service Pattern
**Status**: Medium Priority - Future
**Affected files**: New `app/services/` directory, all route files

**Problem:** Business logic is scattered across route handlers, making it:
- Hard to test (coupled to HTTP concerns)
- Difficult to reuse (when Android app is added)
- Mixed with authorization, validation, and response formatting
- Complex operations span 100+ lines in routes

**Current examples of complex route logic:**
- `place_bid()` in runs.py (264-421): 157 lines with validation, state checks, auto-transitions
- `complete_shopping()` in shopping.py (179-287): Shortage detection, distribution logic
- `finish_adjusting()` in runs.py (671-777): Quantity matching, distribution updates

**Solution:** Introduce service layer incrementally:

**Architecture:**
```
Routes → Services → Repository → Database/Memory
```

**Start with RunService first** (most complex domain logic):
```python
# app/services/run_service.py
class RunService:
    def __init__(self, repo: AbstractRepository):
        self.repo = repo
        self.state_machine = RunStateMachine()

    def place_bid(self, user_id, run_id, product_id, quantity, interested_only):
        """Handle bid placement logic, validation, and state transitions."""
        # All business logic here

    def transition_to_shopping(self, user_id, run_id):
        """Generate shopping list and transition state."""
        # Shopping list generation logic

    def complete_shopping(self, user_id, run_id):
        """Handle shopping completion, shortage detection, distribution."""
        # Shopping completion logic
```

**Then routes become thin:**
```python
@router.post("/{run_id}/bids")
async def place_bid(...):
    service = RunService(get_repository(db))
    result = await service.place_bid(...)
    await manager.broadcast(...)
    return {"message": "Success"}
```

**Implementation order:**
1. **RunService** - Most complex, highest value (state machine, bid logic, shopping)
2. **GroupService** - Group creation, membership, invite management
3. **DistributionService** - Distribution tracking and pickup management
4. **ProductService** - Product search, price history

**Benefits:**
- Testable business logic (no HTTP mocking needed)
- Reusable across HTTP API and future Android app
- Centralized transaction management
- Clearer separation of concerns
- Easier to reason about complex operations

**When to implement:**
- After completing high-priority repository cleanup
- When routes exceed ~150 lines
- Before starting Android app development
- When you need to share logic between platforms

---

## Future Enhancements

### Comprehensive test suite
**Status**: Future
**Affected files**: `backend/tests/`

**Problem:** Minimal or no tests currently. Need comprehensive coverage.

**Solution:** Implement:
- Unit tests for repository methods
- Integration tests for API endpoints
- Test fixtures for common scenarios
- WebSocket connection tests
- State machine transition tests
- Use pytest with fixtures and parametrize

---

### Secure password hashing (bcrypt)
**Status**: Future (critical before production)
**Affected files**: `app/auth.py`

**Problem:** Currently using SHA-256 for password hashing, which is extremely insecure (fast = vulnerable to brute force).

**Current code (auth.py:14-26):**
```python
def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"
```

**Solution:** Use bcrypt (designed to be slow for security):
```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

Also fix hardcoded SECRET_KEY fallback (auth.py:12) - should fail if not set:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set!")
```

---

### Add database indexes
**Status**: Future (before production)
**Affected files**: `app/models.py`

**Problem:** No indexes defined on frequently queried fields, will cause slow queries at scale.

**Solution:** Add indexes on:
- Foreign keys: `group_id`, `store_id`, `user_id`, `run_id`, `product_id`, `participation_id`
- Unique lookups: `email`, `invite_token`
- Filtered queries: `state` (in Run model)

Example:
```python
class User(Base):
    email = Column(String, unique=True, nullable=False, index=True)

class Run(Base):
    state = Column(String, nullable=False, default="planning", index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False, index=True)
```

---

### Implement caching
**Status**: Future
**Affected files**: Multiple

**Problem:** Store lists, product lists fetched on every request - inefficient.

**Solution:**
- Use Redis for caching
- Cache store list (rarely changes)
- Cache product lists per store
- Cache with TTL (time-to-live)
- Invalidate on updates

---

### Add pagination
**Status**: Future
**Affected files**: `app/routes/*.py`

**Problem:** Endpoints like `get_my_groups`, `get_shopping_list`, `get_group_runs` will break with large datasets.

**Solution:** Add pagination parameters:
```python
@router.get("/items")
async def get_items(skip: int = 0, limit: int = 100):
    return repo.get_items(skip=skip, limit=limit)
```

Implement in repository methods with `OFFSET` and `LIMIT`.

---

### Rate limiting
**Status**: Future (before production)
**Affected files**: `app/main.py`, `app/routes/auth.py`

**Problem:** No protection against abuse - login, registration, bid placement all unprotected.

**Solution:** Use `slowapi` middleware:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
```

Apply to:
- Login/registration: 5 requests/minute
- Bid placement: 20 requests/minute
- General API: 100 requests/minute

---

## Frontend Technical Debt / Code Quality

---

### 🔴 CRITICAL: No Error Boundary
**Status**: High Priority - User Experience
**Affected files**: App.tsx, main.tsx

**Problem:** If any component throws an error, the entire app crashes with a blank screen. No error boundary to catch and display errors gracefully.

**Solution:** Add React Error Boundary in App.tsx or main.tsx:
```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    console.error('App error:', error, errorInfo)
  }
  render() {
    if (this.state.hasError) {
      return <div className="error-page">Something went wrong</div>
    }
    return this.props.children
  }
}
```

---

### 🟠 HIGH: Inconsistent State Management Patterns
**Status**: High Priority
**Affected files**: Groups.tsx:95-161, GroupPage.tsx, RunPage.tsx

**Problem:** Groups.tsx has manual WebSocket management with cleanup issues:
```typescript
// Line 95-161: Manual WebSocket array management
useEffect(() => {
  const wsConnections: any[] = []  // ⚠️ 'any' type, poor typing
  groups.forEach((group) => { /* ... */ })
  return () => wsConnections.forEach(ws => ws.close())
}, [groups.map(g => g.id).join(',')]) // ⚠️ Hacky dependency
```

GroupPage.tsx and RunPage.tsx use the custom `useWebSocket` hook properly, but Groups.tsx doesn't.

**Solution:** Refactor Groups.tsx to use the `useWebSocket` hook consistently.

---

### 🟠 HIGH: Data Refetching After Mutations
**Status**: High Priority - Performance
**Affected files**: RunPage.tsx:207-214, 242-250; ShoppingPage.tsx:88-89; Groups.tsx:170-183

**Problem:** After POST/DELETE operations, components fetch the entire resource again:
- RunPage.tsx:207-214 (after bid retraction)
- RunPage.tsx:242-250 (after bid placement)
- ShoppingPage.tsx:88-89 (after adding price)
- Groups.tsx:170-183 (after group creation)

Network overhead, poor UX (brief loading states), doesn't leverage WebSocket updates.

**Solution:** Either trust WebSocket updates OR optimistically update local state, then sync with server response.

---

### 🟠 HIGH: Missing Loading/Error States
**Status**: Medium Priority
**Affected files**: DistributionPage.tsx:123-128, ProductPage.tsx:186-191

**Problem:** Some components handle loading poorly:
- DistributionPage.tsx shows raw text "Loading..." with no styling
- ProductPage.tsx inconsistent with other pages

**Solution:** Create reusable `<LoadingSpinner />` and `<ErrorAlert />` components.

---

### 🟠 HIGH: Inline Styles Mixed with CSS Classes
**Status**: Medium Priority - Code Quality
**Affected files**: RunPage.tsx:456-467, BidPopup.tsx:58-73, GroupPage.tsx:223

**Problem:** Inline styles violate separation of concerns and make theming difficult:
```typescript
// RunPage.tsx:456
<span className="run-state" style={{
  backgroundColor: stateDisplay.color,
  color: 'white',
  padding: '6px 16px',
  // ...
}}>
```

**Solution:** Use CSS classes with CSS variables for dynamic values.

---

### 🟡 MEDIUM: Navigation Smell - Manual URL Management
**Status**: Medium Priority - Architecture
**Affected files**: App.tsx:51-105, 186-251

**Problem:** The app uses manual `window.history.pushState()` and URL parsing instead of React Router:
```typescript
useEffect(() => {
  const path = window.location.pathname
  const inviteMatch = path.match(/^\/invite\/(.+)$/)
  // ...manual routing logic
}, [])
```

**Issues:**
- No back button support
- No browser history management
- URL doesn't update on browser back/forward
- Breaks user expectations

**Solution:** Use React Router properly (already imported but not fully utilized):
```typescript
import { BrowserRouter, Routes, Route, useParams, useNavigate } from 'react-router-dom'
```

---

### 🟡 MEDIUM: WebSocket Connection Leaks
**Status**: Medium Priority
**Affected files**: Groups.tsx:95-161

**Problem:** The WebSocket cleanup has a race condition. If `groups` changes frequently, this creates/destroys many WebSocket connections.

**Solution:** Use the existing `useWebSocket` hook with proper connection pooling.

---

### 🟡 MEDIUM: No Request Deduplication
**Status**: Medium Priority - Performance
**Affected files**: App.tsx, Groups.tsx, RunPage.tsx

**Problem:** Multiple components can trigger the same fetch simultaneously:
- Product search in App.tsx header
- Product search in Groups.tsx
- Run details fetched by RunPage when navigating

**Solution:** Implement a simple request cache or use a library like React Query/SWR.

---

### 🟡 MEDIUM: Console.log Statements in Production
**Status**: Medium Priority
**Affected files**: App.tsx:308, Groups.tsx:150, useWebSocket.ts:45, 62, 66, 74

**Problem:** Console statements in production code:
```typescript
console.log('🔵 App: Rendering main app. currentView:', currentView, 'user:', user)
```

**Solution:** Use a logging utility that can be disabled in production:
```typescript
const isDev = import.meta.env.DEV
const log = isDev ? console.log : () => {}
```

---

### 🟡 MEDIUM: Magic Numbers Throughout
**Status**: Low Priority - Code Quality
**Affected files**: useWebSocket.ts:22, 120; ShoppingPage.tsx:256; RunPage.tsx:619

**Problem:** Unexplained constants:
```typescript
reconnectInterval = 3000,  // What's 3000?
maxReconnectAttempts = 5   // Why 5?
sendMessage('ping'), 30000 // Why 30 seconds?
```

**Solution:** Extract to named constants:
```typescript
const WEBSOCKET_RECONNECT_INTERVAL = 3000 // ms
const WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5
const WEBSOCKET_HEARTBEAT_INTERVAL = 30000 // ms
```

---

### 🟢 LOW: Unused Props/Variables
**Status**: Low Priority - Cleanup
**Affected files**: Groups.tsx:37, ShoppingPage.tsx:31

**Problem:**
- Groups.tsx:37 - `onProductSelect` prop is destructured but never used
- ShoppingPage.tsx:31 - `showPricePopup` state read but logic could be simplified

**Solution:** Remove unused code or implement the missing functionality.

---

### 🟢 LOW: Inconsistent Button Styling
**Status**: Low Priority - Polish
**Affected files**: App.tsx:313, 355

**Problem:** Some buttons use inline styles, some use CSS classes:
- App.tsx:313 uses inline `style={{ cursor: 'pointer' }}`
- App.tsx:355 uses `className="logout-button"`

**Solution:** Standardize on CSS classes from utilities.css.

---

### 🟢 LOW: Duplicate getStateLabel Functions
**Status**: Low Priority - DRY Violation
**Affected files**: Groups.tsx:45-66, GroupPage.tsx:108-129, RunPage.tsx:375-396

**Problem:** The same state label mapping logic is copied 3 times.

**Solution:** Extract to `src/utils/runStates.ts`:
```typescript
export const getStateLabel = (state: string) => { ... }
export const getStateColor = (state: string) => { ... }
```

---

### 🟢 LOW: No Keyboard Navigation in Modals
**Status**: Low Priority - Accessibility
**Affected files**: All modal components

**Problem:** Most modals handle `Escape` to close, but:
- No `Tab` trapping (focus escapes modal)
- No `Enter` to submit from anywhere in form
- BidPopup.tsx and AddProductPopup.tsx handle some keyboard events, but inconsistently

**Solution:** Use a modal library or implement proper focus management.

---

### 🟢 LOW: Alert/Confirm Dialogs Instead of UI Components
**Status**: Low Priority - UX
**Affected files**: RunPage.tsx:217, 256, 317, 344; GroupPage.tsx:189, 208

**Problem:** Native browser dialogs break UI consistency:
```typescript
alert('Failed to place bid. Please try again.')
if (!confirm('Are you sure...'))
```

**Solution:** Create custom `<Toast />` notification and `<ConfirmDialog />` components.

---

### 🟢 LOW: Overly Nested Ternary Operators
**Status**: Low Priority - Readability
**Affected files**: RunPage.tsx:804-815

**Problem:** Complex nested ternaries hurt readability:
```typescript
adjustingMode={run?.state === 'adjusting'}
minAllowed={
  run?.state === 'adjusting' && selectedProduct.current_user_bid && selectedProduct.purchased_quantity !== null
    ? Math.max(0, selectedProduct.current_user_bid.quantity - ...)
    : undefined
}
```

**Solution:** Extract to computed variables for readability.

---

### 🟢 LOW: Missing PropTypes/Runtime Validation
**Status**: Low Priority - Type Safety
**Affected files**: All components

**Problem:** TypeScript interfaces are defined, but no runtime validation:
- No validation that `runId` is a valid UUID
- No validation that API responses match expected shape

**Solution:** Consider adding runtime validation with Zod or similar.

---

### 🟢 LOW: CSS Organization Duplication
**Status**: Low Priority - Maintainability
**Affected files**: Groups.css, GroupPage.css, RunPage.css, multiple component CSS files

**Problem:** Component-specific CSS files have duplication:
- Similar grid layouts in Groups.css, GroupPage.css, RunPage.css
- Repeated `.run-state` styles in multiple files
- Inconsistent spacing (some use px, some use rem)

**Solution:** Extract more common patterns to utilities.css.

---

## Frontend Performance

### Unnecessary Re-renders
**Status**: Medium Priority
**Affected files**: RunPage.tsx

**Problem:** RunPage.tsx with large product lists re-renders on every WebSocket message, even for unrelated products.

**Solution:** Use `React.memo` for ProductItem components or implement shouldComponentUpdate logic.

---

### No Code Splitting
**Status**: Medium Priority
**Affected files**: All component imports

**Problem:** All components load on initial page load. With 14+ components, this creates a large initial bundle.

**Solution:** Implement lazy loading:
```typescript
const ShoppingPage = lazy(() => import('./components/ShoppingPage'))
const DistributionPage = lazy(() => import('./components/DistributionPage'))
```

---

### SVG Graph Rendering Performance
**Status**: Low Priority
**Affected files**: ProductPage.tsx:30-149

**Problem:** SVG graphs rendered inline can be expensive with many price points.

**Solution:** Consider using a charting library (Chart.js, Recharts) or memoize the graph component.

---

## Frontend Architecture Improvements

### No Custom Hook Reuse
**Status**: Medium Priority - Code Reusability
**Affected files**: Multiple components with repeated patterns

**Problem:** Only one custom hook (`useWebSocket`), but many patterns repeat:
- Fetching with loading/error states
- Form handling
- Modal open/close logic

**Suggested hooks:**
```typescript
useApi(endpoint, options)  // Handles fetch, loading, error
useModal()                 // Handles open/close, ESC key
useForm(initialValues)     // Handles form state, validation
```

---

### No Context for Global State
**Status**: Medium Priority - State Management
**Affected files**: App.tsx (prop drilling throughout)

**Problem:** User, current view, selected IDs are all prop-drilled through App.tsx.

**Solution:** Use React Context for:
- Authentication (user, login, logout)
- Navigation state
- Theme/preferences

---

### API Layer Missing
**Status**: High Priority - Code Organization
**Affected files**: All components doing fetch() calls

**Problem:** Every component does its own `fetch()` calls with duplicated:
- credentials: 'include'
- Error handling
- JSON parsing
- URL construction

**Solution:** Create `src/api/` module:
```typescript
// src/api/client.ts
export const api = {
  get: (endpoint) => fetch(`${API_BASE_URL}${endpoint}`, { credentials: 'include' }),
  post: (endpoint, data) => { ... },
  delete: (endpoint) => { ... },
  // ... with proper error handling
}

// src/api/runs.ts
export const runsApi = {
  getDetails: (runId: string) => api.get(`/runs/${runId}`),
  placeBid: (runId: string, data: BidData) => api.post(`/runs/${runId}/bids`, data),
  // ...
}
```

---

### No Input Validation
**Status**: Medium Priority - Data Quality
**Affected files**: BidPopup, Login, NewGroupPopup, NewRunPopup, ShoppingPage

**Problem:** Forms trust user input and send it directly to the backend:
- BidPopup allows negative quantities (checked after submission)
- Email format not validated client-side
- No max length on text inputs

**Solution:** Add client-side validation with a library (react-hook-form, formik) or custom validation.

---

## Product Discovery

### Product families
**Status**: Planned

Allows using general terms (e.g., "rice") instead of specific variants (e.g., "sushi rice", "jasmine rice", "basmati rice").

This creates a hierarchy/grouping system for products.
