# Development vs Production Configuration

This document explains the key differences between development and production modes in Bulq.

## Quick Reference

| Feature | Development | Production |
|---------|------------|------------|
| **Environment** | `ENV=development` | `ENV=production` |
| **HTTPS** | HTTP (optional) | HTTPS (required) |
| **Cookies** | `SECURE_COOKIES=false` | `SECURE_COOKIES=true` |
| **CORS** | Auto-defaults to localhost | Must be explicitly configured |
| **Database** | `REPO_MODE=memory` (optional) | `REPO_MODE=database` (required) |
| **Frontend Port** | 3000 | 80/443 |
| **Backend Port** | 8000 (exposed) | 8000 (internal only) |
| **Log Format** | Structured (key=value) | JSON |
| **SSL Certificates** | Not required | Automatic via Let's Encrypt |

## Environment Configuration

### Development

```bash
ENV=development
SECRET_KEY=any-secret-key-for-dev
SECURE_COOKIES=false
ALLOWED_ORIGINS=
REPO_MODE=memory
DOMAIN=
```

**Characteristics:**
- No HTTPS requirement
- CORS allows localhost by default
- Can use in-memory test data
- Relaxed validation for quick iteration

### Production

```bash
ENV=production
SECRET_KEY=strong-random-32-char-secret
SECURE_COOKIES=true
ALLOWED_ORIGINS=https://yourdomain.com
REPO_MODE=database
DOMAIN=yourdomain.com
```

**Characteristics:**
- HTTPS enforced via Caddy
- CORS strictly validated
- Database required
- Secure cookies required
- Runtime validation prevents misconfigurations

## Network Architecture

### Development

```
┌─────────────────┐
│  Your Browser   │
│  localhost:3000 │
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐      ┌──────────────┐      ┌──────────────┐
│  Caddy          │      │  Backend     │      │  PostgreSQL  │
│  Port 3000      │─────▶│  Port 8000   │─────▶│  Port 5432   │
│  (Docker)       │      │  (Docker)    │      │  (Docker)    │
└─────────────────┘      └──────────────┘      └──────────────┘
```

**Exposed Ports:**
- Frontend: 3000 (Caddy)
- Backend: 8000 (direct access for testing)
- Database: 5432 (optional, for psql access)

### Production

```
┌─────────────────┐
│  Your Browser   │
│  yourdomain.com │
└────────┬────────┘
         │
         │ HTTPS (443)
         ▼
┌─────────────────────────────────────────────┐
│         Caddy Reverse Proxy                 │
│         Port 80 → 443 (HTTPS redirect)      │
│         Port 443 (HTTPS + SSL)              │
└────┬────────────────────────────────────┬───┘
     │                                     │
     │ API requests (/auth/*, /runs/*)    │ Static files
     │                                     │
     ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  Backend     │                    │  React Build │
│  Port 8000   │                    │  /srv        │
│  (internal)  │                    │  (served by  │
└──────┬───────┘                    │   Caddy)     │
       │                            └──────────────┘
       ▼
┌──────────────┐
│  PostgreSQL  │
│  Port 5432   │
│  (internal)  │
└──────────────┘
```

**Exposed Ports:**
- Frontend: 80, 443 (Caddy only)
- Backend: Internal network only
- Database: Internal network only

**Security Benefits:**
- Backend not directly accessible from internet
- Database not accessible from internet
- All traffic encrypted via HTTPS
- Automatic certificate management

## URL Structure

### Development

**Frontend:** `http://localhost:3000`
**Backend API:** `http://localhost:8000`
**WebSocket:** `ws://localhost:8000`

API calls go directly to backend:
```javascript
// Example: Login request
POST http://localhost:8000/auth/login
```

### Production

**Frontend & API:** `https://yourdomain.com`
**WebSocket:** `wss://yourdomain.com`

API calls go through Caddy reverse proxy:
```javascript
// Example: Login request
POST https://yourdomain.com/auth/login
// Caddy proxies to backend:8000/auth/login
```

## CORS Configuration

### Development

**Backend automatically allows:**
- `http://localhost:3000` (Docker frontend)
- `http://localhost:5173` (Vite dev server)

**No configuration needed** - just leave `ALLOWED_ORIGINS` empty.

### Production

**Backend requires explicit configuration:**

```bash
ALLOWED_ORIGINS=https://yourdomain.com
```

**Multiple domains:**
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Application will refuse to start** if `ALLOWED_ORIGINS` is not set in production mode.

## Security Headers

### Development

Minimal security headers for development convenience.

### Production

Caddy adds comprehensive security headers:
- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer
- `Strict-Transport-Security: max-age=31536000` - Forces HTTPS (HSTS)

## Database Configuration

### Development

**Option 1: In-Memory Test Data (Default)**
```bash
REPO_MODE=memory
```
- Pre-populated with test users, groups, stores, products
- No database required
- Data resets on restart
- Perfect for quick iteration

**Option 2: PostgreSQL**
```bash
REPO_MODE=database
DATABASE_URL=postgresql://bulq:password@db:5432/bulq
```
- Persistent data
- Full PostgreSQL features
- Requires database container

### Production

**PostgreSQL Required**
```bash
REPO_MODE=database
DATABASE_URL=postgresql://bulq:strong-password@db:5432/bulq
```
- In-memory mode not allowed
- Database URL required
- Application validates configuration on startup

## Logging

### Development

**Format:** Structured (human-readable)
```
2025-10-14T10:30:45Z level=INFO message="User registered" user_id=abc123 request_id=xyz789
```

**Output:** Console

**Configuration:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=structured
LOG_FILE=
```

### Production

**Format:** JSON (machine-parseable)
```json
{
  "timestamp": "2025-10-14T10:30:45Z",
  "level": "INFO",
  "message": "User registered",
  "user_id": "abc123",
  "request_id": "xyz789"
}
```

**Output:** File and/or log aggregation service

**Configuration:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log
```

## SSL/TLS Certificates

### Development

**Not required** - HTTP is sufficient for local development.

**Optional:** You can test HTTPS locally with self-signed certificates, but not necessary.

### Production

**Automatic via Let's Encrypt:**

1. Set `DOMAIN` environment variable
2. Point DNS A record to server
3. Ensure ports 80/443 are open
4. Caddy automatically provisions certificate
5. Certificate auto-renews before expiry

**No manual certificate management needed!**

## Switching Between Modes

### From Development to Production

1. **Update `.env`:**
   ```bash
   ENV=production
   SECURE_COOKIES=true
   ALLOWED_ORIGINS=https://yourdomain.com
   DOMAIN=yourdomain.com
   REPO_MODE=database
   ```

2. **Generate strong secret:**
   ```bash
   openssl rand -hex 32
   # Update SECRET_KEY in .env
   ```

3. **Rebuild and deploy:**
   ```bash
   docker compose build
   docker compose up -d
   ```

### From Production to Development

1. **Update `.env`:**
   ```bash
   ENV=development
   SECURE_COOKIES=false
   ALLOWED_ORIGINS=
   DOMAIN=
   REPO_MODE=memory
   ```

2. **Rebuild:**
   ```bash
   docker compose down
   docker compose build
   docker compose up -d
   ```

## Testing Production Configuration Locally

You can test production configuration locally using:

1. **Local domain:**
   Add to `/etc/hosts`:
   ```
   127.0.0.1 local.bulq.test
   ```

2. **Update `.env`:**
   ```bash
   ENV=production
   DOMAIN=local.bulq.test
   ALLOWED_ORIGINS=https://local.bulq.test
   SECURE_COOKIES=true
   REPO_MODE=database
   ```

3. **Accept self-signed certificate** in browser

This tests the production configuration without deploying to a real server.

## Common Pitfalls

### ❌ CORS Errors in Production

**Problem:** Frontend can't reach backend

**Cause:** `ALLOWED_ORIGINS` not set or doesn't match domain exactly

**Solution:**
```bash
# Make sure protocol (https://) and domain match exactly
ALLOWED_ORIGINS=https://yourdomain.com
# NOT: http://yourdomain.com (wrong protocol)
# NOT: https://yourdomain.com/ (trailing slash)
```

### ❌ Secure Cookie Errors

**Problem:** "Set-Cookie blocked" in browser console

**Cause:** `SECURE_COOKIES=true` but using HTTP (not HTTPS)

**Solution:**
```bash
# Development: Use HTTP with insecure cookies
SECURE_COOKIES=false

# Production: Use HTTPS with secure cookies
SECURE_COOKIES=true
DOMAIN=yourdomain.com  # This enables HTTPS via Caddy
```

### ❌ Backend Not Accessible in Production

**Problem:** Can't access `http://yourserver.com:8000`

**Cause:** Backend port not exposed in production (by design)

**Solution:** This is correct! Access backend through Caddy:
- ✅ `https://yourdomain.com/auth/login`
- ❌ `https://yourdomain.com:8000/auth/login`

### ❌ WebSocket Connection Failed

**Problem:** WebSocket upgrade failed

**Cause:** Using wrong protocol (ws:// instead of wss://)

**Solution:** In production, use `wss://` for WebSockets. The frontend config handles this automatically based on page protocol.

## Best Practices

1. **Never use production credentials in development**
2. **Never commit `.env` file to version control**
3. **Always test production build locally before deploying**
4. **Use strong secrets in production** (32+ characters)
5. **Enable all production validations** (don't disable for convenience)
6. **Monitor logs after deployment** to catch configuration issues early

## Summary

**Development mode** is optimized for:
- Fast iteration
- Easy debugging
- Minimal configuration
- Flexible testing

**Production mode** is optimized for:
- Security
- Performance
- Reliability
- Compliance

The application enforces these differences through runtime validation, ensuring you can't accidentally deploy an insecure configuration.
