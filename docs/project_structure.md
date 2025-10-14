# Project Structure

High-level overview of the Bulq project organization and key files.

## Root Level

- **README.md** - Main project documentation with setup, architecture, and development workflow
- **docker-compose.yml** - Orchestrates PostgreSQL, FastAPI backend, and Caddy frontend services
- **.gitignore** - Git exclusions for generated files and dependencies

## Documentation (`/docs`)

- **database_schema.md** - Complete ER diagram and database schema documentation
- **project_structure.md** - This file; high-level project organization
- **production_deployment.md** - Production deployment guide with SSL, backups, monitoring
- **development_vs_production.md** - Configuration differences between dev and production modes
- **development_notes.md** - Architectural decisions, code style rules, design principles
- **backlog.md** - Feature backlog and technical debt tracking

## Backend (`/backend`)

Python FastAPI application with three-layer architecture (Routes → Services → Repository).

### Core Application (`/backend/app`)

- **main.py** - FastAPI entry point; registers routes, configures middleware, initializes database

### Core Domain (`/backend/app/core`)

- **models.py** - SQLAlchemy ORM models for all entities (User, Group, Run, Product, etc.)
- **repository.py** - Repository pattern with DatabaseRepository (PostgreSQL) and InMemoryRepository (testing/dev with seed data)
- **run_state.py** - Run state machine defining valid transitions between states
- **exceptions.py** - Custom exception classes with status codes

### API Layer (`/backend/app/api`)

- **middleware.py** - Request logging and context management
- **websocket_manager.py** - WebSocket connection manager for real-time updates
- **routes/** - RESTful API endpoints organized by domain:
  - `auth.py` - Registration, login, logout, session management
  - `groups.py` - Group creation, membership, invites
  - `runs.py` - Run lifecycle, bidding, state transitions
  - `shopping.py` - Shopping list execution, price updates, purchase tracking
  - `distribution.py` - Item distribution and pickup tracking
  - `products.py` - Product catalog management
  - `stores.py` - Store management
  - `notifications.py` - User notifications
  - `search.py` - Global search across entities
  - `websocket.py` - WebSocket endpoint for real-time updates
- **schemas/** - Pydantic request/response models for validation and serialization

### Service Layer (`/backend/app/services`)

Business logic layer separating routes from data access. Services handle authorization, state transitions, and notification triggers.

- **run_service.py** - Run creation, state management, participant tracking
- **bid_service.py** - Bid placement, updates, retraction logic
- **group_service.py** - Group operations, membership, invites
- **shopping_service.py** - Shopping execution, price updates, completion logic
- **distribution_service.py** - Distribution tracking, pickup management
- **notification_service.py** - Notification creation and management
- Additional services for products, stores, admin operations, etc.

### Infrastructure (`/backend/app/infrastructure`)

External dependencies and cross-cutting concerns:

- **database.py** - SQLAlchemy session management
- **config.py** - Environment variable configuration with production validation
- **auth.py** - Password hashing, session management, authentication dependency
- **logging_config.py** - Structured logging with JSON/key-value formats
- **request_context.py** - Thread-safe request ID tracking for log tracing
- **transaction.py** - Database transaction management

### Events System (`/backend/app/events`)

Domain event system for decoupled event handling:

- **domain_events.py** - Event definitions (BidPlaced, RunStateChanged, etc.)
- **event_bus.py** - In-memory pub-sub for domain events
- **handlers/** - Event handlers for WebSocket broadcasts and notifications

### Testing (`/backend/tests`)

Comprehensive pytest suite covering all layers:

- **conftest.py** - Test fixtures and configuration
- **test_*.py** - Tests for auth, models, repositories, routes, services, state machine, WebSocket
- 100+ tests with unit and integration markers

### Configuration

- **Dockerfile** - Multi-stage container with uv package manager
- **pyproject.toml** - Python dependencies managed by uv
- **pytest.ini** - Test configuration

## Frontend (`/frontend`)

React + TypeScript SPA with Vite build tooling, served by Caddy.

### Source Code (`/frontend/src`)

- **main.tsx** - Application entry point with context providers
- **App.tsx** - Router configuration and route protection
- **config.ts** - API and WebSocket URL configuration
- **index.css** - Global styles and CSS variables
- **utilities.css** - Reusable utility classes (DRY principle)

### API Layer (`/frontend/src/api`)

Type-safe API client functions organized by domain (auth, groups, runs, shopping, etc.).

### Components (`/frontend/src/components`)

React components organized by purpose:

**Pages:**
- Login/registration, groups dashboard, run detail, shopping execution, distribution tracking, product/store pages

**Modals:**
- New run/group/store/product creation, bid placement, product search, confirmation dialogs

**Reusable UI:**
- Run cards, notification components, loading spinners, error handling, toast notifications

### State Management

- **contexts/** - AuthContext (user state) and NotificationContext (notification management)
- **hooks/** - Custom hooks for API calls, WebSocket, modals, toast notifications

### Type Definitions (`/frontend/src/types`)

TypeScript interfaces for all data models (User, Group, Run, Product, etc.).

### Configuration

- **package.json** - NPM dependencies and scripts
- **vite.config.ts** - Vite build configuration
- **tsconfig.json** - TypeScript compiler settings
- **Dockerfile** - Multi-stage build (Vite build + Caddy serve)
- **Caddyfile** - Reverse proxy configuration with automatic HTTPS

## Key Architectural Patterns

### Three-Layer Architecture (Backend)
```
Routes (HTTP)  →  Services (Business Logic)  →  Repository (Data Access)
```

### State Machine
Runs progress through validated states: `planning → active → confirmed → shopping → adjusting? → distributing → completed`

### Repository Pattern
Abstract interface with dual implementations: DatabaseRepository (production) and InMemoryRepository (testing/dev)

### Event-Driven Updates
Domain events trigger WebSocket broadcasts and notification creation for real-time UI updates

### Structured Logging
Context-aware logging with automatic request ID tracking for distributed tracing

### CSS Utility-First
Reusable utility classes minimize duplicate CSS across components

## Development Workflow

- **Backend**: `docker compose up backend` with hot-reloading
- **Frontend**: `npm run dev` with Vite HMR
- **Testing**: `pytest tests/ -v` for comprehensive backend tests
- **Docker**: `docker compose up` orchestrates all services

## File Naming Conventions

- **Backend**: snake_case for Python files
- **Frontend**: PascalCase for React components, kebab-case for utilities
- **Configuration**: lowercase with conventional extensions
