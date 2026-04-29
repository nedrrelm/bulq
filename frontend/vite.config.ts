import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Base path is passed via --base flag in package.json build script
// This allows it to be set from VITE_BASE_PATH environment variable
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Listen on all interfaces for Docker
    port: 5173,
    strictPort: true,  // Fail if port is already in use
    // HMR configuration for Docker + Caddy proxy
    hmr: {
      // Use the same host/port - Caddy will proxy WebSocket connections
      clientPort: parseInt(process.env.CADDY_PORT || '1314')  // Port exposed by Caddy to browser
    }
  },
  build: {
    sourcemap: false
  }
})
