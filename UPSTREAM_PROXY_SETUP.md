# Upstream Reverse Proxy Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Internet Users                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ vagolan.com (Upstream Reverse Proxy Server)                │
│ - Handles SSL/TLS certificates                             │
│ - Serves multiple apps on different paths                  │
│ - Routes /bulq/* to Bulq app server                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
                            │ Forwards to port 8080
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Bulq App Server (This Machine)                             │
│ - Receives HTTP traffic on port 8080                       │
│ - Docker Compose stack:                                    │
│   ├─ Caddy (frontend proxy)                                │
│   ├─ FastAPI Backend                                       │
│   └─ PostgreSQL Database                                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Configuration Points

### 1. Path Rewriting

The upstream proxy **MUST strip the `/bulq` prefix** when forwarding requests.

**Why?**
- Frontend is built with `/bulq` base path for browser asset loading
- But the app server serves content at root path
- Upstream proxy removes `/bulq` before forwarding

**Example:**
```
User requests:       https://vagolan.com/bulq/auth/me
Upstream receives:   /bulq/auth/me
Upstream forwards:   /auth/me          ← /bulq stripped!
App receives:        /auth/me
App responds with:   User data
```

### 2. Trailing Slashes Matter

**Nginx example:**
```nginx
# ✅ CORRECT - Both have trailing slashes
location /bulq/ {
    proxy_pass http://bulq-server:8080/;
}

# ❌ WRONG - Missing trailing slash on proxy_pass
location /bulq/ {
    proxy_pass http://bulq-server:8080;  # Will forward to /bulq/auth/me
}
```

### 3. WebSocket Support Required

The app uses WebSockets for real-time updates. The upstream proxy must support:
- HTTP/1.1 protocol
- Connection upgrade headers
- WebSocket protocol

## Complete Configuration Examples

### Nginx

```nginx
# /etc/nginx/sites-available/vagolan.com

upstream bulq_backend {
    server bulq-server:8080;  # Replace with actual server IP/hostname
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name vagolan.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Other apps and routes...

    # Bulq app
    location /bulq/ {
        proxy_pass http://bulq_backend/;

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long-running connections
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering settings
        proxy_buffering off;
        proxy_redirect off;
    }
}
```

### Caddy

```
vagolan.com {
    # TLS configuration (automatic with Caddy)

    # Other routes...

    # Bulq app
    handle /bulq/* {
        uri strip_prefix /bulq
        reverse_proxy bulq-server:8080 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

### Apache

```apache
<VirtualHost *:443>
    ServerName vagolan.com

    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem

    # Other routes...

    # Bulq app
    <Location /bulq>
        ProxyPass http://bulq-server:8080/
        ProxyPassReverse http://bulq-server:8080/
        ProxyPreserveHost On

        # Standard headers
        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Port "443"

        # WebSocket support
        RewriteEngine On
        RewriteCond %{HTTP:Upgrade} websocket [NC]
        RewriteCond %{HTTP:Connection} upgrade [NC]
        RewriteRule /(.*) ws://bulq-server:8080/$1 [P,L]
    </Location>
</VirtualHost>
```

## Testing the Configuration

### 1. Test App Server Locally

From the Bulq app server:
```bash
# Should return HTML
curl http://localhost:8080

# Should return 401 (not authenticated)
curl http://localhost:8080/auth/me
```

### 2. Test from Upstream Proxy Server

From the vagolan.com server:
```bash
# Should return HTML
curl http://bulq-server:8080

# Should return 401
curl http://bulq-server:8080/auth/me
```

### 3. Test from Internet

From any machine:
```bash
# Should return HTML
curl https://vagolan.com/bulq

# Should return 401
curl https://vagolan.com/bulq/auth/me

# Test asset loading
curl https://vagolan.com/bulq/assets/index-XXXXX.js
```

### 4. Test WebSocket

Using browser console at `https://vagolan.com/bulq`:
```javascript
const ws = new WebSocket('wss://vagolan.com/bulq/ws/test');
ws.onopen = () => console.log('Connected!');
ws.onerror = (e) => console.error('WebSocket error:', e);
```

## Common Issues

### Issue: Assets Not Loading (404 errors)

**Symptoms:**
- Browser shows 404 for `/assets/index-XXXXX.js`
- Console errors about missing JavaScript/CSS files

**Causes:**
- Upstream proxy not stripping `/bulq` prefix
- Missing trailing slash in proxy configuration

**Fix:**
```nginx
# Ensure trailing slashes
location /bulq/ {
    proxy_pass http://bulq-server:8080/;  # ← trailing slash here!
}
```

### Issue: API Calls Failing

**Symptoms:**
- Login doesn't work
- API returns 404 or CORS errors

**Causes:**
- Path not being rewritten correctly
- CORS headers not preserved

**Fix:**
```nginx
location /bulq/ {
    proxy_pass http://bulq-server:8080/;
    proxy_set_header Host $host;  # ← preserve Host header
}
```

### Issue: WebSocket Connection Failed

**Symptoms:**
- Real-time updates don't work
- Browser console shows WebSocket connection errors

**Causes:**
- Missing WebSocket upgrade headers
- HTTP/1.0 instead of HTTP/1.1

**Fix:**
```nginx
location /bulq/ {
    proxy_http_version 1.1;                        # ← HTTP/1.1
    proxy_set_header Upgrade $http_upgrade;        # ← Upgrade header
    proxy_set_header Connection "upgrade";         # ← Connection header
    proxy_pass http://bulq-server:8080/;
}
```

### Issue: Infinite Redirects or Mixed Content

**Symptoms:**
- Browser gets stuck in redirect loop
- Console shows "Mixed Content" warnings

**Causes:**
- App doesn't know it's behind HTTPS
- Missing X-Forwarded-Proto header

**Fix:**
```nginx
location /bulq/ {
    proxy_set_header X-Forwarded-Proto $scheme;  # ← tells app about HTTPS
    proxy_pass http://bulq-server:8080/;
}
```

## Security Considerations

### 1. Network Isolation

**Recommended:**
```
┌─────────────┐
│  Internet   │
└──────┬──────┘
       │ HTTPS (443)
       ▼
┌─────────────┐
│  Upstream   │  Private network
│   Proxy     ├──────────────┐
└─────────────┘              │ HTTP (8080)
                             ▼
                    ┌─────────────┐
                    │  Bulq App   │
                    └─────────────┘
```

**Firewall rules on Bulq app server:**
- Allow 8080 from upstream proxy IP only
- Block 8080 from internet
- Block database port (5432) from everywhere except localhost

### 2. Headers to Forward

**Essential:**
- `Host` - Preserves original host for CORS
- `X-Forwarded-Proto` - Tells app about HTTPS
- `X-Forwarded-For` - Original client IP for logging
- `X-Real-IP` - Original client IP

**Optional but recommended:**
- `X-Forwarded-Host` - Original hostname
- `X-Forwarded-Port` - Original port

### 3. Rate Limiting

Apply rate limiting at the upstream proxy level:

```nginx
# Nginx example
limit_req_zone $binary_remote_addr zone=bulq_login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=bulq_api:10m rate=100r/m;

location /bulq/auth/login {
    limit_req zone=bulq_login burst=3 nodelay;
    proxy_pass http://bulq-server:8080/auth/login;
}

location /bulq/ {
    limit_req zone=bulq_api burst=20 nodelay;
    proxy_pass http://bulq-server:8080/;
}
```

## Monitoring

### Check Upstream Proxy Logs

**Nginx:**
```bash
tail -f /var/log/nginx/access.log | grep /bulq
tail -f /var/log/nginx/error.log
```

**Caddy:**
```bash
journalctl -u caddy -f
```

### Check App Server

```bash
# On Bulq app server
docker compose logs -f frontend
docker compose logs -f backend

# Check connections
netstat -an | grep :8080
```

### Monitor Traffic

```bash
# On upstream proxy
tcpdump -i any -n port 8080

# On app server
tcpdump -i any -n port 8080
```

## Summary Checklist

Before going live, verify:

- [ ] Upstream proxy strips `/bulq` prefix (trailing slashes correct)
- [ ] WebSocket upgrade headers configured
- [ ] X-Forwarded-* headers set correctly
- [ ] HTTPS configured on upstream proxy
- [ ] Firewall allows 8080 from upstream proxy only
- [ ] Tested: `curl https://vagolan.com/bulq` returns HTML
- [ ] Tested: Assets load correctly in browser
- [ ] Tested: API calls work (`/bulq/auth/*`)
- [ ] Tested: WebSocket connects successfully
- [ ] Monitoring and logging configured

## Need Help?

Common test commands:
```bash
# From app server
curl http://localhost:8080
docker compose logs -f

# From upstream proxy server
curl http://bulq-server:8080

# From internet
curl https://vagolan.com/bulq
curl https://vagolan.com/bulq/auth/me
```

If issues persist, check:
1. Upstream proxy configuration (path rewriting)
2. Firewall rules (port 8080 accessible?)
3. App server logs (`docker compose logs`)
4. Network connectivity between servers
