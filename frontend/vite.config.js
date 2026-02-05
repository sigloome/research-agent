/* global process */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 18001,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${process.env.BACKEND_PORT || 18000}`,
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
