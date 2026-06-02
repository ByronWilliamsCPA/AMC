import path from 'node:path'
import react from '@vitejs/plugin-react-swc'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Dev-only: proxy same-origin /api and /health to the backend so the
      // browser sees one origin (matching the production reverse proxy) and the
      // session cookie is sent. The app itself always calls relative '/api'.
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    // Hidden source maps: generated for Sentry upload but not referenced from
    // the served bundles, so source isn't exposed to clients.
    sourcemap: 'hidden',
  },
})
