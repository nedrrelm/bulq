// API Configuration
// Production: Use /bulq prefix for subpath deployment at vagolan.com/bulq
// Development: Can use VITE_API_URL to point to backend directly (default: http://localhost:8000)
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '/bulq' : 'http://localhost:8000')

// WebSocket Configuration
// Production: Use /bulq prefix with wss protocol for subpath deployment
// Development: Direct WebSocket connection to backend
export const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  (import.meta.env.PROD ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/bulq` : 'ws://localhost:8000')
