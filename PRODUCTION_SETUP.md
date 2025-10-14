# Production Setup - Quick Reference

This document provides a quick reference for the production-ready Docker setup. For comprehensive details, see [docs/production_deployment.md](docs/production_deployment.md).

## What's New

### ✅ Implemented

1. **Caddy Reverse Proxy**
   - Automatic HTTPS/SSL via Let's Encrypt
   - API request proxying to backend
   - Security headers (HSTS, X-Frame-Options, etc.)
   - Gzip compression

2. **Production Environment Validation**
   - `ENV=production` enforces strict security settings
   - Required: `ALLOWED_ORIGINS`, `SECURE_COOKIES=true`, `REPO_MODE=database`
   - Application fails to start with invalid production config

3. **Docker Network Isolation**
   - Backend not exposed to internet (internal network only)
   - Database not exposed to internet (internal network only)
   - Only Caddy exposed on ports 80/443

4. **Environment-Based Configuration**
   - Development mode: Permissive defaults, HTTP allowed
   - Production mode: Strict validation, HTTPS required

## Quick Start

### Development (Current Setup)

```bash
# Uses existing .env (development mode)
docker compose up -d

# Access at http://localhost:3000
```

### Production Deployment

```bash
# 1. Update .env for production
cp .env .env.production
nano .env.production

# Set these variables:
ENV=production
SECURE_COOKIES=true
ALLOWED_ORIGINS=https://yourdomain.com
DOMAIN=yourdomain.com
REPO_MODE=database

# 2. Use production .env
mv .env .env.development
mv .env.production .env

# 3. Deploy
docker compose up -d

# 4. Access at https://yourdomain.com
```

## File Changes Summary

### Modified Files

1. **`frontend/Caddyfile`**
   - Added reverse proxy for all backend routes
   - Added production block with DOMAIN environment variable
   - Added security headers
   - Configured automatic HTTPS

2. **`docker-compose.yml`**
   - Backend port no longer exposed (internal only)
   - Database port no longer exposed (internal only)
   - Added Caddy data volumes for SSL certificates
   - Added ports 80/443 for production HTTPS
   - Added custom network for service isolation

3. **`backend/app/config.py`**
   - Added `ENV` and `IS_PRODUCTION` configuration
   - Added production validation (CORS, cookies, database)
   - ALLOWED_ORIGINS parsing with defaults for development

4. **`frontend/src/config.ts`**
   - Production uses relative URLs (Caddy handles routing)
   - WebSocket URL auto-detects protocol (ws/wss)
   - Development uses direct backend connection

5. **`.env.example`**
   - Added production configuration sections
   - Added DOMAIN variable for SSL
   - Added comprehensive comments

### New Files

1. **`docs/production_deployment.md`**
   - Complete deployment guide
   - Security checklist
   - Troubleshooting
   - Backup procedures

2. **`docs/development_vs_production.md`**
   - Side-by-side comparison
   - Common pitfalls
   - Configuration examples

## Environment Variables Reference

| Variable | Development | Production | Required |
|----------|------------|------------|----------|
| `ENV` | `development` | `production` | Yes |
| `SECRET_KEY` | Any string | 32+ char random | Yes |
| `SECURE_COOKIES` | `false` | `true` | Yes (production) |
| `ALLOWED_ORIGINS` | Empty (auto) | `https://domain.com` | Yes (production) |
| `DOMAIN` | Empty | `yourdomain.com` | Yes (production) |
| `REPO_MODE` | `memory` or `database` | `database` | Yes (production) |

## Architecture Diagram

### Before (Development Only)

```
Browser → Frontend:3000 (Docker)
Browser → Backend:8000 (Docker)
Backend → Database:5432 (Docker)
```

### After (Production-Ready)

```
Browser → Caddy:443 (HTTPS)
           ├─→ /auth/* → Backend:8000 (internal)
           ├─→ /runs/* → Backend:8000 (internal)
           └─→ /* → React Static Files
                      Backend → Database:5432 (internal)
```

## Security Improvements

1. **HTTPS by Default**: Automatic SSL certificates via Let's Encrypt
2. **Secure Cookies**: Session cookies marked secure, HTTP-only
3. **Network Isolation**: Backend and database not exposed
4. **CORS Validation**: Strict origin checking in production
5. **Security Headers**: HSTS, clickjacking protection, etc.
6. **Configuration Validation**: Prevents insecure deployments

## Testing Production Locally

```bash
# 1. Add to /etc/hosts
echo "127.0.0.1 local.bulq.test" | sudo tee -a /etc/hosts

# 2. Create production .env
ENV=production
DOMAIN=local.bulq.test
ALLOWED_ORIGINS=https://local.bulq.test
SECURE_COOKIES=true
REPO_MODE=database
# ... other vars ...

# 3. Deploy
docker compose up -d

# 4. Access at https://local.bulq.test (accept self-signed cert)
```

## Rollback to Development

```bash
# 1. Restore development .env
mv .env .env.production
mv .env.development .env

# 2. Restart
docker compose down
docker compose up -d

# 3. Access at http://localhost:3000
```

## Next Steps

Before deploying to production:

1. ⚠️ **Critical**: Set up Alembic database migrations (see `docs/backlog.md`)
2. Configure automated backups
3. Set up monitoring and logging
4. Implement rate limiting
5. Review security checklist in deployment guide

## Documentation

- **Comprehensive Guide**: [docs/production_deployment.md](docs/production_deployment.md)
- **Dev vs Prod**: [docs/development_vs_production.md](docs/development_vs_production.md)
- **Backlog**: [docs/backlog.md](docs/backlog.md)
- **Architecture**: [docs/project_structure.md](docs/project_structure.md)

## Support

If you encounter issues:

1. Check the [Troubleshooting section](docs/production_deployment.md#troubleshooting)
2. Review logs: `docker compose logs -f`
3. Verify configuration: Check environment variables match requirements
4. Test connectivity: Ensure DNS, firewall, and ports are configured

## Summary

The application is now production-ready with:
- ✅ Automatic HTTPS/SSL
- ✅ Reverse proxy architecture
- ✅ Security hardening
- ✅ Environment-based configuration
- ✅ Comprehensive documentation

Deploy with confidence! 🚀
