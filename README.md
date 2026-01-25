# Bulq 📦
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

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
# Clone and start (development mode)
git clone https://github.com/nedrrelm/bulq.git
cd bulq
just dev

# Or without just
docker compose up -d
```

Access the application at `http://localhost:1314`

Backend API documentation: `http://localhost:1314/api/docs`

> **Note**: The `.env` file is already configured for development. No setup needed!

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

This project is licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later).

**Copyright (C) 2025 nedrrelm**

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See the [LICENSE](LICENSE) file for the full license text.

### What this means:

- ✅ **You can use, modify, and distribute** this software freely
- ✅ **You can run it as a service** (SaaS/hosted application)
- ⚠️ **If you modify and deploy** it as a network service, you must make your source code available to users
- ⚠️ **Derivative works** must also be licensed under AGPL-3.0

For more information about the AGPL license, see https://www.gnu.org/licenses/agpl-3.0.html
