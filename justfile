# List all available commands
default:
  @just --list

# ============================================
# MAIN COMMANDS
# ============================================

# Start development environment (supports --build, etc.)
dev *args:
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d {{args}}
  @just links

# Start production environment (supports --build, etc.)
prod *args:
  docker compose -f docker-compose.yml -f deployment/docker-compose.prod.yml --env-file deployment/.env.prod up -d {{args}}
  @just links

# Show application URLs
links:
  #!/usr/bin/env bash
  echo ""
  echo "Application URLs:"
  echo "  Frontend:  http://localhost:1314"
  echo "  API docs:  http://localhost:1314/api/docs"
  echo "  Health:    http://localhost:1314/api/health"
  echo ""

# View logs (works for both dev and prod)
logs service="":
  docker compose logs -f {{service}}

# Stop services (works for both dev and prod)
down:
  docker compose down

# Show service status (works for both dev and prod)
ps:
  docker compose ps

# ============================================
# DEVELOPMENT TOOLS
# ============================================

# Backend linting
lint:
  docker compose exec backend uv run --extra dev ruff format app/
  docker compose exec backend uv run --extra dev ruff check app/ --fix
