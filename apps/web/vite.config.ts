import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/bootstrap': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/login': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/orchestrate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/memory': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/finance': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/files': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/camera': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/me': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/openapi.json': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts'
  }
});
