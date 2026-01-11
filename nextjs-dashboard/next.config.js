/** @type {import('next').NextConfig} */
const nextConfig = {
  // React嚴格模式
  reactStrictMode: true,

  // 啟用SWC壓縮
  swcMinify: true,

  // 圖片域名配置
  images: {
    domains: ['localhost', 'api.cbsc.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // 環境變量
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // 重定向配置
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/dashboard',
        permanent: true,
      },
    ]
  },

  // 重寫配置
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:3004/api/:path*',
      },
    ]
  },

  // 頁面預渲染配置
  async generateStaticParams() {
    const posts = await fetch('https://.../posts').then((res) => res.json())

    return posts.map((post) => ({
      slug: post.slug,
    }))
  },

  // Webpack配置
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 添加webpack插件
    config.plugins.push(
      new webpack.ProvidePlugin({
        Buffer: ['buffer', 'Buffer'],
      })
    )

    return config
  },

  // 實驗性功能
  experimental: {
    // 啟用appDir (App Router)
    appDir: true,

    // 啟用serverComponentsExternalPackages
    serverComponentsExternalPackages: ['@prisma/client', 'bcryptjs'],

    // 啟用serverActions
    serverActions: true,

    // 優化包大小
    optimizePackageImports: [
      'antd',
      '@ant-design/icons',
      'lodash',
      'date-fns',
      'recharts',
    ],
  },

  // 輸出配置
  output: 'standalone',

  // 國際化配置
  i18n: {
    locales: ['zh-CN', 'en-US'],
    defaultLocale: 'zh-CN',
  },

  // PWA配置
  pwa: {
    dest: 'public',
    disable: process.env.NODE_ENV === 'development',
    register: true,
    skipWaiting: true,
  },
}

module.exports = nextConfig