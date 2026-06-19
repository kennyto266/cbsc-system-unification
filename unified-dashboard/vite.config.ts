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
    rollupOptions: {
      output: {
        manualChunks: {
          // 核心框架
          vendor: ['react', 'react-dom'],
          // UI 库
          ui: ['@radix-ui/react-slot', '@radix-ui/react-icons', 'class-variance-authority', 'clsx', 'tailwind-merge'],
          // Square-UI components
          'square-ui': ['lucide-react', 'framer-motion'],
          // 图表库
          charts: ['chart.js', 'react-chartjs-2', 'recharts', 'plotly.js', 'react-plotly.js'],
          // 工具库
          utils: ['lodash', 'dayjs', 'axios'],
          // 状态管理
          state: ['@reduxjs/toolkit', 'react-redux', 'react-query', 'zustand'],
          // 路由
          router: ['react-router-dom'],
          // 表单
          forms: ['react-hook-form'],
          // 样式和动画
          styles: ['framer-motion', 'clsx', 'class-variance-authority', 'tailwind-merge'],
        },
        // 资源文件名优化
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          let extType = info[info.length - 1] || ''
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name || '')) {
            extType = 'media'
          } else if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetInfo.name || '')) {
            extType = 'images'
          } else if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || '')) {
            extType = 'fonts'
          }
          return `${extType}/[name]-[hash].[ext]`
        },
      },
    },
    // 压缩优化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log'],
      },
    },
    // 代码分割优化
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', 'chart.js', 'recharts']
  }
})