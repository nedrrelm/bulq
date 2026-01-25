# List all available commands
default:
  @just --list

# ============================================
# MAIN COMMANDS
# ============================================

# Start development environment (supports --build, etc.)
dev *args:
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d {{args}}
  @echo "\nDevelopment running at: http://localhost:1314"

# Start production environment (supports --build, etc.)
prod *args:
  docker compose -f docker-compose.yml -f deployment/docker-compose.prod.yml --env-file deployment/.env.prod up -d {{args}}
  @echo "\nProduction running"

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
