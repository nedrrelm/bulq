import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Base path is passed via --base flag in package.json build script
// This allows it to be set from VITE_BASE_PATH environment variable
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  },
  build: {
    sourcemap: true  // Enable source maps for production debugging
  }
})
