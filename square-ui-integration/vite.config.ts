import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'
import { VitePWA } from 'vite-plugin-pwa'
import checker from 'vite-plugin-checker'
import bundleAnalyzer from 'vite-bundle-analyzer'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  const isAnalyze = mode === 'analyze'

  return {
    plugins: [
      react({
        devTarget: 'modern',
      }),
      checker({
        typescript: true,
        eslint: {
          lintCommand: 'eslint . --ext ts,tsx',
        },
      }),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
        manifest: {
          name: 'CBSC Square UI Dashboard',
          short_name: 'CBSC',
          description: 'CBSC量化交易策略管理系统',
          theme_color: '#0f172a',
          background_color: '#0f172a',
          display: 'standalone',
          icons: [
            {
              src: 'pwa-192x192.png',
              sizes: '192x192',
              type: 'image/png',
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any maskable',
            },
          ],
        },
      }),
      isAnalyze && bundleAnalyzer({
        analyzerMode: 'static',
        openAnalyzer: true,
        reportFilename: 'bundle-analysis.html',
        defaultSizes: 'parsed',
        generateStatsFile: true,
        statsFilename: 'bundle-stats.json',
        excludeAssets: null,
      }),
    ].filter(Boolean),

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@/components': resolve(__dirname, 'src/components'),
        '@/pages': resolve(__dirname, 'src/pages'),
        '@/hooks': resolve(__dirname, 'src/hooks'),
        '@/utils': resolve(__dirname, 'src/utils'),
        '@/types': resolve(__dirname, 'src/types'),
        '@/services': resolve(__dirname, 'src/services'),
        '@/store': resolve(__dirname, 'src/store'),
        '@/assets': resolve(__dirname, 'src/assets'),
        '@/styles': resolve(__dirname, 'src/styles'),
        '@/config': resolve(__dirname, 'src/config'),
        '@/lib': resolve(__dirname, 'src/lib'),
      },
    },

    server: {
      port: 3000,
      host: true,
      open: true,
      cors: true,
      proxy: {
        '/api': {
          target: 'http://localhost:3003',
          changeOrigin: true,
          secure: false,
          ws: true,
        },
        '/ws': {
          target: 'ws://localhost:3003',
          ws: true,
          changeOrigin: true,
        },
      },
    },

    build: {
      target: 'esnext',
      minify: 'terser',
      sourcemap: !isProduction,
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            radix: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
            charts: ['recharts', 'react-chartjs-2', 'plotly.js'],
            utils: ['date-fns', 'clsx', 'tailwind-merge'],
          },
        },
      },
    },

    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        '@tanstack/react-query',
        'framer-motion',
        'lucide-react',
      ],
    },

    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    },
  }
})