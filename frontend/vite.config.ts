import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8008',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://127.0.0.1:8008',
        ws: true,
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8008',
        changeOrigin: true,
      },
    },
  },
})
