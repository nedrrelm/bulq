// API Configuration
// Development: Direct connection to backend at localhost:8000/api
// Production: Proxied through Caddy (relative URLs with /api prefix)
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api')

// WebSocket Configuration
// Development: Direct WebSocket connection to backend at localhost:8000/api
// Production: WebSocket through Caddy using current domain with /api prefix
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  (import.meta.env.PROD
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api`
    : 'ws://localhost:8000/api')
