# Deployment Guide

Complete guide for running Bulq in development and production environments.

## Quick Start

### Development
```bash
git clone https://github.com/nedrrelm/bulq.git
cd bulq
just dev  # or: docker compose up -d
```
Access: http://localhost:1314

### Production
```bash
git clone https://github.com/nedrrelm/bulq.git
cd bulq
cp deployment/.env.prod.example deployment/.env.prod
# Edit deployment/.env.prod - set secrets
just prod --build
```

---

## Environment Configuration

### Development (Default)

**File**: `.env` (tracked in git)

The `.env` file is already configured for development and is tracked in git. No setup needed!

**Configuration:**
- `REPO_MODE=memory` - In-memory data (no DB required, resets on restart)
- `SECURE_COOKIES=false` - HTTP cookies for localhost
- `CADDY_PORT=1314` - App runs on port 1314
- Dev dependencies enabled

**To use PostgreSQL in development:**
```bash
# Edit .env
REPO_MODE=database

# Restart
just down && just dev
```

### Production

**File**: `deployment/.env.prod` (gitignored, created from template)

**Setup:**
```bash
# 1. Copy template
cp deployment/.env.prod.example deployment/.env.prod

# 2. Edit and set secrets
vim deployment/.env.prod

# Required changes:
# - SECRET_KEY: Generate with `openssl rand -hex 32`
# - POSTGRES_PASSWORD: Strong password (16+ chars)
# - ALLOWED_ORIGINS: Your production domain with https://
# - CADDY_DOMAIN: Your domain name

# 3. Set secure permissions
chmod 600 deployment/.env.prod
```

---

## Docker Compose Files

### File Structure

```
bulq/
├── docker-compose.yml           # Base configuration
├── docker-compose.dev.yml       # Development overrides
├── deployment/
│   └── docker-compose.prod.yml  # Production overrides
```

### Development (default)

**Files used**: `docker-compose.yml` + `docker-compose.dev.yml`

```bash
# Using justfile (recommended)
just dev              # Start
just dev --build      # Build and start
just down             # Stop
just logs             # View all logs
just logs backend     # View backend logs
just ps               # Show status

# Direct docker compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Dev-specific features:**
- Backend code mounted for hot-reload (`./backend:/app`)
- Development dependencies included
- In-memory data by default

### Production

**Files used**: `docker-compose.yml` + `deployment/docker-compose.prod.yml`
**Env file**: `deployment/.env.prod`

```bash
# Using justfile (recommended)
just prod --build     # Build and start
just prod             # Start (without build)
just down             # Stop
just logs             # View all logs
just logs backend     # View backend logs
just ps               # Show status

# Direct docker compose
docker compose \\
  -f docker-compose.yml \\
  -f deployment/docker-compose.prod.yml \\
  --env-file deployment/.env.prod \\
  up -d
```

**Prod-specific features:**
- No code mounting (uses built image)
- No development dependencies
- Production logging (JSON format)

---

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Git
- (Optional) just command runner

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/nedrrelm/bulq.git
   cd bulq
   ```

2. **Start application:**
   ```bash
   just dev
   # or
   docker compose up -d
   ```

3. **Verify:**
   - Frontend: http://localhost:1314
   - Backend API: http://localhost:1314/api/docs
   - Backend health: http://localhost:1314/api/health

### Development Workflow

**Start/stop:**
```bash
just dev             # Start all services
just dev --build     # Rebuild and start
just down            # Stop all services
```

**View logs:**
```bash
just logs            # All services
just logs backend    # Specific service
```

### Testing

```bash
# Run tests in backend container
docker compose exec backend uv run --extra dev pytest tests/ -v

# With coverage
docker compose exec backend uv run --extra dev pytest tests/ --cov=app --cov-report=html
```

### Linting

```bash
just lint
# or
docker compose exec backend uv run --extra dev ruff format app/
docker compose exec backend uv run --extra dev ruff check app/ --fix
```

---

## Production Deployment

### Prerequisites

1. **Server** with Docker and Docker Compose installed
2. **Domain name** pointing to server IP (optional but recommended)
3. **Port 1314** open on firewall (or port 80/443 if using reverse proxy)
4. **DNS A record**: `yourdomain.com → your.server.ip` (if using domain)

### Initial Deployment

#### 1. Clone Repository

```bash
git clone https://github.com/nedrrelm/bulq.git
cd bulq
```

#### 2. Configure Production Environment

```bash
# Copy production template
cp deployment/.env.prod.example deployment/.env.prod
```

Edit `deployment/.env.prod`:

**Required changes:**
```bash
# Generate secret key
openssl rand -hex 32
# Paste result:
SECRET_KEY=<generated-key>

# Set strong database password
POSTGRES_PASSWORD=YourStrong16+CharPassword

# Update domain
ALLOWED_ORIGINS=https://yourdomain.com
CADDY_DOMAIN=yourdomain.com
```

**Optional changes:**
```bash
# Port (default 1314, or use reverse proxy for 80/443)
CADDY_PORT=1314

# Logging
LOG_LEVEL=INFO
```

**Set secure permissions:**
```bash
chmod 600 deployment/.env.prod
```

#### 3. Deploy

```bash
# Using justfile (recommended)
just prod --build

# Or manually
docker compose \\
  -f docker-compose.yml \\
  -f deployment/docker-compose.prod.yml \\
  --env-file deployment/.env.prod \\
  up -d --build
```

#### 4. Verify Deployment

**Check services:**
```bash
just ps
# Should show all services running
```

**Test access:**
```bash
curl https://yourdomain.com:1314
# or if using reverse proxy:
curl https://yourdomain.com
```

**Check API health:**
```bash
curl https://yourdomain.com:1314/api/health
# Should return: {"status":"ok"}
```

**Check logs:**
```bash
just logs
```

### SSL/HTTPS Configuration

Caddy automatically provisions SSL certificates from Let's Encrypt when:
- `CADDY_DOMAIN` is set to your actual domain (not `localhost`)
- Port 80 is accessible (for ACME challenge)
- Domain DNS points to your server

**Note**: If using port 1314 instead of 80/443, you may need a reverse proxy in front of Caddy for automatic SSL. See "Using Reverse Proxy" section below.

### Using Reverse Proxy

If you want to use standard ports (80/443) with other apps:

**Example Nginx config:**
```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name bulq.yourdomain.com;

    # SSL config here

    location / {
        proxy_pass http://localhost:1314;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Backups

**Manual backup:**
```bash
docker compose \\
  -f docker-compose.yml \\
  -f deployment/docker-compose.prod.yml \\
  --env-file deployment/.env.prod \\
  exec db pg_dump -U bulq bulq > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore backup:**
```bash
docker compose \\
  -f docker-compose.yml \\
  -f deployment/docker-compose.prod.yml \\
  --env-file deployment/.env.prod \\
  exec -T db psql -U bulq bulq < backup_20250101_120000.sql
```

**Automated backups** (add to cron):
```bash
#!/bin/bash
BACKUP_DIR="/opt/bulq/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cd /opt/bulq
docker compose -f docker-compose.yml -f deployment/docker-compose.prod.yml --env-file deployment/.env.prod exec -T db pg_dump -U bulq bulq > "$BACKUP_DIR/bulq_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/bulq_$TIMESTAMP.sql"
find "$BACKUP_DIR" -name "bulq_*.sql.gz" -mtime +30 -delete
```

### Updating Application

```bash
cd /opt/bulq
git pull origin main
just prod --build
```

---

## Troubleshooting

### Backend Connection Failed

**Check services:**
```bash
just ps
```

**Check logs:**
```bash
just logs
just logs backend
```

**Verify CORS:**
- Dev: `ALLOWED_ORIGINS` should be empty
- Prod: `ALLOWED_ORIGINS` must match your domain exactly

### Database Connection Failed

**Check database:**
```bash
docker compose exec db pg_isready -U bulq -d bulq
```

**Check logs:**
```bash
just logs db
```

### Port Already in Use

```bash
lsof -i :1314  # Check if port is in use
```

Kill conflicting process or change `CADDY_PORT` in `.env` (dev) or `deployment/.env.prod` (prod).

### WebSocket Connection Failed

**Check logs:**
```bash
just logs backend | grep -i websocket
```

**Verify Caddyfile** includes WebSocket proxy:
```
reverse_proxy /ws/* backend:8000
```

---

## Health Checks

```bash
# Check all services
just ps

# Database health
docker compose exec db pg_isready -U bulq -d bulq

# Backend health
curl http://localhost:1314/api/health          # dev
curl https://yourdomain.com:1314/api/health    # prod
```

---

## Security Checklist

### Production Deployment

- [ ] Strong `SECRET_KEY` generated (32+ chars)
- [ ] Strong `POSTGRES_PASSWORD` (16+ chars)
- [ ] `ALLOWED_ORIGINS` set to production domain (with https://)
- [ ] `SECURE_COOKIES=true`
- [ ] `deployment/.env.prod` permissions: `chmod 600`
- [ ] Firewall: only port 1314 open (or 80/443 if using reverse proxy)
- [ ] Database port (5432) NOT exposed to internet
- [ ] Backend port (8000) NOT exposed to internet
- [ ] Frontend internal port (3000) NOT exposed to internet
- [ ] Automated backups configured
- [ ] SSL certificate provisioned (if using Caddy directly)
- [ ] Upstream reverse proxy configured (if applicable)

---

## Architecture

### Development
```
Browser (localhost:1314)
    ↓ HTTP
Caddy (1314) → Frontend (3000 internal) - hot reload enabled
            → Backend (8000 internal) - hot reload enabled
            → PostgreSQL (5432 internal) or in-memory
```

### Production
```
Browser (yourdomain.com:1314)
    ↓ HTTPS
Caddy (1314, SSL) → Frontend (3000 internal) - static build
                 → Backend (8000 internal) - production
                 → PostgreSQL (5432 internal)
```

**Key differences:**
- Dev: Code mounted for hot-reload
- Prod: Baked into image, no hot-reload
- Dev: In-memory data by default
- Prod: PostgreSQL required

---

## Next Steps

After successful deployment:

1. **Monitor logs** for first 24 hours
2. **Test all features** in production environment
3. **Configure monitoring** (Prometheus, Grafana, etc.)
4. **Set up alerts** (uptime, errors, disk space)
5. **Document runbooks** for common issues
6. **Create staging environment** for testing updates
