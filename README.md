# Bulq - Bulk Buying Organization Platform

A platform for organizing group purchases to reduce costs through bulk buying.

## Overview

Bulq enables friend groups to coordinate bulk purchases and track savings through organized group buying. The platform helps manage buying runs, calculate individual costs, and track purchase history across different stores.

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Web Frontend**: React
- **Android App**: Native Kotlin

## Key Features

- Group buying run management
- Individual cost calculation and tracking
- Purchase history tracking
- Price comparison across stores
- Real-time order updates via WebSockets
- No in-app payments (manual settlement)

## Core Workflow

1. **Groups**: Users join friend groups for coordinated shopping
2. **Runs**: Groups create shopping runs targeting specific stores
3. **Bidding**: Users express interest and specify quantities for products
4. **Confirmation**: Products meeting thresholds are confirmed for purchase
5. **Shopping**: Designated group members execute the shopping list
6. **Settlement**: Costs calculated and settled manually among friends

## Architecture

- **Database Schema**: See [docs/database_schema.md](docs/database_schema.md) for detailed ER diagram
- **Project Structure**: See [docs/project_structure.md](docs/project_structure.md) for file organization and contents
- **Containerized Architecture**: Separate Docker containers for backend, frontend, and database
- **Backend**: FastAPI application running in Python container
- **Database**: PostgreSQL running in dedicated container with UUIDs for primary keys
- **Frontend**: React + TypeScript application served with Caddy
- **Real-time Updates**: WebSocket connections for live bid tracking

### Architecture Decisions

- **Monolithic Backend**: Single FastAPI application, suitable for expected load
- **Containerized Development**: Docker Compose for consistent environments
- **Frontend-Backend Separation**: React frontend, FastAPI backend with CORS
- **WebSockets**: For real-time bid updates during group orders (planned)
- **No Image Storage**: Avoiding complexity, text-based product descriptions only
- **PostgreSQL with UUIDs**: For primary keys across all entities (planned)

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

**Thresholds:**
- Deferred for initial version
- Will integrate with bulk pricing tiers later
- For now, any product with quantity bids gets confirmed

**Shopping List Generation:**
- Calculated view, not stored entity
- Confirmed products = products with quantity > 0
- Quantities = sum of all user bids per product
- Assigned to designated_shoppers stored in Run

### Design Principles

- Trust-based system for friend groups
- Focus on management and calculation tools
- Keep it simple for initial version
- Real-time updates for engagement

### Non-Features (Intentionally Excluded)

- In-app payments (users settle manually)
- Chat functionality (users communicate externally)
- Image uploads/storage
- Complex shopping assignment tracking

### Data Entry Strategy

- Manual store/product entry initially
- Future: Store API integration or scraping
- Price tracking built into Product entity

## Target Users

Friend groups who trust each other and handle discussions/payments outside the app.

## Development Setup

### Quick Start with Docker Compose

The easiest way to run the application is using docker compose:

```bash
docker compose up -d
```

This will start both the backend service on `http://localhost:8000` and frontend on `http://localhost:3000`.

### Backend

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

### Frontend

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

### Development Workflow

1. Use `docker compose up -d` for full stack development
2. Individual containers can be rebuilt: `docker compose up -d --build backend`
3. Frontend includes backend connectivity test for integration verification
4. API documentation available at `/docs` endpoint

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

For detailed testing documentation, see [`backend/tests/README.md`](backend/tests/README.md).

## Project Status

✅ **Production-ready architecture implemented:**
- ✅ Backend: FastAPI app with comprehensive API, WebSockets, and service layer
- ✅ Frontend: React + TypeScript SPA with Caddy reverse proxy
- ✅ Database: PostgreSQL with Docker containerization
- ✅ HTTPS/SSL: Automatic certificate provisioning via Let's Encrypt (Caddy)
- ✅ Security: Production environment validation, secure cookies, CORS
- ✅ Testing: Comprehensive test suite with 100+ tests

📋 **Before production deployment:**
- ⏳ Database migrations with Alembic (critical)
- ⏳ Rate limiting implementation
- ⏳ Monitoring and log aggregation
- ⏳ Automated backups to cloud storage

See [docs/production_deployment.md](docs/production_deployment.md) for deployment guide.

## Production Deployment

See the comprehensive [Production Deployment Guide](docs/production_deployment.md) for:
- Server prerequisites and DNS configuration
- Environment variable setup
- SSL certificate provisioning
- Database backups and migrations
- Monitoring and logging
- Security checklist
- Troubleshooting

**Quick Start:**
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values (see deployment guide)

# 2. Deploy
docker compose up -d

# 3. Verify
curl https://yourdomain.com
```

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

See [Production Deployment Guide - Troubleshooting](docs/production_deployment.md#troubleshooting) for:
- SSL certificate issues
- CORS errors
- WebSocket connection failures
- Database connection problems

## Development Guidelines

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

### Commit Message Standards

- Keep commit messages simple, descriptive one-liners
- Focus on what changed, not how or why
- Examples: "Add user authentication", "Fix bid retraction bug", "Update product page styling"
- Do not mention AI tools or assistants in commit messages

## Future Considerations

- Payment integration if user base grows
- Image support for product catalogs
- Chat if coordination becomes complex
- BulkPricingTier entity for threshold logic
- Multiple delivery coordination options
- Alembic database migrations (critical before schema changes)
- Rate limiting and API throttling
- Advanced monitoring and alerting