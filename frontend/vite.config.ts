import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    // En Docker sobre Windows o macOS los cambios del volumen no llegan como eventos:
    // el compose activa el sondeo para que la recarga en caliente funcione.
    watch: process.env.VITE_SONDEO ? { usePolling: true, interval: 300 } : undefined,
    // El panel llama al backend por /api; en produccion lo sirve el mismo dominio.
    // En Docker Compose la API es otro contenedor: VITE_API_PROXY=http://api:8000.
    proxy: {
      '/api': { target: process.env.VITE_API_PROXY ?? 'http://localhost:8000', changeOrigin: true },
    },
  },
})
