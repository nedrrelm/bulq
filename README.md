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

- **Database Schema**: See [database_schema.md](database_schema.md) for detailed ER diagram
- **Containerized Architecture**: Separate Docker containers for backend, frontend, and database
- **Backend**: FastAPI application running in Python container
- **Database**: PostgreSQL running in dedicated container
- **Frontend**: React + TypeScript application served with Caddy
- **Real-time Updates**: WebSocket connections for live bid tracking

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

## Project Status

🚧 Project in initial development phase
- ✅ Backend: FastAPI app with CORS, health checks, and Docker support
- ✅ Frontend: React + TypeScript app with backend connectivity test and Caddy serving
- ✅ Integration: Frontend-backend communication working via CORS
- ⏳ Database: To be containerized

## Troubleshooting

### Frontend shows "Backend connection failed"
1. Ensure both services are running: `docker compose ps`
2. Check backend is responding: `curl http://localhost:8000/health`
3. If using local development, make sure CORS is configured in the backend

### Port conflicts
- Backend uses port 8000
- Frontend uses port 3000
- Stop existing services: `docker compose down`
- Check for conflicting processes: `lsof -i :8000` or `lsof -i :3000`

### Container build issues
- Clean rebuild: `docker compose build --no-cache`
- Remove old images: `docker system prune`

### Development vs Production
- Frontend in development mode (`npm run dev`) runs on Vite dev server
- Frontend in Docker runs on Caddy serving built static files
- CORS is configured for both `localhost:3000` and `127.0.0.1:3000`