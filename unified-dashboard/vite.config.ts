import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // VitePWA disabled (personal use, causes stale cache issues)
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@store': path.resolve(__dirname, './src/store'),
      '@styles': path.resolve(__dirname, './src/styles')
    }
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3003',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://localhost:3003',
        ws: true,
        changeOrigin: true
      }
    }
  },
  define: {
    // Polyfill process.env for browser (legacy CRA-style code uses process.env)
    'process.env': JSON.stringify({
      NODE_ENV: 'development',
      REACT_APP_API_URL: 'http://localhost:3004',
      REACT_APP_WS_URL: 'ws://localhost:3004/ws',
    }),
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'esnext',
    chunkSizeWarningLimit: 2000,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', 'chart.js', 'recharts']
  }
})