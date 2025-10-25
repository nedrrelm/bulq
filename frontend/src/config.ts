// API Configuration
// Development: Direct connection to backend at localhost:8000
// Production: Proxied through Caddy (relative URLs)
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '' : 'http://localhost:8000')

// WebSocket Configuration
// Development: Direct WebSocket connection to backend at localhost:8000
// Production: WebSocket through Caddy using current domain
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  (import.meta.env.PROD
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost:8000')
