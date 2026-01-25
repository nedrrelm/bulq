# Deployment Guide

Complete guide for running Bulq in development and production environments.

## Quick Start

### Development
```bash
cp .env.example .env
docker compose up
```
Access: http://localhost:1314

### Production
```bash
cp .env.example .env
# Edit .env: set PROD_SECRET_KEY, PROD_POSTGRES_PASSWORD, PROD=true, DEV=
# Comment out backend volume in docker-compose.yml
docker compose build && docker compose up -d
```
Access: https://yourdomain.com

---

## Environment Configuration

Bulq uses a **unified `.env` file** with automatic environment switching. Simply change `DEV`/`PROD` flags, and all configuration values automatically switch.

**How it works:**
- `.env` file contains both `DEV_*` and `PROD_*` prefixed values
- Bash parameter expansion automatically selects the right values
- No manual copying or find-replace needed

See [Unified Environment Configuration Guide](unified_env_guide.md) for technical implementation details.

### Development Mode

**Configuration:**
```bash
# In .env:
DEV=true
PROD=
```

**Characteristics:**
- HTTP (no SSL required)
- CORS allows localhost by default
- In-memory test data (`REPO_MODE=memory`)
- Backend hot-reload enabled
- Frontend: http://localhost:1314
- Backend: Internal only (accessed via Caddy)

**Network:**
```
Browser (localhost:1314)
    ↓ HTTP
Caddy (1314) → Frontend (3000 internal)
            → Backend (8000 internal) → PostgreSQL (5432 internal)
```

### Production Mode

**Configuration:**
```bash
# In .env:
DEV=
PROD=true
```

**Characteristics:**
- HTTPS required (via Caddy + Let's Encrypt)
- Strict CORS validation
- Database required (`REPO_MODE=database`)
- Secure cookies enabled
- Backend NOT exposed to internet
- Frontend: https://yourdomain.com:1314 (or use reverse proxy on port 80/443)
- Backend: Internal only

**Network:**
```
Browser (yourdomain.com:1314)
    ↓ HTTP/HTTPS
Caddy (1314, SSL) → Frontend (3000 internal)
                 → Backend (8000 internal) → PostgreSQL (5432 internal)
```

### Key Differences

| Feature | Development | Production |
|---------|------------|------------|
| **Environment** | `DEV=true` | `PROD=true` |
| **HTTPS** | Optional | Required (automatic) |
| **Cookies** | `SECURE_COOKIES=false` | `SECURE_COOKIES=true` |
| **CORS** | Auto (localhost) | Explicit domain |
| **Database** | Memory or PostgreSQL | PostgreSQL only |
| **Exposed Port** | 1314 | 1314 (or use reverse proxy) |
| **Backend Port** | Internal only | Internal only |
| **Log Format** | Structured | JSON |

### Switching Between Modes

**Development → Production:**
1. Set production values in `.env`:
   ```bash
   PROD_SECRET_KEY=$(openssl rand -hex 32)
   PROD_POSTGRES_PASSWORD=your-strong-password
   PROD_ALLOWED_ORIGINS=https://yourdomain.com
   ```
2. Switch flags: `DEV=` and `PROD=true`
3. Comment out backend volume in `docker-compose.yml`
4. Deploy: `docker compose build && docker compose up -d`

**Production → Development:**
1. Switch flags: `DEV=true` and `PROD=`
2. Uncomment backend volume in `docker-compose.yml`
3. Restart: `docker compose down && docker compose up -d`

---

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/bulq.git
   cd bulq
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Default dev settings work out of the box
   ```

3. **Start services:**
   ```bash
   docker compose up -d
   ```

4. **Verify:**
   - Frontend: http://localhost:1314
   - Backend API: http://localhost:1314/api/docs
   - Backend health: http://localhost:1314/api/health

### Development Workflow

**Full stack:**
```bash
docker compose up -d
docker compose logs -f
```

**Backend only:**
```bash
docker compose up -d backend
docker compose logs -f backend
```

**Rebuild after changes:**
```bash
docker compose up -d --build backend
```

**Backend hot-reload:**
The backend volume mount (`./backend:/app`) enables automatic reloading when you edit Python files.

### Testing

```bash
# Run all tests
docker compose run --rm backend uv run --extra dev pytest tests/ -v

# Run specific test
docker compose run --rm backend uv run --extra dev pytest tests/test_auth.py -v

# With coverage
docker compose run --rm backend uv run --extra dev pytest tests/ --cov=app --cov-report=html
```

---

## Production Deployment

### Prerequisites

1. **Server** with Docker and Docker Compose installed
2. **Domain name** pointing to server IP (optional)
3. **Port 1314** open on firewall (or port 80/443 if using reverse proxy)
4. **DNS A record**: `yourdomain.com → your.server.ip` (if using domain)

### Deployment Steps

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/bulq.git
cd bulq
```

#### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

**Set production values:**
```bash
# Generate strong secret
openssl rand -hex 32
# Copy output to:
PROD_SECRET_KEY=<paste-generated-key-here>

# Set strong database password
PROD_POSTGRES_PASSWORD=YourStrong16+CharPassword

# Update domain if different
PROD_ALLOWED_ORIGINS=https://yourdomain.com
```

**Switch to production mode:**
```bash
DEV=
PROD=true
```

**Verify configuration:**
```bash
grep "^PROD=" .env  # Should show: PROD=true
grep "^DEV=" .env   # Should show: DEV= (empty)
```

#### 3. Update docker-compose.yml

Comment out backend volume mount:
```yaml
backend:
  # volumes:
  #   - ./backend:/app
```

#### 4. Deploy

```bash
# Build and start
docker compose build
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

#### 5. Verify Deployment

**Check HTTPS certificate:**
```bash
curl https://yourdomain.com
```

**Check API health:**
```bash
curl https://yourdomain.com/auth/me
# Should return 401 (not authenticated) - confirms backend working
```

**Check logs:**
```bash
docker compose logs backend | grep "ERROR"
```

### SSL Certificates

Caddy automatically provisions and renews SSL certificates from Let's Encrypt.

**Certificate storage:** Docker volume `caddy_data`

**Manual renewal (if needed):**
```bash
docker compose exec frontend caddy reload --config /etc/caddy/Caddyfile
```

### Database Backups

**Manual backup:**
```bash
docker compose exec db pg_dump -U bulq bulq > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore backup:**
```bash
docker compose exec -T db psql -U bulq bulq < backup_20250101_120000.sql
```

**Automated backups:**
Create `/opt/bulq/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/bulq/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f /opt/bulq/docker-compose.yml exec -T db pg_dump -U bulq bulq > "$BACKUP_DIR/bulq_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/bulq_$TIMESTAMP.sql"
find "$BACKUP_DIR" -name "bulq_*.sql.gz" -mtime +30 -delete
```

Add to cron:
```bash
chmod +x /opt/bulq/backup.sh
crontab -e
# Add: 0 2 * * * /opt/bulq/backup.sh >> /var/log/bulq-backup.log 2>&1
```

### Updating Application

```bash
cd /opt/bulq
git pull origin main
docker compose build
docker compose up -d
docker compose logs -f
```

### Rollback Procedure

```bash
docker compose down
git checkout <previous-tag-or-commit>
docker compose exec -T db psql -U bulq bulq < backup_previous.sql
docker compose build
docker compose up -d
```

---

## Troubleshooting

### SSL Certificate Issues

**Symptoms:** Caddy can't provision SSL certificate

**Solutions:**
1. Verify DNS: `dig yourdomain.com`
2. Check ports: `sudo netstat -tlnp | grep :80`
3. Check Caddy logs: `docker compose logs frontend | grep -i certificate`
4. Ensure domain accessible from internet (not just locally)

### Backend Connection Failed

**Symptoms:** Frontend shows "Backend connection failed"

**Solutions:**
1. Check backend running: `docker compose ps backend`
2. Check backend logs: `docker compose logs backend`
3. Verify CORS: Check `ALLOWED_ORIGINS` in `.env`
4. Test backend: `docker compose exec frontend wget -O- http://backend:8000/health`

### Database Connection Failed

**Symptoms:** Backend logs show "could not connect to database"

**Solutions:**
1. Check database healthy: `docker compose ps db`
2. Check database logs: `docker compose logs db`
3. Verify `DATABASE_URL` in `.env`
4. Test connection: `docker compose exec backend env | grep DATABASE_URL`

### CORS Errors in Browser

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Verify `ALLOWED_ORIGINS` matches domain exactly (including `https://`)
2. No trailing slash in domain
3. Ensure `SECURE_COOKIES=true` when using HTTPS
4. Check backend logs for CORS errors

### WebSocket Connection Failed

**Symptoms:** Real-time updates not working

**Solutions:**
1. Check Caddy config for `/ws/*` proxying
2. Verify WebSocket URL in browser console
3. Check backend logs for WebSocket errors

### Port Already in Use

```bash
lsof -i :1314  # Check if port is in use
```

Kill conflicting process or change `CADDY_PORT` in `.env`.

---

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend --tail=100

# Search for errors
docker compose logs backend | grep ERROR

# JSON logs (production)
docker compose logs backend | jq -r 'select(.level == "ERROR")'
```

### Health Checks

```bash
# Check all services
docker compose ps

# Database health
docker compose exec db pg_isready -U bulq -d bulq

# Backend health
curl http://localhost:1314/api/health  # dev
curl https://yourdomain.com:1314/api/health  # prod
```

### Container Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

### Routine Maintenance

**Daily:**
- Monitor logs for errors
- Check disk space: `df -h`

**Weekly:**
- Review backup logs
- Check container health

**Monthly:**
- Update dependencies
- Security patches
- Performance review

---

## Security Checklist

### Production Deployment

- [ ] `PROD=true` and `DEV=` (empty) in `.env`
- [ ] Strong `PROD_SECRET_KEY` (32+ chars)
- [ ] Strong `PROD_POSTGRES_PASSWORD` (16+ chars)
- [ ] `ALLOWED_ORIGINS` set to production domain
- [ ] `SECURE_COOKIES=true`
- [ ] Backend volume mount commented out
- [ ] Firewall: only port 1314 open (or 80/443 if using reverse proxy)
- [ ] Database port (5432) NOT exposed
- [ ] Backend port (8000) NOT exposed
- [ ] Frontend port (3000) NOT exposed
- [ ] `.env` permissions: `chmod 600 .env`
- [ ] Automated backups configured
- [ ] SSL certificate provisioned
- [ ] Upstream reverse proxy configured (if applicable)

---

## Next Steps

After successful deployment:

1. **Monitor logs** for first 24 hours
2. **Test all features** in production
3. **Configure monitoring** (Prometheus, Grafana, etc.)
4. **Set up alerts** (uptime, errors, disk space)
5. **Document runbooks** for common issues
6. **Create staging environment** for testing updates

For technical details on the unified environment system, see [Unified Environment Configuration Guide](unified_env_guide.md).
