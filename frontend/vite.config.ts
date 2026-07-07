import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    // The browser only ever talks to this origin; /api is proxied to the
    // backend server-side. That makes `ngrok http 5173` a complete share of
    // the demo - one tunnel, no CORS, no VITE_BACKEND_URL override needed.
    proxy: {
      '/api': 'http://localhost:8000',
    },
    // Vite rejects requests whose Host header it doesn't know; allow ngrok's.
    allowedHosts: ['.ngrok-free.app', '.ngrok.app', '.ngrok.dev', '.ngrok.io'],
  },
});
