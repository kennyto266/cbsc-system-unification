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
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3004',
        changeOrigin: true,
        secure: false,
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
          ui: ['antd', '@ant-design/plots'],
          charts: ['chart.js', 'react-chartjs-2', 'recharts'],
        },
        // Optimize chunk size
        maxParallelFileOps: 5,
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