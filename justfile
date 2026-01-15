# List all available commands
default:
  @just --list

# Docker operations
up:
  docker compose up -d

restart service="":
  docker compose restart {{service}}

logs service="":
  docker compose logs -f {{service}}

dps:
  docker compose ps

# Frontend
build:
  docker compose exec frontend npm run build

# Backend linting
lint:
  docker compose exec backend uv run --extra dev ruff format app/
  docker compose exec backend uv run --extra dev ruff check app/ --fix
