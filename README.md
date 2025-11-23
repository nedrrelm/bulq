# Bulq 📦

> A platform for organizing group purchases to reduce costs through bulk buying

Bulq enables friend groups to coordinate bulk purchases and track savings through organized group buying. The platform helps manage buying runs, calculate individual costs, and track purchase history across different stores.

## Features

- 🛒 **Group buying run management** - Create and organize shopping runs
- 💰 **Cost calculation** - Automatic per-person cost breakdown
- 📊 **Purchase tracking** - Complete history of all group purchases
- 🏪 **Multi-store support** - Compare prices across different stores
- 🔄 **Real-time updates** - Live bid tracking via WebSockets
- 🤝 **Trust-based** - No in-app payments, designed for friend groups

## How It Works

1. **Groups** - Join or create a friend group for coordinated shopping
2. **Runs** - Create shopping runs targeting specific stores
3. **Bidding** - Express interest and specify quantities for products
4. **Confirmation** - Products meeting thresholds are confirmed for purchase
5. **Shopping** - Designated group members execute the shopping list
6. **Settlement** - Costs calculated and settled manually among friends

## Quick Start

```bash
# Copy environment configuration
cp .env.example .env

# Start the application
docker compose up -d
```

Access the application at `http://localhost:3000`

Backend API documentation: `http://localhost:8000/docs`

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React + TypeScript
- **Database**: PostgreSQL
- **Deployment**: Docker with Caddy reverse proxy

## Documentation

- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions
- **[Development Notes](docs/development_notes.md)** - Architecture, setup, and development guidelines
- **[Database Schema](docs/database_schema.md)** - Entity relationship diagrams
- **[Backlog](docs/backlog.md)** - Feature roadmap and technical debt

## Project Status

✅ Production-ready features:
- Complete backend API with authentication, WebSockets, and comprehensive test suite
- Full-featured React frontend with multi-language support (EN/RU/SR)
- PostgreSQL database with Docker containerization
- HTTPS/SSL with automatic Let's Encrypt certificates
- Production environment validation and security features

📋 See [backlog](docs/backlog.md) for upcoming features and improvements.

## Target Users

Friend groups who trust each other and handle discussions/payments outside the app.

## Contributing

See [Development Notes](docs/development_notes.md) for:
- Development setup and workflow
- Code quality standards
- Testing guidelines
- Commit message conventions

## License

_Coming soon - AGPL v3_
