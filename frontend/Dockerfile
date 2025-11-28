# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Build argument for base path
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for building)
RUN npm ci

# Copy source code
COPY . .

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
