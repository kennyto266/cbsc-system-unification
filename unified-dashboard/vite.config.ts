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
    // Replace individual process.env.X references (not process.env as object)
    'process.env.NODE_ENV': JSON.stringify('development'),
    'process.env.REACT_APP_API_URL': JSON.stringify('http://localhost:3004'),
    'process.env.REACT_APP_WS_URL': JSON.stringify('ws://localhost:3004/ws'),
    'process.env.REACT_APP_API_TIMEOUT': JSON.stringify('30000'),
    'process.env.REACT_APP_API_VERSION': JSON.stringify('v1'),
    'process.env.REACT_APP_API_RETRY_ATTEMPTS': JSON.stringify('3'),
    'process.env.REACT_APP_API_RETRY_DELAY': JSON.stringify('1000'),
    'process.env.REACT_APP_CACHE_TTL': JSON.stringify('300000'),
    'process.env.REACT_APP_CACHE_MAX_SIZE': JSON.stringify('100'),
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