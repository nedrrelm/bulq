# ============================================
# Stage: base - Common dependencies
# ============================================
FROM node:23-alpine AS base

# Switch to non-root user (node user exists in base image)
USER node

WORKDIR /app

# Copy package files
COPY --chown=node:node package*.json ./

# Install all dependencies (includes dev dependencies)
RUN npm ci

# ============================================
# Stage: dev - Development with Vite dev server
# ============================================
FROM base AS dev

# Copy source code
COPY --chown=node:node . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server
CMD ["npm", "run", "dev"]

# ============================================
# Stage: builder - Build production artifacts
# ============================================
FROM base AS builder

# Build argument for base path
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# Copy source code
COPY --chown=node:node . .

# Build the application
RUN npm run build

# Output: /app/dist

# ============================================
# Stage: prod - Production (minimal image with built files)
# ============================================
FROM alpine:latest AS prod

# Create directory for static files
WORKDIR /srv

# Copy built files from builder stage
COPY --from=builder /app/dist .

# This container exists to provide built files via volume to Caddy
# It doesn't need to do anything, just maintain the volume
CMD ["sleep", "infinity"]
