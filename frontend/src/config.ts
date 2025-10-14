// API Configuration
// Production: Use relative URLs (Caddy reverse proxy handles routing)
// Development: Can use VITE_API_URL to point to backend directly (default: http://localhost:8000)
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '' : 'http://localhost:8000')

// WebSocket Configuration
// Production: Use relative URL (Caddy reverse proxy handles routing)
// Development: Direct WebSocket connection to backend
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  (import.meta.env.PROD ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}` : 'ws://localhost:8000')
