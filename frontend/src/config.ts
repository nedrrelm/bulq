// API Configuration
// All requests go through Caddy reverse proxy (localhost:1314 in dev, production domain in prod)
// Using relative URLs ensures requests go to same origin (Caddy), which proxies to backend
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// WebSocket Configuration
// WebSocket connections also go through Caddy reverse proxy
// Use current page protocol/host to construct WebSocket URL
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api`
