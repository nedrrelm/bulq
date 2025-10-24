// API Configuration
// Uses BASE_PATH for subpath deployment (e.g., /bulq in production)
// Development: Direct connection to backend
// Production: Proxied through Caddy with BASE_PATH prefix
const BASE_PATH = import.meta.env.VITE_BASE_PATH || '/'

export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? BASE_PATH.replace(/\/$/, '') : 'http://localhost:8000')

// WebSocket Configuration
// Uses BASE_PATH for subpath deployment
// Development: Direct WebSocket connection to backend
// Production: WebSocket through Caddy with BASE_PATH prefix
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  (import.meta.env.PROD
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}${BASE_PATH.replace(/\/$/, '')}`
    : 'ws://localhost:8000')
