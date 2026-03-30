# Build stage
FROM node:23-alpine AS builder

# Switch to non-root user (node user exists in base image with UID 1000)
USER node

# WORKDIR will be created with node ownership
WORKDIR /app

# Build argument for base path
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# Copy package files
COPY --chown=node:node package*.json ./

# Install dependencies (including dev dependencies for building)
RUN npm ci

# Copy source code with correct ownership
COPY --chown=node:node . .

# Build the application
RUN npm run build

# Production stage
FROM caddy:2-alpine

# Copy built application
COPY --from=builder /app/dist /srv

# Copy Caddy configuration
COPY Caddyfile /etc/caddy/Caddyfile

# Expose port 3000 (dev) or 80 (prod) - controlled by docker-compose
EXPOSE 3000 80

# Caddy will start automatically
