import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 指定 Turbopack 根目錄
  turbopack: {
    root: './',
  },

  // API 代理配置 - 暫時禁用以避免循環
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:3004/api/:path*',  // 後端API端口
  //     },
  //   ];
  // },

  // 環境變量配置
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3004',
    BACKEND_API_URL: process.env.BACKEND_API_URL || 'http://localhost:3004',
  },

  // TypeScript 配置
  transpilePackages: ['@headlessui/react'],

  // 優化配置
  experimental: {
    optimizePackageImports: ['@headlessui/react', 'lucide-react'],
  },
};

export default nextConfig;
