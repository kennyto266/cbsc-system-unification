import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// 簡化的Vite配置，專注於穩定性
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
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // 禁用sourcemap以簡化構建
    minify: 'esbuild', // 使用更快的esbuild
    rollupOptions: {
      // 禁用代碼分割以避免chunks問題
      output: {
        manualChunks: undefined,
      },
    },
  },
  optimizeDeps: {
    // 優化預構建
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@reduxjs/toolkit',
      'react-redux'
    ],
  },
})