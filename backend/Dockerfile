FROM python:3.14-slim

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Switch to non-root user
USER appuser

# WORKDIR will be created with appuser ownership
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files with correct ownership
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Switch to non-root user after files are copied with correct ownership
USER appuser

# Build argument to control dev dependencies installation
ARG BUILD_DEV_DEPS=false

# Install dependencies (conditionally include dev dependencies)
RUN if [ "$BUILD_DEV_DEPS" = "true" ]; then \
      uv sync --frozen --no-cache --extra dev; \
    else \
      uv sync --frozen --no-cache; \
    fi

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
