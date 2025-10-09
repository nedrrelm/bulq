# Project Structure

This document provides a comprehensive overview of the organization and purpose of all files in the Bulq project.

## Root Level

- **README.md** - Main project documentation including project overview, setup instructions, architecture details, and development workflow guidelines
- **docker-compose.yml** - Docker Compose orchestration file defining three services: PostgreSQL database, FastAPI backend, and Caddy-served frontend with volume mounts and networking configuration
- **.gitignore** - Git exclusion patterns for Python bytecode, virtual environments, node_modules, build artifacts, and OS-specific files

## Documentation (`/docs`)

Comprehensive project documentation organized by topic:

- **database_schema.md** - Complete entity-relationship diagram with detailed descriptions of all database tables (User, Group, GroupMembership, Store, Product, Run, RunParticipation, ProductBid, ShoppingListItem, Notification), column specifications, relationships, and the run state machine workflow
- **project_structure.md** - This file; detailed catalog of all project files and directories with purpose descriptions
- **REPOSITORY_PATTERN.md** - Architectural explanation of the repository pattern implementation, including the abstract base class and concrete implementations (DatabaseRepository for production, InMemoryRepository for testing and development)
- **backlog.md** - Product roadmap and feature backlog with planned enhancements including admin console, leader reassignment, caching, and pagination

## Backend (`/backend`)

Python FastAPI application with PostgreSQL database integration and comprehensive API endpoints.

### Core Application (`/backend/app`)

Main application logic and infrastructure:

- **main.py** - FastAPI application entry point; configures CORS middleware, registers all route blueprints (auth, groups, runs, stores, shopping, distribution, products, notifications, search, websocket), sets up database initialization, error handlers, middleware, and logging configuration based on environment
- **models.py** - SQLAlchemy ORM model definitions for all entities: User (authentication), Group (buying groups), GroupMembership (M2M relationship), Store, Product, Run (shopping runs with state machine), RunParticipation (user participation with leader flag), ProductBid (quantity/price tracking), ShoppingListItem (purchase tracking), EncounteredPrice (price history), Notification (user notifications)
- **database.py** - Database connection management using SQLAlchemy; provides `get_db()` dependency for FastAPI endpoints to inject database sessions with automatic cleanup
- **config.py** - Application configuration management; defines `REPO_MODE` environment variable (default: "memory") to switch between in-memory test data and PostgreSQL database, controls seed data loading behavior
- **auth.py** - Authentication and security utilities including password hashing with bcrypt, password verification, and `require_auth()` dependency that validates session cookies and retrieves the current authenticated user
- **repository.py** - Repository pattern implementation with `Repository` abstract base class defining all data access methods, `DatabaseRepository` for PostgreSQL production use, and `InMemoryRepository` for development/testing with rich seed data including multiple users, groups, stores, products, and runs in various states
- **run_state.py** - Run state machine implementation with `RunState` enum and `RunStateMachine` class; defines valid state transitions (planning→active→confirmed→shopping→adjusting→distributing→completed/cancelled), validates transitions, provides state descriptions, and includes singleton instance for convenience
- **exceptions.py** - Custom exception classes for the application: `AppException` (base), `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `ValidationError`, `ConflictError`, `BadRequestError`; all exceptions include status codes and optional details
- **error_handlers.py** - Global exception handlers for FastAPI: handles custom AppException errors, Pydantic validation errors, SQLAlchemy database errors, and unexpected exceptions; provides structured error responses with logging
- **error_models.py** - Pydantic models for error responses: `ErrorDetail`, `ErrorResponse`, `ValidationErrorResponse`; used by error handlers to format consistent error responses
- **middleware.py** - Request logging middleware (`RequestLoggingMiddleware`); logs all HTTP requests with timing, request ID, method, path, status code, and duration; skips WebSocket connections
- **logging_config.py** - Structured logging configuration with `JSONFormatter` for production and `StructuredFormatter` for development; supports file rotation, context managers, and configurable log levels; includes `LogContext` for adding structured context to logs
- **websocket_manager.py** - WebSocket connection manager for real-time updates; handles connection lifecycle, broadcasting messages to specific runs or users, connection tracking, and error handling
- **__init__.py** - Package initialization marker for the app module

### API Routes (`/backend/app/routes`)

RESTful API endpoints organized by domain and responsibility:

- **auth.py** - Authentication endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`; manages secure HTTP-only session cookies
- **groups.py** - Group management: `GET /groups/my-groups`, `POST /groups/create`, `GET /groups/{id}`, `POST /groups/{id}/join`, `POST /groups/{id}/regenerate-invite`, `GET /groups/{id}/runs`, `GET /groups/{id}/members`, `POST /groups/{id}/remove-member`, `POST /groups/{id}/leave`; handles group membership, invite tokens, and administration
- **runs.py** - Shopping run management (primary business logic): `POST /runs/create`, `GET /runs/{id}`, `POST /runs/{id}/bids`, `PUT /runs/{id}/bids/{product_id}`, `DELETE /runs/{id}/bids/{product_id}`, `POST /runs/{id}/toggle-ready`, `POST /runs/{id}/confirm`, `POST /runs/{id}/start-shopping`, `POST /runs/{id}/finish-adjusting`, `POST /runs/{id}/cancel`, `GET /runs/{id}/available-products`, `POST /runs/{id}/add-product`; implements state transitions, bid management, and adjusting state logic
- **stores.py** - Store management: `GET /stores`, `GET /stores/{id}`, `POST /stores/create`, `PUT /stores/{id}`, `DELETE /stores/{id}`; includes store CRUD operations
- **shopping.py** - Shopping execution: `GET /shopping/{run_id}/items`, `POST /shopping/{run_id}/items/{item_id}/encountered-price`, `POST /shopping/{run_id}/items/{item_id}/purchase`, `PUT /shopping/{run_id}/items/{item_id}`, `POST /shopping/{run_id}/complete`; handles shopping list, price logging, and purchase tracking
- **distribution.py** - Distribution tracking: `GET /distribution/{run_id}`, `POST /distribution/{run_id}/toggle-pickup`, `POST /distribution/{run_id}/complete`; manages item distribution and pickup tracking
- **products.py** - Product catalog: `GET /products/search`, `GET /products/{id}`, `POST /products/create`; handles product search and management
- **notifications.py** - Notification system: `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `DELETE /notifications/{id}`, `GET /notifications/unread-count`; manages user notifications with pagination
- **search.py** - Global search: `GET /search?q={query}`; consolidated search across products (up to 3), stores (up to 3), and user's groups (up to 3)
- **websocket.py** - WebSocket endpoint: `WS /ws/{run_id}`; provides real-time updates for run participants; broadcasts bid updates, state changes, and participant actions; handles connection authentication and lifecycle
- **__init__.py** - Package initialization marker for routes module

### Service Layer (`/backend/app/services`)

Business logic layer separating route handlers from data access:

- **base_service.py** - Base service class providing common functionality for all services
- **group_service.py** - Group business logic: group creation, membership management, invite token generation, run summaries, member removal; includes authorization checks and notification triggers
- **run_service.py** - Run business logic: run creation, state transitions, bid management, participant tracking, ready status, shopping list generation; enforces state machine rules and adjusting state constraints; triggers notifications for state changes
- **shopping_service.py** - Shopping business logic: shopping list management, encountered price logging, purchase tracking, completion logic (determines transition to distributing or adjusting based on quantities); validates leader permissions
- **distribution_service.py** - Distribution business logic: distribution tracking, pickup status management, completion logic; ensures all items are picked up before completing
- **product_service.py** - Product business logic: product search, creation, price history retrieval; handles product catalog operations
- **store_service.py** - Store business logic: store CRUD operations, search functionality
- **notification_service.py** - Notification business logic: notification creation, retrieval, marking as read, deletion; supports pagination and unread count; creates notifications for run events (state changes, bid updates, leader actions)
- **__init__.py** - Service module exports for convenient imports

### Scripts (`/backend/app/scripts`)

Utility scripts for database management and seeding:

- **seed_data.py** - Development seed data script that populates in-memory repository with test users (test/password, alice/password, bob/password, carol/password), groups (Test Friends, Work Lunch), stores (Costco, Sam's Club), diverse products, and runs in all states (planning, active, confirmed, shopping, adjusting, distributing, completed)
- **reset_db.py** - Database reset utility script that drops all tables and recreates schema from SQLAlchemy models; useful for development when model changes require clean slate
- **__init__.py** - Package initialization marker for scripts module

### Testing (`/backend/tests`)

Comprehensive pytest-based test suite covering all application layers:

- **conftest.py** - Pytest configuration and shared fixtures including test database setup, test client instantiation, common test data factories, and repository fixtures
- **test_auth.py** - Authentication tests: registration, login, logout, session management, password hashing, require_auth dependency
- **test_models.py** - Database model tests: model creation, relationships, constraints, cascading deletes
- **test_models_advanced.py** - Advanced model tests: complex relationships, edge cases, data integrity
- **test_repository.py** - Repository tests: both DatabaseRepository and InMemoryRepository implementations, data access methods, transaction handling
- **test_routes.py** - Route integration tests: all API endpoints, request/response validation, error handling, authentication requirements
- **test_services.py** - Service layer tests: business logic validation, authorization checks, notification triggers, state transitions
- **test_state_machine.py** - State machine tests: valid/invalid transitions, terminal states, cancellation rules, state descriptions
- **test_websocket.py** - WebSocket tests: connection lifecycle, message broadcasting, authentication, error handling
- **test_main.py** - Application integration tests: startup/shutdown, middleware, error handlers, CORS configuration
- **README.md** - Testing documentation: test organization, running tests, coverage reporting, test markers (unit/integration)
- **TESTS_SUMMARY.md** - Test coverage summary and statistics
- **TEST_RESULTS.md** - Latest test run results and analysis
- **FINAL_STATUS.md** - Final test status and coverage report
- **__init__.py** - Package initialization marker for tests module

### Configuration & Deployment

- **Dockerfile** - Multi-stage Docker container definition for backend: installs `uv` package manager, copies dependencies and source code, exposes port 8000, runs FastAPI with `fastapi dev` for hot-reloading in development
- **pyproject.toml** - Python project metadata and dependencies managed by `uv`: FastAPI, SQLAlchemy, psycopg2 (PostgreSQL driver), bcrypt (password hashing), Pydantic (data validation), uvicorn (ASGI server), pytest (testing), coverage (code coverage), httpx (HTTP client for tests)
- **uv.lock** - Locked dependency versions ensuring reproducible builds across environments
- **pytest.ini** - Pytest configuration specifying test discovery patterns, markers (unit/integration), and default options

## Frontend (`/frontend`)

React + TypeScript single-page application with Vite build tooling, served by Caddy web server.

### Source Code (`/frontend/src`)

Main application structure and entry points:

- **main.tsx** - React application entry point that renders the root App component into the DOM using ReactDOM.createRoot; wraps app with AuthContext and NotificationContext providers
- **App.tsx** - Main application component with React Router configuration for client-side routing; manages navigation between Login, Groups (home), GroupPage, ManageGroupPage, RunPage, ShoppingPage, DistributionPage, ProductPage, StorePage, JoinGroup, and NotificationPage; handles authentication state, route protection, WebSocket connections, and notification polling
- **App.css** - Application-level styles including layout structure, navigation patterns, responsive design rules, and notification badge positioning
- **index.css** - Global CSS reset, CSS custom properties (variables) for theming including colors (--color-primary, --color-secondary, --color-gray-*, --color-success, --color-warning, --color-error, --color-info), spacing, typography, and transitions; defines base element styles
- **utilities.css** - Reusable CSS utility classes following DRY principles: .card (container with shadow), .btn (button variants: primary, secondary, success, warning, danger, ghost), .form-* (form elements), .modal-* (modal dialogs), .alert-* (alert messages), .stat-* (statistics displays), .badge-* (notification badges); components should prefer these over custom CSS
- **config.ts** - Application configuration: `API_BASE_URL` (defaults to http://localhost:8000, override with VITE_API_URL), `WS_BASE_URL` (WebSocket URL derived from API URL)

### API Layer (`/frontend/src/api`)

Type-safe API client functions organized by domain:

- **client.ts** - Base HTTP client with fetch wrapper, authentication handling (credentials: 'include'), error handling, and response parsing; provides `apiClient` singleton
- **auth.ts** - Authentication API: login, register, logout, getCurrentUser
- **groups.ts** - Group API: getMyGroups, getGroup, createGroup, joinGroup, regenerateInvite, getGroupRuns, getGroupMembers, removeGroupMember, leaveGroup
- **runs.ts** - Run API: createRun, getRun, placeBid, updateBid, retractBid, toggleReady, confirmRun, startShopping, finishAdjusting, cancelRun, getAvailableProducts, addProductToRun
- **shopping.ts** - Shopping API: getShoppingItems, recordEncounteredPrice, markItemPurchased, updateShoppingItem, completeShopping
- **distribution.ts** - Distribution API: getDistributionData, togglePickup, completeDistribution
- **products.ts** - Product API: searchProducts, getProduct, createProduct
- **stores.ts** - Store API: getStores, getStore, createStore, updateStore, deleteStore
- **notifications.ts** - Notification API: getNotifications, markAsRead, markAllAsRead, deleteNotification, getUnreadCount
- **search.ts** - Search API: globalSearch (searches products, stores, groups)
- **index.ts** - API module exports for convenient imports

### Context Providers (`/frontend/src/contexts`)

React context for global state management:

- **AuthContext.tsx** - Authentication context provider: manages current user state, login/logout functions, auth status, loading state; provides `useAuth` hook for consuming components
- **NotificationContext.tsx** - Notification context provider: manages notifications state, unread count, polling for new notifications, marking as read; provides `useNotifications` hook; integrates with WebSocket for real-time updates

### Custom Hooks (`/frontend/src/hooks`)

Reusable React hooks for common functionality:

- **useApi.ts** - Generic API call hook with loading, error, and data state management; provides retry functionality and cleanup
- **useWebSocket.ts** - WebSocket connection hook: establishes connection to `/ws/{runId}`, handles reconnection, message parsing, connection state; broadcasts bid updates, state changes, participant actions
- **useToast.ts** - Toast notification hook for displaying temporary messages; provides showToast, showSuccess, showError, showWarning functions
- **useModal.ts** - Modal dialog hook for managing modal open/close state and focus trapping
- **useModalFocusTrap.ts** - Focus trap hook for modal accessibility: traps focus within modal, handles Escape key, returns focus on close
- **useClickOutside.ts** - Click outside detection hook for dropdowns and popovers; triggers callback when clicking outside element
- **useConfirm.ts** - Confirmation dialog hook for dangerous actions; shows modal confirmation before executing action

### Type Definitions (`/frontend/src/types`)

TypeScript type definitions for data models:

- **index.ts** - Core types: User, Group, GroupMembership, Run, RunParticipation, ProductBid, Store, Product, ShoppingListItem, EncounteredPrice, RunState enum
- **notification.ts** - Notification types: Notification, NotificationType enum, notification payload types
- **product.ts** - Product-related types: ProductWithPriceHistory, PricePoint
- **store.ts** - Store-related types: StoreWithProducts, StoreDetails
- **user.ts** - User-related types: UserProfile, UserStats

### Utility Functions (`/frontend/src/utils`)

Shared utility functions:

- **validation.ts** - Form validation functions: validateEmail, validatePassword, validateRequired, validateNumber, validateUUID
- **runStates.ts** - Run state utility functions: getStateColor, getStateLabel, getStateIcon, canTransitionToState, isTerminalState; provides consistent state display logic

### Styles (`/frontend/src/styles`)

Shared styling modules:

- **run-states.css** - Centralized run state badge styling with semantic color coding: .state-planning (yellow), .state-active (green), .state-confirmed (blue), .state-shopping (purple), .state-adjusting (orange), .state-distributing (cyan), .state-completed (gray), .state-cancelled (red); imported by GroupPage, Groups, and RunCard components for consistent state display

### Components (`/frontend/src/components`)

React components for pages, modals, and reusable UI elements:

#### Main Pages

- **Login.tsx** / **Login.css** - Dual-purpose authentication page with tabbed interface for login and registration; validates input, manages form state, handles authentication errors, sets session cookies, redirects to Groups page on success
- **Groups.tsx** / **Groups.css** - Home/dashboard page displaying user's groups with active run summaries (up to 3 runs per group with state badges), global search functionality (products, stores, groups), group creation button, notification dropdown; serves as main navigation hub
- **GroupPage.tsx** / **GroupPage.css** - Individual group detail page showing all runs (current and past) sorted by state priority and recency, member count, completed run count, group invite management (copy link, regenerate token), new run creation, navigation to group management; implements state-based sorting (active states first, then by date)
- **ManageGroupPage.tsx** / **ManageGroupPage.css** - Group administration page: view all members with roles, remove members (admin only), leave group, delete group (creator only); includes confirmation dialogs for destructive actions
- **RunPage.tsx** / **RunPage.css** - Comprehensive run detail page showing products with bids, participants with ready status, state-specific action buttons for leader, real-time updates via WebSocket; implements adjusting state UI with visual indicators (orange highlighting for products needing adjustment, green for satisfied), bid constraints enforcement (disable edit/retract for satisfied products in adjusting mode), product sorting (adjustment-needed products first), leader actions (confirm, start shopping, finish adjusting, cancel), participant actions (place/edit/retract bids, toggle ready status); displays notifications for events
- **ShoppingPage.tsx** / **ShoppingPage.css** - Leader shopping execution interface displaying shopping list sorted by purchase status (unpurchased first, then by purchase order), allows logging encountered prices with notes and minimum quantity, marking items purchased with quantity/price/total, completing shopping which triggers transition to distributing or adjusting based on quantity matching
- **DistributionPage.tsx** / **DistributionPage.css** - Distribution tracking page showing grid of products vs participants with pickup checkboxes; allows toggling pickup status for each participant's items; displays distribution progress; leader can complete distribution when all items picked up
- **ProductPage.tsx** / **ProductPage.css** - Product detail page showing product information, current store price, price history scatter plot (using Chart.js) from all completed runs with timestamps, allowing users to track price trends over time; displays store information and navigation
- **StorePage.tsx** / **StorePage.css** - Store detail page showing store information, address, products available at store, runs targeting this store; provides navigation to related entities
- **JoinGroup.tsx** / **JoinGroup.css** - Group invitation acceptance page that validates invite token via URL parameter, displays group name and member preview, joins user to group on confirmation
- **NotificationPage.tsx** - Full notification list page with filtering, mark all as read, delete options; displays all notifications with pagination

#### Modal Popups

- **NewRunPopup.tsx** / **NewRunPopup.css** - Modal dialog for creating new shopping run; presents dropdown of available stores, optional planned date, validates selection, calls create run API, refreshes group page on success
- **NewGroupPopup.tsx** - Modal dialog for creating new group; simple form with group name input, handles creation and page refresh (uses utilities for styling)
- **NewStorePopup.tsx** - Modal dialog for creating new store; form with name, address, chain, opening hours, handles validation and creation
- **NewProductPopup.tsx** - Modal dialog for creating new product; form with name, brand, unit, store selection, base price, handles validation and creation
- **AddProductPopup.tsx** / **AddProductPopup.css** - Modal dialog for adding products to run; searches available products by name with debounced input, displays results with store context, adds selected product to run's available products
- **BidPopup.tsx** / **BidPopup.css** - Modal dialog for placing/editing bids on products; handles quantity input with validation, interested-only checkbox option, adjusting mode constraints (shows warning banner, enforces min/max quantity based on shortage, displays acceptable range), autofocus and keyboard shortcuts (Enter to submit, Escape to cancel)
- **ConfirmDialog.tsx** / **ConfirmDialog.css** - Reusable confirmation dialog for destructive actions; displays custom message, confirm/cancel buttons with customizable labels, handles keyboard shortcuts

#### Reusable UI Components

- **RunCard.tsx** / **RunCard.css** - Card component displaying run summary with state badge, store name, participant count, progress indicators; used in Groups and GroupPage; supports click navigation to run details
- **NotificationBadge.tsx** - Badge component showing unread notification count; displays on notification bell icon
- **NotificationDropdown.tsx** - Dropdown component showing recent notifications (up to 5); supports mark as read, navigation to notification page, displays relative timestamps
- **NotificationItem.tsx** - Individual notification item component; displays icon, message, timestamp, read status; supports click to mark as read and navigate to related entity
- **LoadingSpinner.tsx** / **LoadingSpinner.css** - Loading spinner component with customizable size and centered layout; used throughout app for async operations
- **ErrorBoundary.tsx** / **ErrorBoundary.css** - Error boundary component for catching React errors; displays fallback UI with error message and reload button; logs errors to console
- **ErrorAlert.tsx** - Error alert component for displaying API errors; shows error message with icon, optional retry button, auto-dismiss option
- **Toast.tsx** / **Toast.css** - Toast notification component for temporary messages; supports success, error, warning, info variants; auto-dismisses after timeout; stacks multiple toasts

### Configuration & Build

- **package.json** - NPM dependencies (React, React Router, TypeScript, Chart.js for price history visualization) and build scripts (`dev` for development server, `build` for production, `preview` for production preview, `lint` for code quality)
- **package-lock.json** - Locked NPM dependency tree ensuring consistent installs across environments
- **vite.config.ts** - Vite build tool configuration specifying React plugin, development server port (5173), build output directory, and proxy settings for API calls
- **tsconfig.json** - Root TypeScript configuration delegating to app and node-specific configs
- **tsconfig.app.json** - TypeScript compiler settings for application code: strict mode, JSX transform, ES2020 target, module resolution, path aliases
- **tsconfig.node.json** - TypeScript compiler settings for Node.js tooling and build scripts
- **eslint.config.js** - ESLint linting rules for TypeScript and React code quality enforcement: React hooks rules, accessibility rules, naming conventions
- **Dockerfile** - Multi-stage Docker build: (1) Node.js build stage that compiles TypeScript and bundles with Vite, (2) Caddy server stage that serves static files with SPA fallback routing
- **Caddyfile** - Caddy web server configuration: serves static files from /usr/share/caddy, implements SPA routing with try_files directive (falls back to index.html for client-side routing), enables gzip compression
- **.gitignore** - Frontend-specific exclusions: node_modules, dist build output, environment files, editor configs
- **README.md** - Frontend-specific documentation covering development setup, available scripts, deployment instructions, and technology decisions
- **index.html** - HTML entry point: defines root div, includes favicon, loads main.tsx script, sets viewport meta tags

## Key Architectural Patterns

### Service Layer Architecture
The backend now uses a service layer pattern separating business logic from route handlers and data access:
- **Routes**: Handle HTTP requests/responses, authentication, validation (thin layer)
- **Services**: Implement business logic, state transitions, authorization checks, notification triggers (core logic)
- **Repository**: Data access abstraction (database or in-memory)

This separation improves testability, maintainability, and allows business logic reuse across different interfaces (REST, WebSocket, CLI).

### State Machine (Run Lifecycle)
Runs progress through a well-defined state machine with validation at each transition:
1. **planning** - Initial state; leader expresses interest in products
2. **active** - At least one non-leader participant has placed a bid; users specify quantities
3. **confirmed** - All participants mark ready; shopping list generated
4. **shopping** - Leader executes shopping; logs encountered prices and purchased quantities
5. **adjusting** - (Optional) Insufficient quantities purchased; participants reduce bids downward-only until totals match purchased quantities
6. **distributing** - Distribution in progress; tracking pickup status per participant
7. **completed** - All items distributed; run archived with price history
8. **cancelled** - Run cancelled (can occur from most states)

State transitions are validated by `RunStateMachine` class and enforced in service layer.

### Notification System
Real-time notification system for keeping users informed of run events:
- **Backend**: `NotificationService` creates notifications for state changes, bid updates, leader actions, member changes
- **Database**: `Notification` model stores notifications with type, message, read status, related entity IDs
- **API**: RESTful endpoints for retrieving, marking as read, deleting notifications
- **Frontend**: `NotificationContext` manages state, polls for updates, displays unread count in badge
- **WebSocket**: Real-time notification delivery for immediate feedback

### WebSocket Real-Time Updates
WebSocket integration for live collaboration during runs:
- **Backend**: `WebSocketManager` handles connection lifecycle, message broadcasting to run participants
- **Endpoint**: `WS /ws/{run_id}` authenticated WebSocket endpoint
- **Messages**: Broadcasts bid updates, state changes, participant actions
- **Frontend**: `useWebSocket` hook manages connection, reconnection, message handling
- **Integration**: RunPage subscribes to WebSocket updates and refreshes data on events

### Adjusting State Implementation
Special state handling for quantity shortages:
- **Backend**: Shopping service detects `purchased_quantity < requested_quantity` and transitions to adjusting; run service enforces downward-only bid edits with min/max constraints; `finish_adjusting` endpoint validates all products match before transitioning to distributing
- **Frontend**: RunPage sorts products (adjustment-needed first), visually highlights products with color coding (orange border/background for needs-adjustment, green for satisfied), disables edit/retract buttons for satisfied products, shows clear indicators of required reductions; BidPopup displays warning banner in adjusting mode with acceptable quantity range

### Error Handling Architecture
Comprehensive error handling with structured logging:
- **Custom Exceptions**: Type-safe exception classes (`NotFoundError`, `ForbiddenError`, etc.) with status codes and details
- **Global Handlers**: FastAPI exception handlers convert exceptions to consistent JSON responses
- **Structured Logging**: All errors logged with context (request ID, user ID, path, method) for debugging
- **Frontend**: API client catches errors, displays user-friendly messages via toast notifications

### CSS Organization
Frontend CSS follows strict DRY (Don't Repeat Yourself) principles:
- **utilities.css**: Comprehensive utility classes for common patterns (cards, buttons, forms, modals, badges); components should use these whenever possible
- **index.css**: Global variables, resets, base element styling; defines design system tokens (colors, spacing, typography)
- **run-states.css**: Shared state badge styling imported by multiple components
- **Component CSS**: Only component-specific layouts and unique visual treatments; should be minimal

### Authentication & Authorization
Session-based authentication with role-based access:
- **Backend**: `require_auth` dependency validates HTTP-only session cookies
- **Authorization**: Service layer checks permissions (group membership, leader status, admin role)
- **Frontend**: `AuthContext` manages user state, redirects unauthenticated users
- **Security**: Passwords hashed with bcrypt, sessions stored server-side

### Type Safety
Strong typing throughout the stack:
- **Backend**: Pydantic models for request/response validation, SQLAlchemy models for database
- **Frontend**: TypeScript interfaces for all API responses, strict mode enabled
- **API Contract**: Shared understanding of data structures between frontend and backend

### File Naming Conventions
- **Backend**: snake_case for all Python files (`run_service.py`, `test_state_machine.py`)
- **Frontend**: PascalCase for React components (`RunPage.tsx`, `BidPopup.tsx`), matching CSS files (`RunPage.css`), kebab-case for utilities and styles (`run-states.css`)
- **Configuration**: lowercase with conventional extensions (`package.json`, `tsconfig.json`, `Dockerfile`, `Caddyfile`)

### Data Flow
1. **Request**: Frontend makes authenticated fetch() request to backend API endpoint
2. **Route Handler**: Validates request, extracts user from session, calls service method
3. **Service Layer**: Implements business logic, checks authorization, interacts with repository
4. **Repository**: Data access abstraction (database or in-memory), returns domain models
5. **Response**: Pydantic models validate and serialize response data as JSON
6. **Frontend Update**: React component updates state, triggers re-render with new data
7. **Real-Time**: WebSocket broadcasts changes to other connected users

### Development Workflow
- **Backend**: `docker compose up backend` or `fastapi dev app/main.py` with hot-reloading; defaults to in-memory repository with seed data for immediate development
- **Frontend**: `npm run dev` with Vite HMR (Hot Module Replacement) for instant feedback
- **Docker**: `docker compose up` orchestrates all services for integration testing or production-like environment
- **Testing**: `pytest` for backend comprehensive test suite; frontend tests not yet implemented
- **Logging**: Structured logs in development (key=value), JSON logs in production

### Security Model
- **Authentication**: Session-based with HTTP-only cookies (not vulnerable to XSS)
- **Password Storage**: Bcrypt hashing with automatic salt generation
- **Authorization**: Group membership checked for all group/run operations; leader status checked for state-changing operations
- **CORS**: Configured to allow frontend origin with credentials
- **Error Handling**: Internal errors not exposed to clients, generic messages with structured logging
- **Trust-Based**: System designed for friend groups; no payment processing, minimal access controls beyond group membership

### Future Extensibility Points
The codebase is structured to easily accommodate planned features:
- **Admin Console**: Service layer includes admin checks, ready for admin UI
- **Leader Reassignment**: Database schema supports tracking leadership changes
- **Caching**: Service layer abstraction allows adding Redis caching without route changes
- **Pagination**: Repository methods prepared for limit/offset parameters
- **Mobile App**: Backend API is platform-agnostic REST; same endpoints can serve native mobile apps
- **Advanced Analytics**: Price history infrastructure (EncounteredPrice, completed runs) enables trend analysis, savings calculations
- **Bulk Operations**: Repository pattern allows efficient bulk updates; useful for large-scale distribution tracking
