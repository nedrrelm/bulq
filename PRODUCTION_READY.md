# Production Deployment - Ready for vagolan.com/bulq

## 🏗️ Architecture

This app is deployed **behind an upstream reverse proxy**:

```
Internet → vagolan.com (Upstream Reverse Proxy)
              ↓ HTTPS, handles /bulq/*
         This App Server (HTTP on port 8080)
              ↓
         Docker Compose Stack:
           - Caddy (serves frontend, proxies to backend)
           - FastAPI Backend
           - PostgreSQL Database
```

**Key Points:**
- Upstream proxy handles HTTPS/SSL certificates (not this app)
- Upstream proxy routes `vagolan.com/bulq/*` to this server's port 8080
- This app serves on HTTP port 8080 (secure behind upstream proxy)
- Frontend app is built with `/bulq` base path for proper asset loading

## ✅ Completed Changes

All necessary changes have been made to prepare Bulq for production deployment at **vagolan.com/bulq**.

### Files Modified

1. **frontend/Caddyfile**
   - Changed to listen on `:80` (receives requests from upstream proxy)
   - Serves app at root path (upstream proxy strips `/bulq` prefix)
   - Configured reverse proxy to backend for API routes

2. **frontend/vite.config.ts**
   - Added `base: '/bulq/'` for proper asset path handling

3. **frontend/src/App.tsx**
   - Added `basename="/bulq"` to BrowserRouter

4. **frontend/index.html**
   - Added `<base href="/bulq/">` tag
   - Updated title to "Bulq - Bulk Buying Platform"

5. **frontend/src/config.ts**
   - Updated API_BASE_URL to use `/bulq` prefix in production
   - Updated WS_BASE_URL to use `/bulq` prefix in production

6. **docker-compose.yml**
   - Removed backend port exposure (internal network only)
   - Frontend exposed on port 8080 (default, configurable via FRONTEND_PORT)
   - Removed SSL certificate volumes (handled by upstream proxy)

7. **backend/Dockerfile**
   - Removed `--dev` flag from uv sync (production dependencies only)

8. **.env.production** (NEW FILE)
   - Production-ready environment configuration template
   - Includes setup instructions and security checklist

## 🚀 Deployment Instructions

### Prerequisites
- Server with Docker and Docker Compose installed
- Upstream reverse proxy configured to forward `vagolan.com/bulq/*` to this server's port 8080
- Firewall: port 8080 accessible from upstream proxy server

### Step 1: Configure Environment

```bash
# Copy the production template
cp .env.production .env

# Generate a strong SECRET_KEY
openssl rand -hex 32

# Edit .env and replace:
# - REPLACE_WITH_GENERATED_SECRET_KEY (with output from above)
# - REPLACE_WITH_STRONG_PASSWORD (both instances, use same password)

# Secure the .env file
chmod 600 .env
```

### Step 2: Build and Deploy

```bash
# Build all containers
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps
```

### Step 3: Configure Upstream Reverse Proxy

Configure your upstream reverse proxy to forward requests to this server. Example nginx config:

```nginx
# At vagolan.com server
location /bulq/ {
    proxy_pass http://your-app-server:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

Note the trailing slashes - they ensure path rewriting works correctly.

### Step 4: Verify Deployment

```bash
# View logs
docker compose logs -f

# Test from upstream proxy server or locally
curl http://localhost:8080

# Check backend health
docker compose logs backend | grep -i "started"

# Test from internet
curl https://vagolan.com/bulq
```

### Step 5: Monitor First Startup

Watch the logs for:
- ✅ Database connection successful
- ✅ Backend API started
- ✅ Frontend serving on port 8080

## 🔒 Security Checklist

Before going live, verify:

- [ ] Strong SECRET_KEY generated (32+ characters)
- [ ] Strong database password set (16+ characters)
- [ ] `ENV=production` in .env
- [ ] `SECURE_COOKIES=true` in .env
- [ ] `ALLOWED_ORIGINS=https://vagolan.com` in .env
- [ ] `REPO_MODE=database` in .env
- [ ] `FRONTEND_PORT` configured (default 8080)
- [ ] Upstream reverse proxy configured and tested
- [ ] Firewall allows port 8080 from upstream proxy server
- [ ] .env file has restricted permissions: `chmod 600 .env`
- [ ] Backend port NOT exposed to internet (internal only)
- [ ] Database port NOT exposed to internet (internal only)
- [ ] Only port 8080 exposed for upstream proxy access

## 📍 Access URLs

After deployment:
- **Main App**: https://vagolan.com/bulq
- **API Docs**: https://vagolan.com/bulq/docs (FastAPI auto-generated)
- **WebSocket**: wss://vagolan.com/bulq/ws/*
- **Direct Access** (from app server): http://localhost:8080

## 🔧 Upstream Reverse Proxy Configuration

Your upstream proxy at vagolan.com must:

1. **Accept HTTPS requests** at `/bulq/*`
2. **Forward to this server** on port 8080
3. **Strip the `/bulq` prefix** when forwarding (or use path rewriting)
4. **Preserve headers** (X-Forwarded-For, X-Forwarded-Proto, etc.)
5. **Support WebSocket upgrade** for real-time features

### Example Configurations

**Nginx:**
```nginx
location /bulq/ {
    proxy_pass http://bulq-server:8080/;  # Note trailing slashes!
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**Caddy:**
```
vagolan.com {
    handle /bulq/* {
        uri strip_prefix /bulq
        reverse_proxy bulq-server:8080
    }
}
```

**Apache:**
```apache
<Location /bulq>
    ProxyPass http://bulq-server:8080/
    ProxyPassReverse http://bulq-server:8080/
    ProxyPreserveHost On

    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteRule /(.*) ws://bulq-server:8080/$1 [P,L]
</Location>
```

## 🔧 Post-Deployment Tasks

### Set Up Automated Backups

```bash
# Create backup script
sudo mkdir -p /opt/bulq/backups
sudo nano /opt/bulq/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/bulq/backup.sh >> /var/log/bulq-backup.log 2>&1
```

See `docs/production_deployment.md` for backup script template.

### Monitor Application

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f backend
docker compose logs -f frontend

# Check SSL certificate
docker compose exec frontend caddy list-certificates

# Check database
docker compose exec db psql -U bulq -d bulq -c "\dt"
```

### Update Application

```bash
# Pull latest changes
git pull origin prod

# Rebuild and restart
docker compose build
docker compose up -d

# Verify
docker compose ps
docker compose logs -f
```

## 📚 Documentation

For more details, see:
- `docs/production_deployment.md` - Comprehensive deployment guide
- `docs/development_vs_production.md` - Configuration differences
- `README.md` - Project overview and setup

## ⚠️ Important Notes

1. **Subpath Deployment**: The app is configured for `/bulq` subpath. All routes, assets, and API calls include this prefix.

2. **HTTPS Required**: Production mode requires HTTPS. Caddy will automatically provision Let's Encrypt certificates for vagolan.com.

3. **Database Persistence**: Data is stored in Docker volume `postgres_data`. Back up regularly!

4. **First Launch**: SSL certificate provisioning may take 1-2 minutes on first startup.

5. **No Development Tools**: Production build excludes dev dependencies, hot-reload, and debug tools.

## 🆘 Troubleshooting

### Can't Access App from Internet
- Test locally first: `curl http://localhost:8080`
- Check upstream proxy logs
- Verify proxy configuration (path rewriting, trailing slashes)
- Test from upstream proxy server: `curl http://bulq-server:8080`

### Backend Connection Failed
- Check backend status: `docker compose ps backend`
- View logs: `docker compose logs backend`
- Verify CORS: Check ALLOWED_ORIGINS in .env

### WebSocket Not Working
- Ensure using wss:// protocol
- Check Caddy proxy config for /bulq/ws/*
- View backend WebSocket logs

For more troubleshooting, see `docs/production_deployment.md`.

## ✨ You're Ready!

All code changes are complete and committed to the `prod` branch. Follow the deployment instructions above to launch Bulq at vagolan.com/bulq.
