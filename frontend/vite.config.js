import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/echarts') || id.includes('node_modules/zrender')) return 'charts'
          if (id.includes('node_modules/vue') || id.includes('node_modules/@vue')) return 'vue'
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // In development, forward /api to Flask; same-origin from the browser's perspective, so no CORS needed
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
