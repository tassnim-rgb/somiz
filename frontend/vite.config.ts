import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev proxy: the dashboard talks to the SIMULATED backend on :8000.
// Same-origin /api and /health calls work in dev and in the built app
// (which is served behind the backend's CORS anyway).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})