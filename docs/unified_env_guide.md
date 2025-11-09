# Unified Environment Configuration Guide

This guide explains how to set up a single `.env` file that automatically switches between development and production configurations based on simple flag variables.

## The Problem

Traditionally, you need separate `.env.development` and `.env.production` files, and you have to manually copy values or switch files when deploying. This is error-prone and tedious.

## The Solution

Use bash parameter expansion **inside the `.env` file** to automatically select dev or prod values based on `DEV` and `PROD` flags.

## How It Works

### 1. Structure

```bash
# Set ONE flag (leave the other empty)
DEV=true
PROD=

# Define dev-specific values
DEV_SECRET_KEY=dev-secret
DEV_POSTGRES_PASSWORD=dev-password
DEV_FRONTEND_PORT=3000

# Define prod-specific values
PROD_SECRET_KEY=prod-secret-generated-key
PROD_POSTGRES_PASSWORD=strong-prod-password
PROD_FRONTEND_PORT=8080

# Derived ENV variable
ENV=${PROD:+production}
ENV=${ENV:-development}

# Auto-select based on PROD flag
SECRET_KEY=${PROD:+${PROD_SECRET_KEY}}
SECRET_KEY=${SECRET_KEY:-${DEV_SECRET_KEY}}

POSTGRES_PASSWORD=${PROD:+${PROD_POSTGRES_PASSWORD}}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-${DEV_POSTGRES_PASSWORD}}

FRONTEND_PORT=${PROD:+${PROD_FRONTEND_PORT}}
FRONTEND_PORT=${FRONTEND_PORT:-${DEV_FRONTEND_PORT}}
```

### 2. The Flag System

Instead of using a single `ENV` variable, we use two flags:

```bash
# Development mode
DEV=true
PROD=

# Production mode
DEV=
PROD=true
```

The `ENV` variable is automatically derived:
```bash
ENV=${PROD:+production}    # If PROD is set, ENV=production
ENV=${ENV:-development}     # Otherwise, ENV=development
```

**Result:**
- If `PROD=true` → `ENV=production` (uses PROD_* values)
- If `PROD=` (empty) → `ENV=development` (uses DEV_* values)

### 3. The Conditional Pattern

For each variable, use this two-line pattern:

```bash
VARIABLE_NAME=${PROD:+${PROD_VARIABLE_NAME}}           # If PROD is set, use PROD_*
VARIABLE_NAME=${VARIABLE_NAME:-${DEV_VARIABLE_NAME}}   # Otherwise, use DEV_*
```

**How it works:**
- `${PROD:+${PROD_VARIABLE_NAME}}` → If PROD is set (not empty), expand to PROD_VARIABLE_NAME value
- `${VARIABLE_NAME:-${DEV_VARIABLE_NAME}}` → If VARIABLE_NAME is still empty, use DEV_VARIABLE_NAME as default

**Example execution:**
```bash
# In development (PROD="")
POSTGRES_PASSWORD=${PROD:+${PROD_POSTGRES_PASSWORD}}  # PROD is empty, so this expands to ""
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bulq_dev_pass}  # POSTGRES_PASSWORD is empty, so use bulq_dev_pass
# Result: POSTGRES_PASSWORD=bulq_dev_pass

# In production (PROD=true)
POSTGRES_PASSWORD=${PROD:+${PROD_POSTGRES_PASSWORD}}  # PROD is set, so expand to value of PROD_POSTGRES_PASSWORD
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bulq_dev_pass}  # POSTGRES_PASSWORD already set, skip this
# Result: POSTGRES_PASSWORD=<value of PROD_POSTGRES_PASSWORD>
```

## Step-by-Step Implementation

### 1. Create `.env.example`

```bash
# ============================================
# ENVIRONMENT SELECTOR
# ============================================
# Set ONE of these to "true" (leave the other empty)
DEV=true
PROD=

# Derived ENV variable
ENV=${PROD:+production}
ENV=${ENV:-development}

# ============================================
# DEVELOPMENT VALUES
# ============================================
DEV_SECRET_KEY=dev-secret-key
DEV_POSTGRES_PASSWORD=dev-pass
DEV_REPO_MODE=memory
DEV_FRONTEND_PORT=3000
DEV_BACKEND_PORT=8000
# ... all dev values

# ============================================
# PRODUCTION VALUES
# ============================================
PROD_SECRET_KEY=REPLACE_WITH_GENERATED_KEY
PROD_POSTGRES_PASSWORD=REPLACE_WITH_STRONG_PASSWORD
PROD_REPO_MODE=database
PROD_FRONTEND_PORT=8080
PROD_BACKEND_PORT=
# ... all prod values

# ============================================
# AUTO-SELECTED VARIABLES
# ============================================
SECRET_KEY=${PROD:+${PROD_SECRET_KEY}}
SECRET_KEY=${SECRET_KEY:-${DEV_SECRET_KEY}}

POSTGRES_PASSWORD=${PROD:+${PROD_POSTGRES_PASSWORD}}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-${DEV_POSTGRES_PASSWORD}}

REPO_MODE=${PROD:+${PROD_REPO_MODE}}
REPO_MODE=${REPO_MODE:-${DEV_REPO_MODE}}

FRONTEND_PORT=${PROD:+${PROD_FRONTEND_PORT}}
FRONTEND_PORT=${FRONTEND_PORT:-${DEV_FRONTEND_PORT}}

BACKEND_PORT=${PROD:+${PROD_BACKEND_PORT}}
BACKEND_PORT=${BACKEND_PORT:-${DEV_BACKEND_PORT}}
# ... repeat for all variables
```

### 2. Use in Docker Compose

In `docker-compose.yml`, just reference the final variable names directly (no defaults, no interpolation):

```yaml
services:
  backend:
    env_file:
      - .env
    ports:
      - "${BACKEND_PORT}:8000"  # No defaults needed - .env handles everything

  frontend:
    env_file:
      - .env
    ports:
      - "${FRONTEND_PORT}:${CADDY_PORT}"
```

**Important:**
- All interpolation happens in `.env`, NOT in `docker-compose.yml`
- Don't use defaults like `${VAR:-default}` in docker-compose.yml - let `.env` handle it
- Every variable used by docker-compose must have a value in `.env` (either DEV or PROD)

### 3. Usage

**Development:**
```bash
cp .env.example .env
# DEV=true, PROD= (already default)
docker compose up
```

**Production:**
```bash
cp .env.example .env
# Edit .env:
# 1. Update PROD_SECRET_KEY and PROD_POSTGRES_PASSWORD
# 2. Set PROD=true and DEV=
docker compose up -d
```

## Testing

Verify the configuration works:

```bash
# Test development
source .env && echo "ENV=$ENV, PASSWORD=$POSTGRES_PASSWORD, PORT=$FRONTEND_PORT"
# Output: ENV=development, PASSWORD=dev-pass, PORT=3000

# Test with docker-compose
docker compose config | grep -E "POSTGRES_PASSWORD|FRONTEND_PORT|ENV"
# Should show development values
```

## Key Benefits

✅ **Single source of truth** - One `.env` file for all environments
✅ **Automatic switching** - Change one variable, everything updates
✅ **No duplication** - Dev and prod values clearly separated
✅ **Git-friendly** - `.env.example` in repo, `.env` gitignored
✅ **Docker Compose compatible** - Works with standard docker compose

## Common Pitfalls

❌ **Don't use interpolation or defaults in docker-compose.yml**
```yaml
# Wrong - Docker Compose should just read variables
environment:
  - PASSWORD=${POSTGRES_PASSWORD:-default}
ports:
  - "${BACKEND_PORT:-8000}:8000"
```

✅ **Do all interpolation in .env**
```yaml
# Correct - docker-compose.yml just references variables
environment:
  - PASSWORD=${POSTGRES_PASSWORD}
ports:
  - "${BACKEND_PORT}:8000"
```

❌ **Don't use string substitution (unsupported by docker-compose)**
```bash
# Wrong - Docker Compose can't parse this
PROD=${ENV:+${ENV}}
PROD=${PROD/development/}  # String substitution not supported
```

✅ **Use simple flag variables**
```bash
# Correct - Works with docker-compose
DEV=true
PROD=
ENV=${PROD:+production}
ENV=${ENV:-development}
```

❌ **Don't forget the two-line pattern**
```bash
# Wrong - only sets if PROD is set, no fallback
PASSWORD=${PROD:+${PROD_PASSWORD}}
```

✅ **Always use both lines**
```bash
# Correct - sets PROD value if available, otherwise DEV
PASSWORD=${PROD:+${PROD_PASSWORD}}
PASSWORD=${PASSWORD:-${DEV_PASSWORD}}
```

## Summary

The pattern is simple:

1. **Define** both `DEV_*` and `PROD_*` prefixed values
2. **Set** either `DEV=true` or `PROD=true` (leave the other empty)
3. **Derive** `ENV` variable from `PROD` flag
4. **Apply** the two-line conditional pattern to each variable
5. **Switch** environments by changing `DEV`/`PROD` flags only

That's it! Change two flags and your entire configuration switches between dev and prod.
