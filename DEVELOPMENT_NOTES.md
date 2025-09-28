# Development Notes

## Architecture Decisions

- **Monolithic Backend**: Single FastAPI application, suitable for expected load
- **Containerized Development**: Docker Compose for consistent environments
- **Frontend-Backend Separation**: React frontend, FastAPI backend with CORS
- **WebSockets**: For real-time bid updates during group orders (planned)
- **No Image Storage**: Avoiding complexity, text-based product descriptions only
- **PostgreSQL with UUIDs**: For primary keys across all entities (planned)

## Core Entity Logic

### Run States Flow
`planning` → `active` → `confirmed` → `shopping` → `completed`
- Can transition to `cancelled` from any state before `shopping`

### ProductBid System
- **interested_only**: Boolean flag for expressing interest without commitment
- **quantity**: Required for items to make it to shopping list
- Real-time totals calculated from sum of quantities per product per run

### Thresholds
- Deferred for initial version
- Will integrate with bulk pricing tiers later
- For now, any product with quantity bids gets confirmed

### Shopping List Generation
- Calculated view, not stored entity
- Confirmed products = products with quantity > 0
- Quantities = sum of all user bids per product
- Assigned to designated_shoppers stored in Run

## Non-Features (Intentionally Excluded)

- In-app payments (users settle manually)
- Chat functionality (users communicate externally)
- Image uploads/storage
- Complex shopping assignment tracking

## Design Principles

- Trust-based system for friend groups
- Focus on management and calculation tools
- Keep it simple for initial version
- Real-time updates for engagement

## Data Entry Strategy

- Manual store/product entry initially
- Future: Store API integration or scraping
- Price tracking built into Product entity

## Development Environment

### Current Stack Implementation
- **Backend**: FastAPI with uv dependency management
- **Frontend**: React + TypeScript with Vite build tool
- **Containerization**: Docker with multi-stage builds
- **Web Server**: Caddy for frontend serving
- **Node.js Management**: Volta for consistent Node.js versions
- **CORS**: Configured for localhost:3000 frontend communication

### Development Workflow
1. Use `docker compose up -d` for full stack development
2. Individual containers can be rebuilt: `docker compose up -d --build backend`
3. Frontend includes backend connectivity test for integration verification
4. API documentation available at `/docs` endpoint

## Future Considerations

- Payment integration if user base grows
- Image support for product catalogs
- Chat if coordination becomes complex
- BulkPricingTier entity for threshold logic
- Multiple delivery coordination options
- Database containerization and persistence
- Production deployment configuration