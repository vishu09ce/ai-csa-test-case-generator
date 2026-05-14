import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/ai-csa-test-case-generator/',
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
