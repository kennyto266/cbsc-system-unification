import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    'process.env.REACT_APP_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:3007'),
    'process.env.REACT_APP_WS_URL': JSON.stringify(process.env.VITE_WS_URL || 'ws://localhost:3007/ws'),
    'process.env.REACT_APP_WEBSOCKET_URL': JSON.stringify(process.env.VITE_WEBSOCKET_URL || 'ws://localhost:3007/ws'),
    'process.env': JSON.stringify({
      NODE_ENV: process.env.NODE_ENV || 'development',
      REACT_APP_API_URL: process.env.VITE_API_URL || 'http://localhost:3007',
      REACT_APP_WS_URL: process.env.VITE_WS_URL || 'ws://localhost:3007/ws',
      REACT_APP_WEBSOCKET_URL: process.env.VITE_WEBSOCKET_URL || 'ws://localhost:3007/ws',
    }),
    global: 'globalThis',
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://127.0.0.1:3007',
        ws: true,
        changeOrigin: true,
      },
    },
    // Optimize server for memory usage
    hmr: {
      overlay: false,
    },
    watch: {
      usePolling: false,
      interval: 1000,
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Enable memory optimization
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
          ui: ['antd'],
          charts: ['chart.js', 'react-chartjs-2', 'recharts', 'plotly.js', 'react-plotly.js'],
        },
      },
    },
    // Reduce memory usage during build
    chunkSizeWarningLimit: 1000,
    assetsInlineLimit: 4096,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', '@reduxjs/toolkit', 'react-redux'],
    // Force optimization to reduce runtime memory
    force: true,
  },
  // Experimental features for memory optimization
  experimental: {
    renderBuiltUrl: (filename, { hostType }) => {
      if (hostType === 'js') {
        return { js: `/${filename}` }
      } else {
        return { relative: true }
      }
    },
  },
  esbuild: {
    // Reduce memory usage during esbuild
    drop: ['console', 'debugger'],
  },
})
