# Production Deployment Guide

This guide covers deploying Bulq to production with Docker, Caddy reverse proxy, and automatic HTTPS/SSL certificates via Let's Encrypt.

## Overview

The production stack consists of:
- **PostgreSQL** - Database (internal network only)
- **FastAPI Backend** - Python API server (internal network only)
- **Caddy + React Frontend** - Reverse proxy and static file server (exposed on ports 80/443)

Caddy handles:
- HTTPS/SSL certificate provisioning via Let's Encrypt
- Reverse proxying API requests to backend
- Serving static React frontend files
- WebSocket proxying for real-time updates
- Security headers

## Prerequisites

1. **Server with Docker and Docker Compose** installed
2. **Domain name** pointing to your server's IP address
3. **Ports 80 and 443** open on your firewall (required for Let's Encrypt)
4. **DNS A record** configured: `yourdomain.com` → `your.server.ip`

## Production Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/bulq.git
cd bulq
```

### 2. Configure Environment Variables

Copy the example environment file and configure for production:

```bash
cp .env.example .env
```

Edit `.env` with production values:

```bash
# REQUIRED: Set to production mode
ENV=production

# REQUIRED: Generate a strong secret key
# Generate with: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-here

# REQUIRED: Enable secure cookies (requires HTTPS)
SECURE_COOKIES=true

# Database configuration
POSTGRES_DB=bulq
POSTGRES_USER=bulq
POSTGRES_PASSWORD=change-to-strong-password
DATABASE_URL=postgresql://bulq:change-to-strong-password@db:5432/bulq

# REQUIRED: Use database mode in production
REPO_MODE=database

# Session configuration
SESSION_EXPIRY_HOURS=24

# REQUIRED: Set allowed origins to your domain
ALLOWED_ORIGINS=https://yourdomain.com

# REQUIRED: Set your domain for automatic HTTPS
DOMAIN=yourdomain.com

# Port configuration (defaults are fine)
FRONTEND_PORT=3000
HTTP_PORT=80
HTTPS_PORT=443

# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log
```

### 3. Verify Configuration

Production mode enforces strict validation. The application will fail to start if:

- `ENV=production` but `ALLOWED_ORIGINS` is not set
- `ENV=production` but `SECURE_COOKIES=false`
- `REPO_MODE=database` but `DATABASE_URL` is not set

This prevents accidentally running in insecure mode.

### 4. Deploy with Docker Compose

```bash
# Build and start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f db
```

### 5. Verify Deployment

**Check HTTPS Certificate:**
```bash
# Caddy should automatically provision SSL certificate
curl https://yourdomain.com
```

**Check API Health:**
```bash
curl https://yourdomain.com/auth/me
# Should return 401 (not authenticated) - this confirms backend is working
```

**Check WebSocket:**
Open browser console at `https://yourdomain.com` and verify WebSocket connections work.

## DNS Configuration

Ensure your DNS is properly configured **before** deploying:

```
Type: A
Name: yourdomain.com (or @)
Value: your.server.ip.address
TTL: 3600
```

For www subdomain:
```
Type: CNAME
Name: www
Value: yourdomain.com
TTL: 3600
```

## Firewall Configuration

Allow incoming traffic on ports 80 and 443:

**UFW (Ubuntu):**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**firewalld (CentOS/RHEL):**
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## SSL Certificate Management

Caddy automatically provisions and renews SSL certificates from Let's Encrypt.

**Certificate Storage:**
Certificates are stored in the `caddy_data` Docker volume.

**Manual Certificate Renewal:**
```bash
# Certificates auto-renew, but to force renewal:
docker compose exec frontend caddy reload --config /etc/caddy/Caddyfile
```

**View Certificate Info:**
```bash
docker compose exec frontend caddy list-certificates
```

## Database Management

### Initial Setup

The database is automatically initialized on first startup. Tables are created based on SQLAlchemy models.

### Backups

**Manual Backup:**
```bash
# Create backup
docker compose exec db pg_dump -U bulq bulq > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T db psql -U bulq bulq < backup_20250101_120000.sql
```

**Automated Backups (recommended):**

Create a backup script at `/opt/bulq/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/bulq/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bulq_$TIMESTAMP.sql"

# Create backup
docker compose -f /opt/bulq/docker-compose.yml exec -T db pg_dump -U bulq bulq > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "bulq_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Make executable and add to cron:
```bash
chmod +x /opt/bulq/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /opt/bulq/backup.sh >> /var/log/bulq-backup.log 2>&1
```

### Database Migrations

**⚠️ Important:** Before production use, set up Alembic for database migrations (see [backlog.md](backlog.md)).

Currently using `create_tables()` which can't handle schema changes. This is acceptable for initial deployment but must be replaced with migrations before making schema changes in production.

## Monitoring and Logs

### View Logs

```bash
# All services
docker compose logs -f

# Specific service with tail
docker compose logs -f --tail=100 backend

# Search logs
docker compose logs backend | grep ERROR
```

### Log Configuration

Production logs are in JSON format for easy parsing:

```bash
# Parse JSON logs
docker compose logs backend | jq -r 'select(.level == "ERROR")'

# View requests with errors
docker compose logs backend | jq -r 'select(.status_code >= 400)'
```

### Health Checks

The database includes a health check. Backend depends on healthy database:

```bash
# Check service health
docker compose ps

# Should show "healthy" status for db service
```

## Updating the Application

### Update Code

```bash
cd /opt/bulq
git pull origin main
```

### Rebuild and Deploy

```bash
# Rebuild images
docker compose build

# Restart services
docker compose up -d

# View updated logs
docker compose logs -f
```

### Zero-Downtime Deployment (Advanced)

For production with users, use rolling updates:

```bash
# Scale up new version
docker compose up -d --scale backend=2 --no-recreate

# Health check new instance
# ... verify new instance is healthy ...

# Remove old instance
docker compose up -d --scale backend=1
```

## Security Checklist

- [ ] `ENV=production` set in `.env`
- [ ] Strong `SECRET_KEY` generated (32+ characters)
- [ ] `SECURE_COOKIES=true` enabled
- [ ] `ALLOWED_ORIGINS` set to production domain only
- [ ] Strong database password configured
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] Database port (5432) NOT exposed to internet
- [ ] Backend port (8000) NOT exposed to internet
- [ ] SSL certificate provisioned successfully
- [ ] Automated backups configured
- [ ] Log monitoring set up
- [ ] `.env` file has restricted permissions: `chmod 600 .env`

## Troubleshooting

### SSL Certificate Not Provisioning

**Symptoms:** Caddy can't provision SSL certificate

**Solutions:**
1. Verify DNS points to server: `dig yourdomain.com`
2. Verify ports 80/443 are open: `sudo netstat -tlnp | grep :80`
3. Check Caddy logs: `docker compose logs frontend | grep -i certificate`
4. Ensure `DOMAIN` environment variable is set
5. Verify domain is accessible from internet (not just locally)

### Backend Connection Failed

**Symptoms:** Frontend shows "Backend connection failed"

**Solutions:**
1. Check backend is running: `docker compose ps backend`
2. Check backend logs: `docker compose logs backend`
3. Verify CORS configuration: Check `ALLOWED_ORIGINS` includes your domain
4. Test backend directly: `docker compose exec frontend wget -O- http://backend:8000/auth/me`

### Database Connection Failed

**Symptoms:** Backend logs show "could not connect to database"

**Solutions:**
1. Check database is healthy: `docker compose ps db`
2. Check database logs: `docker compose logs db`
3. Verify `DATABASE_URL` in `.env`
4. Verify database credentials match
5. Test connection: `docker compose exec backend env | grep DATABASE_URL`

### CORS Errors in Browser

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Verify `ALLOWED_ORIGINS` matches your domain exactly (including https://)
2. Verify domain doesn't have trailing slash
3. Check backend logs for CORS errors
4. Ensure `SECURE_COOKIES=true` when using HTTPS

### WebSocket Connection Failed

**Symptoms:** Real-time updates not working

**Solutions:**
1. Check Caddy reverse proxy config for `/ws/*`
2. Verify WebSocket URL in browser console
3. Check backend logs for WebSocket errors
4. Ensure firewall allows WebSocket upgrade requests

## Performance Tuning

### Database Connection Pool

Adjust pool size based on load in `.env`:

```bash
DB_POOL_SIZE=20          # Concurrent connections
DB_MAX_OVERFLOW=10       # Additional connections when pool exhausted
DB_POOL_TIMEOUT=30       # Seconds to wait for connection
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour
```

### Caddy Optimization

Caddy automatically enables:
- HTTP/2
- Gzip compression
- Asset caching

### Backend Scaling

For high load, scale backend horizontally:

```bash
# Run multiple backend instances
docker compose up -d --scale backend=3
```

Configure Caddy load balancing in `Caddyfile`:
```
reverse_proxy /auth/* {
    to backend:8000
    lb_policy round_robin
    health_uri /health
    health_interval 10s
}
```

## Maintenance

### Routine Tasks

**Weekly:**
- Review logs for errors
- Check disk space: `df -h`
- Verify backups are running

**Monthly:**
- Review and rotate logs
- Update dependencies
- Security patches

**Quarterly:**
- Review and optimize database
- Performance testing
- Security audit

### Container Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full cleanup (careful!)
docker system prune -a --volumes
```

## Rollback Procedure

If deployment fails:

```bash
# Stop containers
docker compose down

# Restore previous code
git checkout previous-tag-or-commit

# Restore database backup
docker compose exec -T db psql -U bulq bulq < backup_previous.sql

# Rebuild and start
docker compose build
docker compose up -d
```

## Support and Resources

- **Documentation:** `/docs` directory
- **Backend API:** `https://yourdomain.com/docs` (FastAPI auto-generated)
- **Logs:** `docker compose logs`
- **Health Check:** `https://yourdomain.com/auth/me`

## Next Steps

After successful deployment:

1. Set up monitoring (Prometheus, Grafana, etc.)
2. Configure rate limiting (see [backlog.md](backlog.md))
3. Set up automated backups to S3/cloud storage
4. Implement database migrations with Alembic
5. Configure log aggregation (ELK, Datadog, etc.)
6. Set up uptime monitoring
7. Create staging environment
