# Unified Development/Production Configuration

## Overview

The codebase now uses **environment variables** to control all dev/prod differences. **No more separate branches!**

## Quick Start

### Development
```bash
cp .env.development .env
docker compose up
```
Access at: https://localhost:3000

### Production
```bash
cp .env.production .env
# Edit .env: Set SECRET_KEY and database password
docker compose build
docker compose up -d
```
Access at: https://vagolan.com/bulq

## Key Environment Variables

### `VITE_BASE_PATH`
Controls the subpath for deployment:
- **Development:** `/` (root path)
- **Production:** `/bulq` (subpath at vagolan.com/bulq)

Affects:
- Vite build base path
- React Router basename
- API URLs
- WebSocket URLs

### `CADDY_LISTEN`
Controls where Caddy listens:
- **Development:** `localhost:3000` (HTTPS with self-signed cert)
- **Production:** `:80` (HTTP behind upstream proxy)

### `FRONTEND_PORT`
Host port mapping:
- **Development:** `3000` (direct access)
- **Production:** `8080` (for upstream reverse proxy)

### `CADDY_PORT`
Container internal port:
- **Development:** `3000`
- **Production:** `80`

### `BACKEND_PORT`
Backend port exposure:
- **Development:** `8000` (exposed for direct access)
- **Production:** `` (empty, not exposed)

### `BACKEND_VOLUME`
Source code mounting for hot-reload:
- **Development:** `./backend` (mount for hot-reload)
- **Production:** `/dev/null` (no mount)

### `BUILD_DEV_DEPS`
Include dev dependencies in Docker build:
- **Development:** `true` (includes pytest, etc.)
- **Production:** `false` (minimal dependencies)

## How It Works

### 1. Frontend Build-Time Configuration

**vite.config.ts:**
```typescript
base: process.env.VITE_BASE_PATH || '/'
```
- Reads from environment during `npm run build`
- Passed via Docker build args
- Controls asset paths in built files

**App.tsx:**
```typescript
const basePath = import.meta.env.VITE_BASE_PATH || '/'
const basename = basePath === '/' ? undefined : basePath
<BrowserRouter basename={basename}>
```
- Reads from build-time env var
- Sets React Router base path dynamically

**config.ts:**
```typescript
const BASE_PATH = import.meta.env.VITE_BASE_PATH || '/'
export const API_BASE_URL = import.meta.env.PROD
  ? BASE_PATH.replace(/\/$/, '')
  : 'http://localhost:8000'
```
- Constructs API URLs with correct base path
- Dev: direct backend connection
- Prod: proxied through Caddy with base path

### 2. Runtime Configuration

**Caddyfile:**
```
{$CADDY_LISTEN:localhost:3000} {
    # ... routes
}
```
- Caddy reads `CADDY_LISTEN` environment variable at runtime
- Dev: listens on `localhost:3000`
- Prod: listens on `:80`

**docker-compose.yml:**
```yaml
backend:
  build:
    args:
      BUILD_DEV_DEPS: ${BUILD_DEV_DEPS:-false}
  ports:
    - "${BACKEND_PORT:-}:8000"
  volumes:
    - ${BACKEND_VOLUME:-/dev/null}:/app

frontend:
  build:
    args:
      VITE_BASE_PATH: ${VITE_BASE_PATH:-/}
  ports:
    - "${FRONTEND_PORT:-3000}:${CADDY_PORT:-3000}"
  environment:
    CADDY_LISTEN: ${CADDY_LISTEN:-localhost:3000}
```
- All configurations controlled by `.env`
- Conditional port exposure
- Conditional volume mounts
- Build args passed to Dockerfiles

## Configuration Files

### `.env.development`
Pre-configured for local development:
- `VITE_BASE_PATH=/`
- `CADDY_LISTEN=localhost:3000`
- `FRONTEND_PORT=3000`
- `BACKEND_PORT=8000` (exposed)
- `BACKEND_VOLUME=./backend` (hot-reload)
- `BUILD_DEV_DEPS=true`
- `REPO_MODE=memory` (in-memory test data)

### `.env.production`
Pre-configured for production at vagolan.com/bulq:
- `VITE_BASE_PATH=/bulq`
- `CADDY_LISTEN=:80`
- `FRONTEND_PORT=8080`
- `BACKEND_PORT=` (not exposed)
- `BACKEND_VOLUME=/dev/null` (no mount)
- `BUILD_DEV_DEPS=false`
- `REPO_MODE=database`
- Requires: SECRET_KEY, database password

### `.env.example`
Template showing all available options with documentation.

## Switching Modes

### From Dev to Prod
```bash
cp .env.production .env
# Edit .env: Set SECRET_KEY and passwords
docker compose build  # Rebuild with new config
docker compose up -d
```

### From Prod to Dev
```bash
cp .env.development .env
docker compose build  # Rebuild with new config
docker compose up
```

### Custom Configuration
```bash
cp .env.example .env
# Edit .env with custom values
docker compose build
docker compose up -d
```

## Architecture Details

### Development Mode
```
Developer → https://localhost:3000 (Caddy with self-signed cert)
                    ↓
                Caddy (frontend proxy)
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
React App (/)              Backend (http://backend:8000)
    ↓                               ↓
Browser assets              PostgreSQL or In-Memory
```

- Single machine
- Direct port access
- Hot-reload enabled
- Self-signed HTTPS cert

### Production Mode
```
Internet → vagolan.com (Upstream Proxy with HTTPS)
              ↓ forwards /bulq/* → http://app-server:8080
          This Server
              ↓
          Caddy (:80)
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
React App (/bulq)   Backend (internal)
                        ↓
                   PostgreSQL (internal)
```

- Behind upstream reverse proxy
- HTTPS handled upstream
- No hot-reload
- Production dependencies only
- Database persistence required

## Troubleshooting

### Assets Not Loading (404)
**Symptom:** JavaScript/CSS files return 404

**Cause:** `VITE_BASE_PATH` mismatch

**Fix:**
- Check `.env` has correct `VITE_BASE_PATH`
- Rebuild: `docker compose build frontend`
- Restart: `docker compose up -d frontend`

### Backend Connection Refused
**Symptom:** API calls fail

**Cause:** Backend port not exposed in production

**Fix:** This is correct! In production, backend is accessed through Caddy proxy, not directly.

### Wrong Base Path in URLs
**Symptom:** URLs don't include `/bulq` prefix

**Cause:** Build-time env var not passed correctly

**Fix:**
```bash
# Rebuild with --no-cache to ensure env vars are picked up
docker compose build --no-cache frontend
docker compose up -d
```

### Hot-Reload Not Working
**Symptom:** Code changes don't reflect

**Cause:** Volume mount not configured

**Fix:**
- Check `.env` has `BACKEND_VOLUME=./backend`
- Restart: `docker compose down && docker compose up`

### Caddy Won't Start
**Symptom:** Frontend container exits immediately

**Cause:** Invalid `CADDY_LISTEN` value

**Fix:**
- Dev: `CADDY_LISTEN=localhost:3000`
- Prod: `CADDY_LISTEN=:80`
- Check `.env` syntax (no quotes, no spaces)

## Benefits of This Approach

✅ **Single Branch:** No more master/prod split
✅ **Single Codebase:** All bug fixes apply everywhere
✅ **Easy Switching:** Just swap `.env` file
✅ **Clear Configuration:** All settings in one place
✅ **No Hardcoded Values:** Everything configurable
✅ **Docker Native:** Uses Docker Compose features properly
✅ **Build-Time Optimization:** Frontend built with correct base path
✅ **Runtime Flexibility:** Caddy adapts without rebuilding

## Migration from Branch-Based Config

The old approach had:
- `master` branch - dev config hardcoded
- `prod` branch - prod config hardcoded
- Manual merging required for bug fixes

The new approach has:
- Single `master` branch
- `.env.development` - dev settings
- `.env.production` - prod settings
- `cp .env.{mode} .env` to switch

**To migrate existing deployments:**
1. Switch to `master` branch
2. Copy appropriate `.env.{mode}` to `.env`
3. Review and update values (SECRET_KEY, passwords, etc.)
4. Rebuild: `docker compose build`
5. Deploy: `docker compose up -d`

## Testing Both Modes Locally

You can test both modes on your dev machine:

**Test Development:**
```bash
cp .env.development .env
docker compose up
# Visit https://localhost:3000
```

**Test Production (locally):**
```bash
cp .env.production .env
# Edit .env: Set valid SECRET_KEY and password
docker compose build
docker compose up -d
# Visit http://localhost:8080
# Note: Will serve at /bulq path
```

## Summary

All configuration is now controlled by environment variables in the `.env` file. No more branch divergence, no more maintaining separate codebases. Just copy the appropriate template and deploy!
