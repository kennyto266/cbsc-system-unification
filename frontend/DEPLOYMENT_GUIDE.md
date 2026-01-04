# Frontend Deployment Guide
# 前端部署指南

**Version:** 1.0
**Last Updated:** 2025-12-20

---

## Table of Contents 目錄

1. [Prerequisites 前置要求](#prerequisites-前置要求)
2. [Environment Setup 環境設置](#environment-setup-環境設置)
3. [Build Process 構建流程](#build-process-構建流程)
4. [Deployment Options 部署選項](#deployment-options-部署選項)
5. [Configuration 配置](#configuration-配置)
6. [Monitoring & Logging 監控與日誌](#monitoring--logging-監控與日誌)
7. [Troubleshooting 故障排除](#troubleshooting-故障排除)

---

## Prerequisites 前置要求

### System Requirements 系統要求
- **Node.js:** 18.x or higher
- **npm:** 8.x or higher
- **Git:** 2.x or higher
- **Docker:** 20.x or higher (optional)

### Development Tools 開發工具
```bash
# Install Node.js using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Verify installations
node --version
npm --version
git --version
```

---

## Environment Setup 環境設置

### 1. Clone Repository 克隆倉庫
```bash
git clone <repository-url>
cd CODEX--/frontend
```

### 2. Install Dependencies 安裝依賴
```bash
# Install production dependencies
npm install --production

# Or install all dependencies for development
npm install
```

### 3. Environment Variables 環境變量
Create `.env` file in the `frontend` directory:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:3004
VITE_WS_URL=ws://localhost:3004
VITE_APP_NAME=CBS-C Economic Dashboard
VITE_APP_VERSION=1.0.0

# Development Settings
VITE_ENABLE_MOCK_DATA=false
VITE_LOG_LEVEL=info
VITE_DEBUG_MODE=false

# WebSocket Settings
VITE_WS_RECONNECT_INTERVAL=5000
VITE_WS_MAX_RECONNECT_ATTEMPTS=10

# Chart Configuration
VITE_DEFAULT_CHART_THEME=light
VITE_CHART_ANIMATION_DURATION=300

# Performance Settings
VITE_MAX_LOG_ENTRIES=10000
VITE_DEBOUNCE_DELAY=300
VITE_CACHE_TTL=300000

# Feature Flags
VITE_ENABLE_ADVANCED_FEATURES=true
VITE_ENABLE_BETA_FEATURES=false
```

### 4. Environment-Specific Configurations 特定環境配置

#### Development Environment 開發環境
```env
# .env.development
VITE_API_BASE_URL=http://localhost:3004
VITE_WS_URL=ws://localhost:3004
VITE_ENABLE_MOCK_DATA=true
VITE_LOG_LEVEL=debug
VITE_DEBUG_MODE=true
```

#### Staging Environment 測試環境
```env
# .env.staging
VITE_API_BASE_URL=https://staging-api.cbsc.com
VITE_WS_URL=wss://staging-ws.cbsc.com
VITE_ENABLE_MOCK_DATA=false
VITE_LOG_LEVEL=info
VITE_DEBUG_MODE=false
```

#### Production Environment 生產環境
```env
# .env.production
VITE_API_BASE_URL=https://api.cbsc.com
VITE_WS_URL=wss://ws.cbsc.com
VITE_ENABLE_MOCK_DATA=false
VITE_LOG_LEVEL=error
VITE_DEBUG_MODE=false
```

---

## Build Process 構建流程

### 1. Development Build 開發構建
```bash
# Start development server
npm run dev

# Start with specific port
npm run dev -- --port 3000

# Start with custom host
npm run dev -- --host 0.0.0.0
```

### 2. Production Build 生產構建
```bash
# Build for production
npm run build

# Build with analysis
npm run build:analyze

# Build specific environment
npm run build:staging
```

### 3. Preview Build 預覽構建
```bash
# Preview production build
npm run preview

# Preview with specific port
npm run preview -- --port 4173
```

### 4. Run Tests 運行測試
```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm run test EconomicDataCharts
```

---

## Deployment Options 部署選項

### Option 1: Static File Hosting 靜態文件託管

#### 1.1 Build Application
```bash
npm run build
```

#### 1.2 Deploy to Nginx 部署到Nginx
```bash
# Copy build files to nginx directory
sudo cp -r dist/* /var/www/html/

# Configure nginx
sudo nano /etc/nginx/sites-available/cbsc-frontend
```

Nginx Configuration (`/etc/nginx/sites-available/cbsc-frontend`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

#### 1.3 Enable Site 啟用站點
```bash
sudo ln -s /etc/nginx/sites-available/cbsc-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Docker Deployment Docker部署

#### 2.1 Create Dockerfile
```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

#### 2.2 Create nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # SPA fallback
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

#### 2.3 Build and Run Docker Container
```bash
# Build Docker image
docker build -t cbsc-frontend:latest .

# Run container
docker run -d \
  --name cbsc-frontend \
  -p 80:80 \
  -e VITE_API_BASE_URL=https://api.cbsc.com \
  -e VITE_WS_URL=wss://ws.cbsc.com \
  cbsc-frontend:latest
```

#### 2.4 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: .
    container_name: cbsc-frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=https://api.cbsc.com
      - VITE_WS_URL=wss://ws.cbsc.com
    restart: unless-stopped
    networks:
      - cbsc-network

networks:
  cbsc-network:
    external: true
```

```bash
# Deploy with Docker Compose
docker-compose up -d
```

### Option 3: Cloud Platform Deployment 雲平台部署

#### 3.1 AWS S3 + CloudFront
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Deploy to S3
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

#### 3.2 Google Cloud Storage
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Deploy to GCS
gsutil -m rsync -r -d dist/ gs://your-bucket-name
```

#### 3.3 Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel --prod

# Deploy to staging
vercel
```

---

## Configuration 配置

### 1. Build Configuration 構建配置

#### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  const isStaging = mode === 'staging'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@hooks': resolve(__dirname, 'src/hooks'),
        '@services': resolve(__dirname, 'src/services'),
        '@store': resolve(__dirname, 'src/store'),
        '@types': resolve(__dirname, 'src/types'),
        '@utils': resolve(__dirname, 'src/utils')
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: !isProduction,
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: isProduction,
          drop_debugger: isProduction
        }
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            redux: ['@reduxjs/toolkit', 'react-redux'],
            charts: ['recharts'],
            utils: ['date-fns', 'lodash']
          }
        }
      },
      chunkSizeWarningLimit: 1000
    },
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: 'http://localhost:3004',
          changeOrigin: true
        },
        '/ws': {
          target: 'ws://localhost:3004',
          ws: true
        }
      }
    },
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString())
    }
  }
})
```

### 2. Package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "build:staging": "vite build --mode staging",
    "build:analyze": "vite-bundle-analyzer dist",
    "preview": "vite preview",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "type-check": "tsc --noEmit",
    "clean": "rimraf dist",
    "deploy:staging": "npm run build:staging && aws s3 sync dist/ s3://staging-bucket",
    "deploy:prod": "npm run build && aws s3 sync dist/ s3://production-bucket"
  }
}
```

### 3. ESLint Configuration
```javascript
// .eslintrc.js
module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'react-hooks/exhaustive-deps'
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    'react-hooks/exhaustive-deps': 'warn'
  },
}
```

---

## Monitoring & Logging 監控與日誌

### 1. Performance Monitoring 性能監控

#### Google Analytics Setup
```typescript
// src/utils/analytics.ts
export const initAnalytics = () => {
  if (import.meta.env.PROD) {
    // Initialize Google Analytics
    gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: document.title,
      page_location: window.location.href
    })
  }
}

export const trackEvent = (eventName: string, parameters?: Record<string, any>) => {
  if (import.meta.env.PROD) {
    gtag('event', eventName, parameters)
  }
}
```

#### Error Tracking
```typescript
// src/utils/errorTracking.ts
export const trackError = (error: Error, context?: Record<string, any>) => {
  console.error('Application Error:', error, context)

  if (import.meta.env.PROD) {
    // Send to error tracking service (e.g., Sentry)
    // Sentry.captureException(error, { extra: context })
  }
}
```

### 2. Logging Configuration 日誌配置

#### Development Logging
```typescript
// src/utils/logger.ts
export const logger = {
  debug: (message: string, data?: any) => {
    if (import.meta.env.DEV) {
      console.debug(`[DEBUG] ${message}`, data)
    }
  },
  info: (message: string, data?: any) => {
    if (import.meta.env.DEV || import.meta.env.MODE === 'staging') {
      console.info(`[INFO] ${message}`, data)
    }
  },
  warn: (message: string, data?: any) => {
    console.warn(`[WARN] ${message}`, data)
  },
  error: (message: string, error?: Error | any) => {
    console.error(`[ERROR] ${message}`, error)
    trackError(error instanceof Error ? error : new Error(message))
  }
}
```

### 3. Performance Metrics 性能指標

#### Web Vitals
```typescript
// src/utils/webVitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

export const reportWebVitals = (onPerfEntry?: (metric: any) => void) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry)
      getFID(onPerfEntry)
      getFCP(onPerfEntry)
      getLCP(onPerfEntry)
      getTTFB(onPerfEntry)
    })
  }
}
```

---

## Troubleshooting 故障排除

### Common Issues 常見問題

#### 1. Build Fails 構建失敗
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
npm run dev
```

#### 2. TypeScript Errors TypeScript錯誤
```bash
# Check TypeScript configuration
npx tsc --noEmit

# Update types
npm update
```

#### 3. CSS Issues CSS問題
```bash
# Check Tailwind configuration
npx tailwindcss --help

# Rebuild CSS
npm run build
```

#### 4. Environment Variables 環境變量
```bash
# Check current environment
echo $VITE_API_BASE_URL

# Reload environment variables
source .env
```

### Performance Issues 性能問題

#### 1. Bundle Size Analysis 包大小分析
```bash
# Analyze bundle size
npm run build:analyze
```

#### 2. Memory Leaks 內存泄漏
```bash
# Check memory usage in Chrome DevTools
# Look for detached DOM nodes
# Profile component unmounting
```

#### 3. Slow Loading 加載緩慢
```bash
# Check network requests
# Enable code splitting
# Optimize images
# Use CDN
```

### Debugging Steps 調試步驟

#### 1. Enable Debug Mode 啟用調試模式
```env
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

#### 2. Check Console 檢查控制檯
- Look for JavaScript errors
- Check network requests
- Monitor console logs

#### 3. Use Browser Tools 使用瀏覽器工具
- Chrome DevTools
- React Developer Tools
- Redux DevTools

---

## Security Considerations 安全考量

### 1. HTTPS Only 僅HTTPS
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    # SSL configuration
}
```

### 2. Security Headers 安全頭部
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 3. Input Validation 輸入驗證
```typescript
// Validate API responses
const validateApiResponse = (response: any) => {
  if (!response || typeof response !== 'object') {
    throw new Error('Invalid API response')
  }
  return response
}
```

---

## Maintenance 維護

### 1. Regular Updates 定期更新
```bash
# Check for updates
npm outdated

# Update dependencies
npm update

# Security audit
npm audit
npm audit fix
```

### 2. Backup 備份
```bash
# Backup configuration
cp .env.example .env.backup

# Backup build artifacts
tar -czf dist-backup.tar.gz dist/
```

### 3. Monitoring 監控
- Set up uptime monitoring
- Monitor error rates
- Track performance metrics
- Regular security scans

---

**Contact Information 聯繫信息**
- **Development Team:** dev-team@cbsc.com
- **Support:** support@cbsc.com
- **Security:** security@cbsc.com

*This guide will be updated regularly to reflect changes in deployment processes and best practices.*

*Last Updated: 2025-12-20*