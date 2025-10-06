# Project Structure

This document provides a comprehensive overview of the organization and purpose of all files in the Bulq project.

## Root Level

- **README.md** - Main project documentation including project overview, setup instructions, architecture details, and development workflow guidelines
- **docker-compose.yml** - Docker Compose orchestration file defining three services: PostgreSQL database, FastAPI backend, and Caddy-served frontend with volume mounts and networking configuration
- **.gitignore** - Git exclusion patterns for Python bytecode, virtual environments, node_modules, build artifacts, and OS-specific files

## Documentation (`/docs`)

Comprehensive project documentation organized by topic:

- **database_schema.md** - Complete entity-relationship diagram with detailed descriptions of all database tables (User, Group, GroupMembership, Store, Product, Run, RunParticipation, ProductBid, ShoppingListItem), column specifications, relationships, and the run state machine workflow
- **project_structure.md** - This file; detailed catalog of all project files and directories with purpose descriptions
- **REPOSITORY_PATTERN.md** - Architectural explanation of the repository pattern implementation, including the abstract base class and concrete implementations (DatabaseRepository for production, InMemoryRepository for testing and development)
- **backlog.md** - Product roadmap and feature backlog with planned enhancements including WebSocket real-time updates, product families/hierarchies, and quantity adjustment handling

## Backend (`/backend`)

Python FastAPI application with PostgreSQL database integration and comprehensive API endpoints.

### Core Application (`/backend/app`)

Main application logic and infrastructure:

- **main.py** - FastAPI application entry point; configures CORS middleware to allow frontend requests, registers all route blueprints (auth, groups, runs, stores, shopping, distribution, products), sets up database initialization and optional seed data loading based on `REPO_MODE` environment variable
- **models.py** - SQLAlchemy ORM model definitions for all entities: User (authentication), Group (buying groups), GroupMembership (M2M relationship), Store (Costco/Sam's Club), Product (store inventory), Run (shopping runs with state machine: planning→active→confirmed→shopping→adjusting→distributing→completed), RunParticipation (user participation in runs with leader flag), ProductBid (user bids on products with quantity/price tracking), ShoppingListItem (consolidated shopping list with purchase tracking)
- **database.py** - Database connection management using SQLAlchemy; provides `get_db()` dependency for FastAPI endpoints to inject database sessions with automatic cleanup
- **config.py** - Application configuration management; defines `REPO_MODE` environment variable (default: "memory") to switch between in-memory test data and PostgreSQL database, controls seed data loading behavior
- **auth.py** - Authentication and security utilities including password hashing with bcrypt, password verification, and `require_auth()` dependency that validates session cookies and retrieves the current authenticated user
- **repository.py** - Repository pattern implementation with `Repository` abstract base class defining all data access methods, `DatabaseRepository` for PostgreSQL production use, and `InMemoryRepository` for development/testing with rich seed data including multiple users (test, alice, bob, carol), groups, stores (Costco, Sam's Club), products, and runs in various states including a complete adjusting state example
- **__init__.py** - Package initialization marker for the app module

### API Routes (`/backend/app/routes`)

RESTful API endpoints organized by domain and responsibility:

- **auth.py** - Authentication endpoints: `POST /auth/register` (create new user account), `POST /auth/login` (authenticate and create session), `POST /auth/logout` (destroy session), `GET /auth/me` (get current user info); manages secure HTTP-only session cookies
- **groups.py** - Group management: `GET /groups/my-groups` (list user's groups with active run summaries), `POST /groups/create` (create new group), `GET /groups/{id}` (group details), `POST /groups/{id}/regenerate-invite` (regenerate invite token), `GET /groups/{id}/runs` (list group's runs); handles group membership and invite tokens
- **runs.py** - Shopping run management (primary business logic): `POST /runs/create` (create new run in planning state), `GET /runs/{id}` (detailed run info with products, bids, participants, state-specific data), `POST /runs/{id}/bids` (place/update bid on product with adjusting state validation for downward-only changes), `DELETE /runs/{id}/bids/{product_id}` (retract bid with adjusting state constraints), `POST /runs/{id}/toggle-ready` (mark participant ready/not ready), `POST /runs/{id}/confirm` (leader transitions planning→active or active→confirmed), `POST /runs/{id}/start-shopping` (leader transitions confirmed→shopping, generates shopping list), `POST /runs/{id}/finish-adjusting` (leader transitions adjusting→distributing after bids adjusted to match purchased quantities), `GET /runs/{id}/available-products` (products available to add to run)
- **stores.py** - Store management: `GET /stores` (list all stores), `POST /stores/create` (admin-level store creation - not currently used)
- **shopping.py** - Shopping execution: `GET /shopping/{run_id}/items` (shopping list for leader), `POST /shopping/{run_id}/items/{item_id}/encountered-price` (log price found in store), `POST /shopping/{run_id}/items/{item_id}/purchase` (mark item purchased with quantity/price), `POST /shopping/{run_id}/complete` (finish shopping - transitions to distributing if quantities match, or adjusting if insufficient quantities purchased)
- **distribution.py** - Distribution tracking: `GET /distribution/{run_id}` (distribution page with participant pickup status), `POST /distribution/{run_id}/toggle-pickup` (toggle item pickup status for participant)
- **products.py** - Product catalog: `GET /products/search` (search products across stores by name), `GET /products/{id}` (product details with price history from completed runs), `POST /products/create` (create new product for a store)
- **__init__.py** - Package initialization marker for routes module

### Database & Utilities

- **seed_data.py** - Development seed data script that populates in-memory repository with test users (test/password, alice/password, bob/password, carol/password), two groups (Test Friends, Work Lunch), two stores (Costco, Sam's Club), diverse products (groceries, household items), and runs in all states (planning, active, confirmed, shopping, adjusting with shortage scenario, distributing, completed with historical timestamps)
- **reset_db.py** - Database reset utility script that drops all tables and recreates schema from SQLAlchemy models; useful for development when model changes require clean slate

### Testing (`/backend/tests`)

Pytest-based test suite:

- **conftest.py** - Pytest configuration and shared fixtures including test database setup, test client instantiation, and common test data factories
- **test_main.py** - Integration tests for main API endpoints testing full request/response cycles
- **test_models.py** - Unit tests for SQLAlchemy model validation, relationships, and business logic
- **__init__.py** - Package initialization marker for tests module

### Configuration & Deployment

- **Dockerfile** - Multi-stage Docker container definition for backend: installs `uv` package manager, copies dependencies and source code, exposes port 8000, runs FastAPI with `fastapi dev` for hot-reloading in development
- **pyproject.toml** - Python project metadata and dependencies managed by `uv`: FastAPI, SQLAlchemy, psycopg2 (PostgreSQL driver), bcrypt (password hashing), Pydantic (data validation), uvicorn (ASGI server)
- **uv.lock** - Locked dependency versions ensuring reproducible builds across environments
- **.python-version** - Python version specification (3.11) for `uv` and development environment consistency
- **pytest.ini** - Pytest configuration specifying test discovery patterns and default options

## Frontend (`/frontend`)

React + TypeScript single-page application with Vite build tooling, served by Caddy web server.

### Source Code (`/frontend/src`)

Main application structure and entry points:

- **main.tsx** - React application entry point that renders the root App component into the DOM using ReactDOM.createRoot
- **App.tsx** - Main application component with React Router configuration for client-side routing; manages navigation between Login, Groups (home), GroupPage, RunPage, ShoppingPage, DistributionPage, ProductPage, and JoinGroup; handles authentication state and route protection; implements URL-based navigation pattern for deep linking
- **App.css** - Application-level styles including layout structure, navigation patterns, and responsive design rules
- **index.css** - Global CSS reset, CSS custom properties (variables) for theming including colors (--color-primary, --color-secondary, --color-gray-*), spacing, and typography; defines base element styles
- **utilities.css** - Reusable CSS utility classes following DRY principles: .card (container with shadow), .btn (button variants), .form-* (form elements), .modal-* (modal dialogs), .alert-* (alert messages), .stat-* (statistics displays); components should prefer these over custom CSS

### Styles (`/frontend/src/styles`)

Shared styling modules:

- **run-states.css** - Centralized run state badge styling with semantic color coding: .state-planning (yellow), .state-active (green), .state-confirmed (blue), .state-shopping (purple), .state-adjusting (orange), .state-distributing (cyan), .state-completed (gray), .state-cancelled (red); imported by GroupPage and Groups components for consistent state display

### Components (`/frontend/src/components`)

React components for pages and modal dialogs:

#### Main Pages

- **Login.tsx** / **Login.css** - Dual-purpose authentication page with tabbed interface for login and registration; validates input, manages form state, handles authentication errors, sets session cookies, redirects to Groups page on success
- **Groups.tsx** / **Groups.css** - Home/dashboard page displaying user's groups with active run summaries (up to 3 runs per group with state badges), product search functionality using debounced search API, group creation button; serves as main navigation hub
- **GroupPage.tsx** / **GroupPage.css** - Individual group detail page showing all runs (current and past) sorted by state priority, member count, completed run count, group invite management (copy link, regenerate token), new run creation; implements state-based sorting (distributing > adjusting > shopping > confirmed > active > planning)
- **RunPage.tsx** / **RunPage.css** - Comprehensive run detail page showing products with bids, participants with ready status, state-specific action buttons for leader; implements adjusting state UI with visual indicators (orange highlighting for products needing adjustment, green for satisfied), bid constraints enforcement (disable edit/retract for satisfied products in adjusting mode, disable retract when bid exceeds shortage), product sorting (adjustment-needed products first), leader actions (confirm, start shopping, finish adjusting), and participant actions (place/edit/retract bids, toggle ready status)
- **ShoppingPage.tsx** / **ShoppingPage.css** - Leader shopping execution interface displaying shopping list sorted by purchase status (unpurchased first, then by purchase order), allows logging encountered prices with notes, marking items purchased with quantity/price/total, completing shopping which triggers transition to distributing or adjusting based on quantity matching
- **DistributionPage.tsx** / **DistributionPage.css** - Distribution tracking page showing grid of products vs participants with pickup checkboxes; allows toggling pickup status for each participant's items; provides visual overview of distribution progress
- **ProductPage.tsx** / **ProductPage.css** - Product detail page showing product information, current store price, price history scatter plot (using Chart.js) from all completed runs with timestamps, allowing users to track price trends over time
- **JoinGroup.tsx** / **JoinGroup.css** - Group invitation acceptance page that validates invite token via URL parameter, displays group name, and joins user to group on confirmation

#### Modal Popups

- **NewRunPopup.tsx** / **NewRunPopup.css** - Modal dialog for creating new shopping run; presents dropdown of available stores, validates selection, calls create run API, refreshes group page on success
- **NewGroupPopup.tsx** - Modal dialog for creating new group; simple form with group name input, handles creation and page refresh (no dedicated CSS file, uses utilities)
- **AddProductPopup.tsx** / **AddProductPopup.css** - Modal dialog for adding products to run; searches available products by name with debounced input, displays results with store context, adds selected product to run's available products
- **BidPopup.tsx** / **BidPopup.css** - Modal dialog for placing/editing bids on products; handles quantity input with validation, interested-only checkbox option, adjusting mode constraints (shows warning banner, enforces min/max quantity based on shortage, displays acceptable range), autofocus and keyboard shortcuts (Enter to submit, Escape to cancel)

### Configuration & Build

- **package.json** - NPM dependencies (React, React Router, TypeScript, Chart.js for price history visualization) and build scripts (`dev` for development server, `build` for production, `preview` for production preview, `lint` for code quality)
- **package-lock.json** - Locked NPM dependency tree ensuring consistent installs across environments
- **vite.config.ts** - Vite build tool configuration specifying React plugin, development server port (5173), and build output directory
- **tsconfig.json** - Root TypeScript configuration delegating to app and node-specific configs
- **tsconfig.app.json** - TypeScript compiler settings for application code: strict mode, JSX transform, ES2020 target, module resolution
- **tsconfig.node.json** - TypeScript compiler settings for Node.js tooling and build scripts
- **eslint.config.js** - ESLint linting rules for TypeScript and React code quality enforcement
- **Dockerfile** - Multi-stage Docker build: (1) Node.js build stage that compiles TypeScript and bundles with Vite, (2) Caddy server stage that serves static files with SPA fallback routing
- **Caddyfile** - Caddy web server configuration: serves static files from /usr/share/caddy, implements SPA routing with try_files directive (falls back to index.html for client-side routing), enables file server with browse capability
- **.gitignore** - Frontend-specific exclusions: node_modules, dist build output, environment files
- **README.md** - Frontend-specific documentation covering development setup, available scripts, and deployment instructions

## Key Architectural Patterns

### Repository Pattern
The backend implements the repository pattern with a clear separation of concerns:
- **Abstract Base (`Repository`)**: Defines interface for all data access operations (CRUD, queries, business logic)
- **Database Implementation (`DatabaseRepository`)**: Production implementation using SQLAlchemy ORM with PostgreSQL, handles transactions and rollbacks
- **In-Memory Implementation (`InMemoryRepository`)**: Development/testing implementation using Python dictionaries, includes comprehensive seed data with realistic scenarios (runs in all states, multiple users/groups, price history)
- **Mode Switching**: Controlled via `REPO_MODE` environment variable in config.py (default: "memory" for easy development)

### State Machine (Run Lifecycle)
Runs progress through a well-defined state machine with validation at each transition:
1. **planning** - Initial state; users express interest in products (interested-only bids)
2. **active** - At least one non-leader participant has placed a bid; users specify quantities
3. **confirmed** - Leader confirms; all participants mark ready; shopping list generated
4. **shopping** - Leader executes shopping; logs encountered prices and purchased quantities
5. **adjusting** - (Optional) Insufficient quantities purchased; participants reduce bids downward-only until totals match purchased quantities
6. **distributing** - Distribution in progress; tracking pickup status per participant
7. **completed** - All items distributed; run archived with price history

Each state has specific allowed actions, UI visibility, and validation rules enforced in both backend (API endpoints) and frontend (UI controls).

### Adjusting State Implementation
Special state handling for quantity shortages:
- **Backend**: `shopping.py` detects purchased_quantity < requested_quantity and transitions to adjusting instead of distributing; `runs.py` enforces downward-only bid edits with min/max constraints (cannot reduce below `current - shortage`, cannot increase); `finish_adjusting` endpoint validates all products match before transitioning to distributing
- **Frontend**: RunPage sorts products (adjustment-needed first), visually highlights products with color coding (orange border/background for needs-adjustment, green for satisfied), disables edit/retract buttons for satisfied products, disables retract when bid > shortage (would over-reduce), shows clear indicators of required reductions; BidPopup displays warning banner in adjusting mode with acceptable quantity range

### CSS Organization
Frontend CSS follows strict DRY (Don't Repeat Yourself) principles:
- **utilities.css**: Comprehensive utility classes for common patterns (cards, buttons, forms, modals, badges); components should use these whenever possible
- **index.css**: Global variables, resets, base element styling; defines design system tokens
- **run-states.css**: Shared state badge styling imported by multiple components
- **Component CSS**: Only component-specific layouts and unique visual treatments; should be minimal

### File Naming Conventions
- **Backend**: snake_case for all Python files (`auth.py`, `shopping.py`, `test_models.py`)
- **Frontend**: PascalCase for React components (`RunPage.tsx`, `BidPopup.tsx`), matching CSS files (`RunPage.css`), kebab-case for utilities and styles (`run-states.css`)
- **Configuration**: lowercase with conventional extensions (`package.json`, `tsconfig.json`, `Dockerfile`, `Caddyfile`)

### Data Flow
1. **Request**: Frontend makes authenticated fetch() request to backend API endpoint
2. **Authentication**: `require_auth()` dependency validates session cookie, retrieves User object
3. **Repository**: Route handler calls repository methods via `get_repository(db)` for data access
4. **Response**: Pydantic models validate and serialize response data as JSON
5. **Frontend Update**: React component updates state, triggers re-render with new data
6. **Optimistic Updates**: Some operations (like toggling ready status) refresh entire run data after successful mutation to ensure consistency

### Development Workflow
- **Backend**: `fastapi dev app/main.py` with hot-reloading; defaults to in-memory repository with seed data for immediate development
- **Frontend**: `npm run dev` with Vite HMR (Hot Module Replacement) for instant feedback
- **Docker**: `docker-compose up` orchestrates all services for integration testing or production-like environment
- **Testing**: `pytest` for backend unit/integration tests; frontend tests not yet implemented

### Security Model
- **Authentication**: Session-based with HTTP-only cookies (not vulnerable to XSS)
- **Password Storage**: Bcrypt hashing with automatic salt generation
- **Authorization**: Group membership checked for all group/run operations; leader status checked for state-changing operations
- **CORS**: Configured to allow frontend origin with credentials
- **Trust-Based**: System designed for friend groups; no payment processing, minimal access controls beyond group membership

### Future Extensibility Points
The codebase is structured to easily accommodate planned features:
- **WebSocket Support**: Real-time updates can be added via FastAPI WebSocket endpoints, minimal frontend changes due to centralized data fetching
- **Product Families**: Database schema supports this via potential new ProductFamily table; UI already handles dynamic product lists
- **Mobile App**: Backend API is platform-agnostic REST; same endpoints can serve native mobile apps
- **Advanced Analytics**: Price history infrastructure (completed runs with timestamps) enables trend analysis, savings calculations
- **Bulk Operations**: Repository pattern allows efficient bulk updates; useful for large-scale distribution tracking
