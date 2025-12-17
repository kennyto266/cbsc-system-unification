/**
 * Next.js Configuration
 * CBSC量化交易系統的Next.js應用配置
 */

const { i18n } = require('./next-i18next.config')

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 基本配置
  reactStrictMode: true,
  swcMinify: true,

  // 國際化配置
  i18n,

  // 圖片優化
  images: {
    domains: [
      'localhost',
      'cbsc.com',
      'api.cbsc.com',
      'cdn.cbsc.com',
    ],
    formats: ['image/webp', 'image/avif'],
  },

  // 環境變量
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // 重寫規則
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:3003/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'ws://localhost:3003/:path*',
      },
    ]
  },

  // 路由配置
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: false,
      },
    ]
  },

  // Webpack配置
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 添加自定義webpack配置
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    }

    return config
  },

  // 實驗性功能
  experimental: {
    // 啟用應用目錄結構
    appDir: false, // 暫時禁用，保持pages目錄結構

    // 啟用並發功能
    concurrentFeatures: true,

    // 服務器組件
    serverComponentsExternalPackages: ['@prisma/client'],
  },

  // 頁面擴展
  pageExtensions: ['ts', 'tsx', 'js', 'jsx'],

  // 輸出配置
  output: 'standalone',

  // 壓縮配置
  compress: true,

  // 靜態文件導出
  trailingSlash: false,

  // 頭部配置
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ]
  },
}

// 開發環境特定配置
if (process.env.NODE_ENV === 'development') {
  nextConfig.compiler = {
    ...nextConfig.compiler,
    // 開發環境移除console.log
    removeConsole: false,
  }
}

// 生產環境特定配置
if (process.env.NODE_ENV === 'production') {
  nextConfig.compiler = {
    ...nextConfig.compiler,
    // 生產環境移除console.log
    removeConsole: true,
  }
}

module.exports = nextConfig