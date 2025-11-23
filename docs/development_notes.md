# Development Notes

This document captures architectural decisions, their reasoning, code style rules, and development setup for the Bulq project.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Architecture Decisions](#architecture-decisions)
- [Code Style Rules](#code-style-rules)
- [Design Principles](#design-principles)
- [Common Patterns](#common-patterns)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Contributing Guidelines](#contributing-guidelines)

---

## Architecture Overview

### Containerized Architecture

- **Separate Docker containers** for backend, frontend, and database
- **Backend**: FastAPI application running in Python container
- **Database**: PostgreSQL running in dedicated container with UUIDs for primary keys
- **Frontend**: React + TypeScript application served with Caddy
- **Real-time Updates**: WebSocket connections for live bid tracking

### Core Architecture Decisions

- **Monolithic Backend**: Single FastAPI application, suitable for expected load
- **Containerized Development**: Docker Compose for consistent environments
- **Frontend-Backend Separation**: React frontend, FastAPI backend with CORS
- **WebSockets**: For real-time bid updates during group orders
- **No Image Storage**: Avoiding complexity, text-based product descriptions only
- **PostgreSQL with UUIDs**: For primary keys across all entities

### Core Entity Logic

**Run States Flow:**
`planning` → `active` → `confirmed` → `shopping` → `distributing` → `completed`

- Can transition to `cancelled` from any state before `distributing`
- **planning**: Run leader's initial bids only
- **active**: Multiple users bidding, with "ready" checkboxes
- **confirmed**: All users ready, awaiting shopping trip
- **shopping**: Shopping in progress
- **distributing**: Items being distributed to members
- **completed**: Final historical record

**ProductBid System:**
- **interested_only**: Boolean flag for expressing interest without commitment
- **quantity**: Required for items to make it to shopping list
- Real-time totals calculated from sum of quantities per product per run

**Shopping List Generation:**
- Calculated view, not stored entity
- Confirmed products = products with quantity > 0
- Quantities = sum of all user bids per product
- Assigned to designated_shoppers stored in Run

### Non-Features (Intentionally Excluded)

- In-app payments (users settle manually)
- Chat functionality (users communicate externally)
- Image uploads/storage
- Complex shopping assignment tracking

### Data Entry Strategy

- Manual store/product entry initially
- Future: Store API integration or scraping
- Price tracking built into Product entity

---

## Development Setup

### Environment Configuration

Bulq uses a unified `.env` file for both development and production configurations.

**First-time setup:**
```bash
# Copy the example environment file
cp .env.example .env

# The default configuration is already set for development
# No changes needed for local development
```

The `.env` file contains:
- **DEV_*** variables for development
- **PROD_*** variables for production
- **Final variables** that reference either DEV or PROD values
- Switch between modes by changing the `ENV` variable and updating final variable references

**For production deployment**, see [Deployment Guide](deployment.md).

### Quick Start with Docker Compose

The easiest way to run the application is using docker compose:

```bash
docker compose up -d
```

This will start both the backend service on `http://localhost:8000` and frontend on `http://localhost:3000`.

### Backend Setup

The backend is a FastAPI application managed with `uv` for dependency management.

**Local Development:**
```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Docker (individual container):**
```bash
cd backend
docker build -t bulq-backend .
docker run -p 8000:8000 bulq-backend
```

**Docker Compose (recommended):**
```bash
docker compose up -d backend
```

The backend API will be available at `http://localhost:8000` with automatic API documentation at `http://localhost:8000/docs`.

**Backend Features:**
- CORS configured for frontend communication (`localhost:3000`)
- Health check endpoint at `/health`
- Automatic API documentation with FastAPI

### Frontend Setup

The frontend is a React + TypeScript application managed with Volta and served with Caddy.

**Local Development:**
```bash
cd frontend
npm run dev
```

**Docker (individual container):**
```bash
cd frontend
docker build -t bulq-frontend .
docker run -p 3000:3000 bulq-frontend
```

**Docker Compose (recommended):**
```bash
docker compose up -d frontend
```

The frontend will be available at `http://localhost:3000` and includes a backend connection test.

**Technology Stack:**
- **Package Manager**: npm with Volta for Node.js version management
- **Build Tool**: Vite
- **Framework**: React + TypeScript
- **Web Server**: Caddy (for production builds)

**CSS Guidelines:**
- **Reuse utility classes** from `utilities.css` whenever possible
- Common components available: `.card`, `.card-lg`, `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-success`, `.modal`, `.modal-overlay`, `.form-group`, `.form-input`, `.form-label`, `.alert`, `.alert-error`, `.alert-success`, `.empty-state`, `.breadcrumb`
- Only create component-specific CSS when absolutely necessary
- Use CSS variables (e.g., `var(--color-primary)`) for colors and common values
- This keeps the codebase DRY and makes styling changes easier

---

## Testing

The backend includes a comprehensive test suite covering all components.

### Running Tests

**Run all tests:**
```bash
docker compose run --rm backend uv run --extra dev pytest tests/ -v
```

**Run specific test file:**
```bash
docker compose run --rm backend uv run --extra dev pytest tests/test_state_machine.py -v
```

**Run with coverage report:**
```bash
docker compose run --rm backend uv run --extra dev pytest tests/ --cov=app --cov-report=html
```

**Run only unit tests:**
```bash
docker compose run --rm backend uv run --extra dev pytest -m unit
```

**Run only integration tests:**
```bash
docker compose run --rm backend uv run --extra dev pytest -m integration
```

### Test Coverage

The test suite includes:
- ✅ **Authentication tests** - Registration, login, sessions, password hashing
- ✅ **Repository tests** - Database and in-memory implementations
- ✅ **Service layer tests** - Business logic for all services
- ✅ **Route integration tests** - All API endpoints
- ✅ **State machine tests** - Run state transitions and validation
- ✅ **Model tests** - Database models, relationships, constraints
- ✅ **WebSocket tests** - Real-time communication

For detailed testing documentation, see [`backend/tests/README.md`](../backend/tests/README.md).

---

## Development Workflow

### Full Stack Development

1. Use `docker compose up -d` for full stack development
2. Individual containers can be rebuilt: `docker compose up -d --build backend`
3. Frontend includes backend connectivity test for integration verification
4. API documentation available at `/docs` endpoint

### Code Quality

**Linting with Ruff:**
```bash
# Check code style
docker compose exec backend uv run --extra dev ruff check app/

# Auto-fix issues
docker compose exec backend uv run --extra dev ruff check app/ --fix

# Format code
docker compose exec backend uv run --extra dev ruff format app/
```

Note: Dev dependencies (including ruff) are installed when `BUILD_DEV_DEPS=true` in `.env`

---

## Troubleshooting

### Development Mode

**Frontend shows "Backend connection failed"**
1. Ensure both services are running: `docker compose ps`
2. Check backend logs: `docker compose logs backend`
3. Verify CORS configuration in backend

**Port conflicts**
- Backend: 8000 (internal only with reverse proxy)
- Frontend: 3000 (development), 80/443 (production)
- Stop services: `docker compose down`
- Check processes: `lsof -i :3000` or `lsof -i :8000`

**Container build issues**
- Clean rebuild: `docker compose build --no-cache`
- Remove old images: `docker system prune`

### Production Mode

See [Production Deployment Guide - Troubleshooting](deployment.md#troubleshooting) for:
- SSL certificate issues
- CORS errors
- WebSocket connection failures
- Database connection problems

---

## Architecture Decisions

### Service Layer Pattern

**Decision**: Implement a three-layer architecture (Routes → Services → Repository)

**Reasoning**:
- **Separation of Concerns**: Routes handle HTTP/validation, Services contain business logic, Repository manages data access
- **Testability**: Business logic can be tested independently of HTTP layer
- **Reusability**: Services can be called from REST routes, WebSocket handlers, CLI tools, etc.
- **Maintainability**: Changes to business rules don't require touching route handlers

**Implementation**:
```
Routes (thin)         → HTTP request/response, auth, validation
Services (thick)      → Business logic, state transitions, authorization
Repository (abstract) → Data access (DB or in-memory)
```

---

### Repository Pattern with Dual Implementation

**Decision**: Abstract repository interface with DatabaseRepository and InMemoryRepository

**Reasoning**:
- **Development Speed**: InMemoryRepository with seed data enables instant development without DB setup
- **Testing**: Tests run faster with in-memory data, no DB cleanup needed
- **Flexibility**: Easy to switch between modes via `REPO_MODE` environment variable
- **Production Ready**: DatabaseRepository for real PostgreSQL persistence

**Trade-offs**:
- Must maintain two implementations (though interface ensures consistency)
- In-memory seed data needs manual updates when schema changes

---

### Session-Based Authentication (Not JWT)

**Decision**: HTTP-only session cookies with server-side session storage

**Reasoning**:
- **Security**: HTTP-only cookies not accessible to JavaScript, immune to XSS attacks
- **Simplicity**: No token refresh logic, no client-side token management
- **Revocation**: Sessions can be invalidated server-side immediately
- **Trust Model**: Friend group app doesn't need stateless auth for scalability

**Trade-offs**:
- Server must maintain session state (acceptable for our scale)
- Not suitable for distributed systems without session store (Redis)

---

### State Machine for Run Lifecycle

**Decision**: Explicit state machine with validated transitions

**Reasoning**:
- **Data Integrity**: Prevents invalid state transitions (e.g., can't shop before confirming)
- **Business Logic**: Codifies the run workflow in one place (`run_state.py`)
- **Debugging**: Clear audit trail via state transition timestamps
- **UI Logic**: Frontend can derive available actions from current state

**States**: `planning → active → confirmed → shopping → adjusting? → distributing → completed`

**Alternative Rejected**: Event sourcing (too complex for current needs)

---

### Adjusting State for Quantity Shortages

**Decision**: Special state when purchased quantity < requested quantity

**Reasoning**:
- **Fairness**: All participants adjust bids together rather than leader deciding
- **Transparency**: Visual indicators show which products need adjustment
- **Constraint**: Downward-only edits prevent bid inflation
- **Validation**: Can't proceed until totals match purchased quantities

**Implementation Details**:
- Orange highlighting for products needing adjustment
- Disabled edit/retract for satisfied products
- Min/max constraints enforced in BidPopup

---

### WebSocket for Real-Time Updates

**Decision**: WebSocket connections for run participants

**Reasoning**:
- **User Experience**: Immediate feedback when someone places/updates bids
- **Coordination**: Multiple people shopping together see live updates
- **Engagement**: Feels collaborative, not polling-based
- **Efficiency**: Push notifications vs. polling every N seconds

**Scope**: Only for active runs, not global notifications (those use polling)

---

### No In-App Payments

**Decision**: Manual settlement outside the app

**Reasoning**:
- **Trust Model**: Designed for friend groups who settle externally
- **Complexity**: Payment processing adds regulatory, security, UX overhead
- **Focus**: Keep MVP focused on coordination and calculation tools
- **Future Option**: Can add payment integration if user base grows

---

### Store-Agnostic Products

**Decision**: Products linked to stores via ProductAvailability junction table

**Reasoning**:
- **Flexibility**: Same product (e.g., "Milk 1L") available at multiple stores
- **Price Tracking**: Historical prices across stores and runs
- **Deduplication**: Avoid duplicate products for each store
- **Discovery**: Users can find which stores carry a product

**Schema**: `Product ←→ ProductAvailability ←→ Store`

---

### CSS Utility-First Approach

**Decision**: Reusable utility classes in `utilities.css`, minimal component CSS

**Reasoning**:
- **DRY Principle**: Avoid repeating button/card/form styles across components
- **Consistency**: Design system tokens ensure uniform look
- **Maintainability**: Global style changes in one place
- **Performance**: Smaller CSS bundles

**Rule**: Only create component-specific CSS when absolutely necessary

---

### Structured Logging with Extra Context

**Decision**: All logs must include `extra` dict with context

**Reasoning**:
- **Observability**: Enables filtering/searching logs by user_id, run_id, etc.
- **Debugging**: Trace requests across distributed logs with structured data
- **Production**: Works with log aggregation tools (ELK, Datadog, etc.)

**Pattern**:
```python
logger.info(
    "Event description",
    extra={"user_id": str(user.id), "run_id": str(run.id)}
)
```

---

### UUIDs for Primary Keys

**Decision**: Use UUIDs instead of auto-incrementing integers

**Reasoning**:
- **Security**: Non-guessable IDs, can't enumerate resources
- **Distribution**: Can generate IDs client-side or across services
- **Merging**: No ID conflicts when merging data from different sources
- **Future-Proof**: Easier to shard/partition database

**Trade-offs**:
- Slightly larger storage (16 bytes vs 4-8 bytes)
- Less human-readable in logs (mitigated by structured logging)

---

## Code Style Rules

### Python (Backend)

#### File Naming
- **snake_case** for all Python files: `run_service.py`, `test_state_machine.py`
- **Descriptive names**: `reassignment_service.py` not `rs.py`

#### Logging
- **Always use context-aware logger** with `get_logger(__name__)`
  ```python
  from app.request_context import get_logger

  logger = get_logger(__name__)  # At module level
  ```
- **Request IDs are automatic**: Every log entry within a request includes the same `request_id` for tracing
- **Always use structured logging** with `extra` dict
- **Message format**: Describe the event, not the data
  ```python
  # Good
  logger.info("User registered", extra={"user_id": str(user.id)})
  # Automatically includes: request_id, timestamp, level

  # Bad
  logger.info(f"User {user.id} registered")
  ```
- **Background tasks**: Set context manually
  ```python
  from app.request_context import set_request_id, generate_request_id

  set_request_id(generate_request_id())
  logger.info("Background task started")  # Now includes request_id
  ```

#### Type Hints
- **Required** for all function parameters and return types
- Use `from typing import` for complex types
- Example:
  ```python
  def get_run(run_id: UUID, user: User) -> Dict[str, Any]:
  ```

#### Response Models
- **Prefer Pydantic models** over raw dicts for type safety
- Use `response_model` in route decorators
- Example:
  ```python
  @router.get("/users/{id}", response_model=UserResponse)
  ```

#### Error Handling
- **Use custom exceptions** from `exceptions.py`
- Include context in error details
- Example:
  ```python
  raise NotFoundError("Run", run_id)
  ```

#### Service Methods
- **Keep methods focused** - single responsibility
- **Extract helpers** if method exceeds ~50 lines
- **Document complex logic** with docstrings

#### Commit Messages
- **Simple, descriptive one-liners**
- Focus on **what** changed, not how or why
- Examples: "Add user authentication", "Fix bid retraction bug"
- **No AI mentions** in commit messages

---

### TypeScript/React (Frontend)

#### File Naming
- **PascalCase** for React components: `RunPage.tsx`, `BidPopup.tsx`
- **Matching CSS files**: `RunPage.css` alongside `RunPage.tsx`
- **kebab-case** for utilities: `run-states.css`, `utilities.css`
- **lowercase** for config: `vite.config.ts`, `package.json`

#### Component Structure
- **Functional components** with hooks (no class components)
- **Custom hooks** for reusable logic: `useWebSocket`, `useApi`
- **Context providers** for global state: `AuthContext`, `NotificationContext`

#### CSS Guidelines
- **Reuse utility classes** from `utilities.css` whenever possible
- **Only create component CSS** for unique layouts/visuals
- **Use CSS variables** for colors: `var(--color-primary)`
- **Import shared styles**: `run-states.css` for state badges

#### API Integration
- **Type-safe API calls** with TypeScript interfaces
- **Centralized API client** in `src/api/client.ts`
- **Error handling** with try/catch and user-friendly messages

#### State Management
- **Context for global state** (auth, notifications)
- **Local state** for component-specific data
- **Avoid prop drilling** - use context when passing 3+ levels deep

---

### General Rules

#### Documentation
- **Update README** when adding major features
- **Document complex logic** in code comments
- **Keep docs in sync** with code changes
- **No auto-generated docs** unless explicitly requested

#### Testing
- **Write tests** for business logic in services
- **Test state transitions** thoroughly
- **Mock external dependencies** (DB, WebSocket)
- **Run tests before committing**: `pytest tests/ -v`

#### Code Quality
- **Run ruff before committing**: `ruff check app/ && ruff format app/`
- **Fix all linting errors** - aim for zero errors
- **Use ruff format** for consistent code style
- **Docker command**: `docker compose run --rm backend uv run ruff check app/`
- **Auto-fix**: `docker compose run --rm backend uv run ruff check app/ --fix`

#### Git Workflow
- **Feature branches** for new work
- **Descriptive branch names**: `feature/leader-reassignment`
- **Small, focused commits** - one logical change per commit
- **No force push** to main/master

#### Environment Configuration
- **Use environment variables** for all configuration
- **Provide defaults** for development
- **Document required vars** in README or `.env.example`
- **Never commit secrets** or `.env` files

---

## Design Principles

### Keep It Simple
- **YAGNI** (You Aren't Gonna Need It) - don't build features speculatively
- **Start with simple solutions** - add complexity only when needed
- **Defer optimization** - make it work, then make it fast

### Trust-Based System
- **Designed for friend groups** who trust each other
- **No complex access controls** beyond group membership
- **Manual settlement** is acceptable for target users
- **Focus on coordination**, not enforcement

### Progressive Enhancement
- **MVP first** - core workflow before polish
- **Add features based on feedback** from real usage
- **Keep backlog prioritized** - production blockers → enhancements → nice-to-haves

---

## Common Patterns

### Adding a New Route

1. **Define Pydantic request/response models**
2. **Add route handler** in appropriate file (`routes/`)
3. **Implement business logic** in service layer (`services/`)
4. **Add repository methods** if new data access needed
5. **Write tests** for service and route
6. **Update frontend** API client and types

### Adding a New State

1. **Update RunState enum** in `run_state.py`
2. **Define valid transitions** in `RunStateMachine`
3. **Add timestamp column** to Run model: `{state}_at`
4. **Update service methods** for transition logic
5. **Add frontend handling** in RunPage and state utils
6. **Write state machine tests**

### Adding a New Notification Type

1. **Define type** in notification types enum
2. **Create notification** in service method
3. **Broadcast via WebSocket** for real-time delivery
4. **Add frontend handler** in NotificationContext
5. **Update notification display** logic

---

## Future Considerations

### Scalability Decisions Deferred

- **Caching**: Not implemented yet - add Redis when needed
- **Pagination**: Repository prepared for limit/offset, not enforced yet
- **Rate Limiting**: Documented in backlog, add before production
- **Database Migrations**: Alembic setup needed before production

### Potential Rewrites

- **Mobile App**: Backend API is platform-agnostic, same endpoints
- **Payment Integration**: Architecture supports adding payment service
- **Admin Console**: Service layer includes admin checks, ready for UI
- **Analytics**: Price history infrastructure enables trend analysis

---

## Anti-Patterns to Avoid

### Backend
- ❌ **Don't** put business logic in route handlers
- ❌ **Don't** return database models directly (use Pydantic)
- ❌ **Don't** use raw SQL unless absolutely necessary
- ❌ **Don't** log without structured `extra` context
- ❌ **Don't** hardcode configuration values

### Frontend
- ❌ **Don't** create duplicate utility CSS
- ❌ **Don't** use inline styles (use classes)
- ❌ **Don't** make API calls directly in components (use API layer)
- ❌ **Don't** store sensitive data in localStorage
- ❌ **Don't** ignore TypeScript errors

### General
- ❌ **Don't** commit directly to main/master
- ❌ **Don't** leave commented-out code
- ❌ **Don't** use `any` type in TypeScript
- ❌ **Don't** skip writing tests for complex logic
- ❌ **Don't** mention AI tools in commits/docs

---

## Contributing Guidelines

When adding new code:

1. **Follow existing patterns** - look at similar code first
2. **Update this doc** if making architectural decisions
3. **Write tests** for business logic
4. **Use structured logging** with context
5. **Keep commits focused** and well-described
6. **Ask questions** if unsure about patterns

When in doubt, **optimize for readability and maintainability** over cleverness.
