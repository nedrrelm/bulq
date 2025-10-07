// API Configuration
// Default to localhost for development, override with VITE_API_URL environment variable
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// WebSocket Configuration
// Convert HTTP URL to WebSocket URL
const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws'
const wsHost = API_BASE_URL.replace(/^https?:\/\//, '')
export const WS_BASE_URL = `${wsProtocol}://${wsHost}`
