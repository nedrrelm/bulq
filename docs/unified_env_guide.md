# Unified Environment Configuration Guide

This guide explains how to set up a single `.env` file that automatically switches between development and production configurations based on a single `ENV` variable.

## The Problem

Traditionally, you need separate `.env.development` and `.env.production` files, and you have to manually copy values or switch files when deploying. This is error-prone and tedious.

## The Solution

Use bash parameter expansion **inside the `.env` file** to automatically select dev or prod values based on an `ENV` variable.

## How It Works

### 1. Structure

```bash
# Set the environment
ENV=development  # or "production"

# Define dev-specific values
DEV_SECRET_KEY=dev-secret
DEV_POSTGRES_PASSWORD=dev-password
DEV_FRONTEND_PORT=3000

# Define prod-specific values
PROD_SECRET_KEY=prod-secret-generated-key
PROD_POSTGRES_PASSWORD=strong-prod-password
PROD_FRONTEND_PORT=8080

# Auto-select based on ENV
PROD=${ENV:+${ENV}}
PROD=${PROD/development/}

SECRET_KEY=${PROD:+${PROD_SECRET_KEY}}
SECRET_KEY=${SECRET_KEY:-${DEV_SECRET_KEY}}

POSTGRES_PASSWORD=${PROD:+${PROD_POSTGRES_PASSWORD}}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-${DEV_POSTGRES_PASSWORD}}

FRONTEND_PORT=${PROD:+${PROD_FRONTEND_PORT}}
FRONTEND_PORT=${FRONTEND_PORT:-${DEV_FRONTEND_PORT}}
```

### 2. The Magic Lines

These two lines create a conditional flag:

```bash
PROD=${ENV:+${ENV}}           # If ENV is set, PROD=ENV value
PROD=${PROD/development/}     # If PROD="development", clear it (PROD="")
```

**Result:**
- If `ENV=production` → `PROD="production"` (truthy)
- If `ENV=development` → `PROD=""` (empty/falsy)

### 3. The Conditional Pattern

For each variable, use this two-line pattern:

```bash
VARIABLE_NAME=${PROD:+${PROD_VARIABLE_NAME}}      # If PROD is set, use PROD_*
VARIABLE_NAME=${VARIABLE_NAME:-${DEV_VARIABLE_NAME}}  # Otherwise, use DEV_*
```

**How it works:**
- `${PROD:+${PROD_VARIABLE_NAME}}` → If PROD is set (production), expand to PROD_VARIABLE_NAME
- `${VARIABLE_NAME:-${DEV_VARIABLE_NAME}}` → If VARIABLE_NAME is empty, use DEV_VARIABLE_NAME as default

## Step-by-Step Implementation

### 1. Create `.env.example`

```bash
# ============================================
# ENVIRONMENT SELECTOR
# ============================================
ENV=development

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
PROD=${ENV:+${ENV}}
PROD=${PROD/development/}

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

In `docker-compose.yml`, just reference the final variable names directly:

```yaml
services:
  backend:
    env_file:
      - .env
    ports:
      - "${BACKEND_PORT:-}:8000"  # No interpolation needed!

  frontend:
    env_file:
      - .env
    ports:
      - "${FRONTEND_PORT}:${CADDY_PORT}"
```

**Important:** All interpolation happens in `.env`, NOT in `docker-compose.yml`.

### 3. Usage

**Development:**
```bash
cp .env.example .env
# ENV=development (already default)
docker compose up
```

**Production:**
```bash
cp .env.example .env
# Edit .env:
# 1. Set ENV=production
# 2. Update PROD_SECRET_KEY and PROD_POSTGRES_PASSWORD
docker compose up -d
```

## Testing

Verify the configuration works:

```bash
# Test development
source .env && echo "ENV=$ENV, PASSWORD=$POSTGRES_PASSWORD, PORT=$FRONTEND_PORT"
# Output: ENV=development, PASSWORD=dev-pass, PORT=3000

# Test production (temporarily)
sed 's/ENV=development/ENV=production/' .env > /tmp/test.env
source /tmp/test.env && echo "ENV=$ENV, PASSWORD=$POSTGRES_PASSWORD, PORT=$FRONTEND_PORT"
# Output: ENV=production, PASSWORD=REPLACE_WITH_STRONG_PASSWORD, PORT=8080
```

## Key Benefits

✅ **Single source of truth** - One `.env` file for all environments
✅ **Automatic switching** - Change one variable, everything updates
✅ **No duplication** - Dev and prod values clearly separated
✅ **Git-friendly** - `.env.example` in repo, `.env` gitignored
✅ **Docker Compose compatible** - Works with standard docker compose

## Common Pitfalls

❌ **Don't use bash substitution in docker-compose.yml**
```yaml
# Wrong - Docker Compose doesn't support this
environment:
  - PASSWORD=${ENV:+${PROD_PASSWORD}}
```

✅ **Do use bash substitution in .env**
```bash
# Correct - .env file supports bash expansion
PASSWORD=${PROD:+${PROD_PASSWORD}}
PASSWORD=${PASSWORD:-${DEV_PASSWORD}}
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
2. **Create** the `PROD` flag from `ENV`
3. **Apply** the two-line conditional pattern to each variable
4. **Switch** environments by changing `ENV` only

That's it! One variable change switches your entire configuration.
