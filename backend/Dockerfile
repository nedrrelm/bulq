# ============================================
# Stage: builder — install dependencies with uv
# ============================================
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Build argument to control dev dependencies installation
ARG BUILD_DEV_DEPS=false

# Install dependencies with BuildKit cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$BUILD_DEV_DEPS" = "true" ]; then \
      uv sync --frozen --extra dev; \
    else \
      uv sync --frozen; \
    fi

# ============================================
# Stage: dev — includes uv for development workflow
# ============================================
FROM builder AS dev

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Copy application code (overridden by volume mount in dev)
COPY --chown=appuser:appuser . .

USER appuser

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Use uv run so it can manage .venv when source is volume-mounted
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# Stage: prod — lean image without uv
# ============================================
FROM python:3.14-slim AS prod

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Copy only the virtual environment from builder (no uv binary)
COPY --from=builder /app/.venv .venv/

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Run directly from venv — no uv needed
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
