FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Build argument to control dev dependencies installation
ARG BUILD_DEV_DEPS=false

# Install dependencies (conditionally include dev dependencies)
RUN if [ "$BUILD_DEV_DEPS" = "true" ]; then \
      uv sync --frozen --no-cache --dev; \
    else \
      uv sync --frozen --no-cache; \
    fi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
