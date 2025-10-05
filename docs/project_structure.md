# Project Structure

This document describes the organization and purpose of all files in the Bulq project.

## Root Level

- **README.md** - Main project documentation with setup instructions, architecture overview, and development workflow
- **database_schema.md** - Detailed entity-relationship diagram and database schema documentation
- **docker-compose.yml** - Docker Compose configuration for running backend, frontend, and database containers
- **.gitignore** - Git ignore patterns for the project

## Backend (`/backend`)

Python FastAPI application with PostgreSQL database integration.

### Application Code (`/backend/app`)

- **main.py** - FastAPI application entry point, CORS configuration, and route registration
- **models.py** - SQLAlchemy ORM models (User, Group, Store, Run, Product, ProductBid)
- **database.py** - Database connection and session management
- **config.py** - Application configuration and environment variables
- **auth.py** - Authentication logic (password hashing, session management)
- **repository.py** - Repository pattern implementation with abstract base class and concrete implementations (DB and in-memory)
- **__init__.py** - Package initialization

### Routes (`/backend/app/routes`)

API endpoint definitions organized by domain:

- **auth.py** - Authentication endpoints (login, register, logout, session management)
- **groups.py** - Group management endpoints (create, list, view, add members)
- **runs.py** - Shopping run endpoints (create, list, view, manage products and bids)
- **stores.py** - Store management endpoints (create, list)
- **__init__.py** - Package initialization

### Configuration & Deployment

- **Dockerfile** - Backend container configuration
- **pyproject.toml** - Python project dependencies and metadata (managed by `uv`)
- **uv.lock** - Locked dependency versions
- **.python-version** - Python version specification for the project
- **pytest.ini** - Pytest configuration

### Documentation

- **REPOSITORY_PATTERN.md** - Explanation of the repository pattern implementation

### Database & Testing

- **seed_data.py** - Development seed data script for populating the database
- **tests/** - Test suite
  - **conftest.py** - Pytest fixtures and configuration
  - **test_main.py** - Main application tests
  - **test_models.py** - Model tests
  - **__init__.py** - Package initialization

## Frontend (`/frontend`)

React + TypeScript application served with Caddy.

### Source Code (`/frontend/src`)

- **main.tsx** - Application entry point
- **App.tsx** - Main app component with routing logic
- **App.css** - App-level styles
- **index.css** - Global styles and CSS variable definitions
- **utilities.css** - Reusable utility CSS classes (cards, buttons, forms, modals, alerts, etc.)

### Components (`/frontend/src/components`)

Page and popup components for the application:

- **Login.tsx** / **Login.css** - Login and registration page
- **Groups.tsx** / **Groups.css** - Groups list page
- **GroupPage.tsx** / **GroupPage.css** - Individual group detail page with runs
- **RunPage.tsx** / **RunPage.css** - Individual run detail page with products and bidding
- **NewRunPopup.tsx** / **NewRunPopup.css** - Modal for creating new shopping runs
- **AddProductPopup.tsx** / **AddProductPopup.css** - Modal for adding products to a run
- **BidPopup.tsx** / **BidPopup.css** - Modal for placing bids on products

### Assets (`/frontend/src/assets`)

- **react.svg** - React logo

### Public Assets (`/frontend/public`)

- **vite.svg** - Vite logo

### Configuration & Build

- **package.json** - npm dependencies and scripts
- **package-lock.json** - Locked npm dependency tree
- **vite.config.ts** - Vite build tool configuration
- **tsconfig.json** - TypeScript compiler configuration
- **tsconfig.app.json** - TypeScript config for application code
- **tsconfig.node.json** - TypeScript config for Node.js code
- **eslint.config.js** - ESLint linting configuration
- **Dockerfile** - Frontend container configuration with multi-stage build
- **Caddyfile** - Caddy web server configuration for serving the frontend
- **.gitignore** - Frontend-specific git ignore patterns
- **README.md** - Frontend-specific documentation

## Key Architectural Patterns

### Repository Pattern
The backend uses an abstract repository pattern (`repository.py`) with two implementations:
- **DatabaseRepository**: Production implementation using SQLAlchemy
- **InMemoryRepository**: Testing implementation using in-memory dictionaries

### CSS Organization
Frontend follows DRY principles with CSS:
- **utilities.css**: Reusable classes for common patterns (prefer using these)
- Component-specific CSS: Only when absolutely necessary
- CSS variables for theming (defined in `index.css`)

### File Naming
- Backend: snake_case Python files
- Frontend: PascalCase for components, snake_case for utilities
- Each React component has a corresponding `.css` file
