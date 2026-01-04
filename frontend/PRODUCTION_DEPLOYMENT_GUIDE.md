# 生產環境部署和運維指南
# Production Deployment and Operations Guide

**版本:** 1.0
**最後更新:** 2025-12-20
**狀態:** ✅ 就緒生產

---

## 📋 目錄 Table of Contents

1. [部署準備](#部署準備)
2. [生產環境部署](#生產環境部署)
3. [監控設置](#監控設置)
4. [日常運維](#日常運維)
5. [故障排除](#故障排除)
6. [性能優化](#性能優化)

---

## 🔧 部署準備 Deployment Prerequisites

### 系統要求 System Requirements
- **Node.js:** 18.x 或更高版本
- **內存:** 最少 2GB RAM
- **存儲:** 最少 20GB 可用空間
- **網絡:** 穩定的互聯網連接
- **操作系統:** Linux (推薦 Ubuntu 20.04+) 或 Windows Server 2019+

### 依賴服務 Dependencies
- **後端API服務:** 必須運行在 `http://localhost:3004` 或配置的遠程地址
- **數據庫服務:** PostgreSQL 12+ 或 MySQL 8.0+
- **Redis服務:** 用於緩存和會話管理
- **WebSocket服務:** 支持實時數據推送

### 預檢清單 Pre-Deployment Checklist
- [ ] 後端API服務正常運行
- [ ] 數據庫連接正常
- [ ] 環境變量配置完成
- [ ] SSL證書配置（HTTPS）
- [ ] 域名DNS解析完成
- [ ] 防火牆規則配置

---

## 🚀 生產環境部署 Production Deployment

### 方案一：靜態文件服務器部署

#### 1. 構建應用程序
```bash
# 構建生產版本
npm run build

# 驗證構建文件
ls -la dist/
```

#### 2. Nginx 配置
```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 證書配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # 根目錄
    root /var/www/html;
    index index.html;

    # Gzip 壓縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        application/javascript
        application/xml+rss
        application/json;

    # 靜態資源緩存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    # 單頁應用路由
    location / {
        try_files $uri $uri/ /index.html;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:3004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://localhost:3004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. 部署文件
```bash
# 複製構建文件
sudo cp -r dist/* /var/www/html/

# 設置權限
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/

# 重新加載 Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 方案二：Docker 容器化部署

#### 1. 構建 Docker 鏡像
```bash
# 構建應用鏡像
docker build -t cbsc-frontend:1.0.0 .

# 或使用現有鏡像
docker build -t cbsc-frontend:latest .
```

#### 2. Docker Compose 部署
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    image: cbsc-frontend:1.0.0
    container_name: cbsc-frontend
    ports:
      - "80:80"
      - "443:443"
    environment:
      - VITE_API_BASE_URL=https://api.your-domain.com
      - VITE_WS_URL=wss://api.your-domain.com
      - VITE_APP_NAME=CBSC量化策略管理系統
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    restart: unless-stopped
    networks:
      - cbsc-network

networks:
  cbsc-network:
    external: true
```

#### 3. 啟動服務
```bash
# 啟動服務
docker-compose -f docker-compose.prod.yml up -d

# 查看服務狀態
docker-compose -f docker-compose.prod.yml ps

# 查看日誌
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 方案三：CDN 部署 (靜態站點託管)

#### 1. 構建配置更新
```typescript
// vite.config.ts
export default defineConfig({
  base: '/your-app-path/',
  build: {
    assetsDir: 'assets',
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
          utils: ['date-fns', 'lodash']
        }
      }
    }
  }
})
```

#### 2. AWS S3 + CloudFront 部署
```bash
# 安裝 AWS CLI
pip install awscli

# 配置 AWS 憑證
aws configure

# 上傳到 S3
aws s3 sync dist/ s3://your-bucket-name --delete

# 配置 CloudFront 分發
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

---

## 📊 監控設置 Monitoring Setup

### 1. 應標監控

#### 應標收集配置
```typescript
// src/utils/metrics.ts
export const setupMetrics = () => {
  // Web Vitals 指標
  reportWebVitals((metric) => {
    // 發送到監控服務
    console.log('Performance Metric:', metric);

    // 發送到 Google Analytics
    if (window.gtag) {
      window.gtag('event', metric.name, {
        event_category: 'Web Vitals',
        value: metric.value,
        non_interaction: true,
      });
    }
  });

  // 自定義指標
  const observeChartRenderTime = () => {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name.includes('chart-render')) {
          console.log('Chart Render Time:', entry.duration);
        }
      }
    });
    observer.observe({ entryTypes: ['measure'] });
  };

  observeChartRenderTime();
};
```

### 2. 錯誤監控

#### 錯誤邊界設置
```typescript
// src/components/ErrorBoundary.tsx
import React from 'react';

export class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error, errorInfo) {
    return { hasError: true, error, errorInfo };
  }

  componentDidCatch(error, errorInfo) {
    // 發送錯誤到監控服務
    console.error('Application Error:', error, errorInfo);

    // 發送到 Sentry 或其他錯誤追蹤服務
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        extra: errorInfo,
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>應用程序出現錯誤</h2>
          <details>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo.componentStack}
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 3. 日誌管理

#### 日誌配置
```typescript
// src/utils/logger.ts
export class Logger {
  static info(message: string, data?: any) {
    console.info(`[INFO] ${message}`, data);
  }

  static warn(message: string, data?: any) {
    console.warn(`[WARN] ${message}`, data);
  }

  static error(message: string, error?: Error | any) {
    console.error(`[ERROR] ${message}`, error);

    // 發送到後端日誌服務
    this.sendToServer('error', message, error);
  }

  static sendToServer(level: string, message: string, data?: any) {
    if (import.meta.env.PROD) {
      fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          timestamp: new Date().toISOString(),
          level,
          message,
          data,
          url: window.location.href,
          userAgent: navigator.userAgent,
        }),
      });
    }
  }
}
```

### 4. 性能監控

#### 性能分析工具
```typescript
// src/utils/performance.ts
export class PerformanceMonitor {
  static measureComponentRender(componentName: string, renderFn: () => void) {
    const startTime = performance.now();
    renderFn();
    const endTime = performance.now();

    const duration = endTime - startTime;

    if (duration > 100) {
      console.warn(`Slow Render: ${componentName} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  static measureAsyncOperation<T>(
    operationName: string,
    operation: () => Promise<T>
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const startTime = performance.now();

      operation()
        .then((result) => {
          const endTime = performance.now();
          const duration = endTime - startTime;

          if (duration > 1000) {
            console.warn(`Slow Operation: ${operationName} took ${duration.toFixed(2)}ms`);
          }

          resolve(result);
        })
        .catch((error) => {
          const endTime = performance.now();
          const duration = endTime - startTime;

          console.error(`Operation Failed: ${operationName} failed after ${duration.toFixed(2)}ms`, error);
          reject(error);
        });
    });
  }
}
```

---

## 🔧 日常運維 Daily Operations

### 1. 備份策略 Backup Strategy

#### 數據庫備份
```bash
#!/bin/bash
# backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"

# 創建數據庫備份
mysqldump -u root -p cbsc_db > "$BACKUP_DIR/cbsc_db_$DATE.sql"

# 壓縮備份
gzip "$BACKUP_DIR/cbsc_db_$DATE.sql"

# 清理30天前的備份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: cbsc_db_$DATE.sql.gz"
```

#### 應用文件備份
```bash
#!/bin/bash
# backup-application.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/application"

# 備份應用配置
tar -czf "$BACKUP_DIR/app_config_$DATE.tar.gz" \
  /etc/nginx/sites-available/cbsc-frontend \
  /var/www/html/.env \
  /var/www/html/package.json

# 備份日誌
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
  /var/log/nginx/ \
  /var/log/cbsc/

echo "Application backup completed"
```

### 2. 系統維護 System Maintenance

#### 定期清理腳本
```bash
#!/bin/bash
# system-cleanup.sh

# 清理 Docker 佔用鏡像
docker system prune -f

# 清理 Nginx 舊用日志
find /var/log/nginx/ -name "*.log" -mtime +7 -delete

# 清理系統日誌
journalctl --vacuum-time=7days

# 檢查磁盤空間
df -h

echo "System cleanup completed"
```

#### 健康檢查腳本
```bash
#!/bin/bash
# health-check.sh

# 檢查服務狀態
echo "=== Service Status ==="
systemctl status nginx
systemctl status docker

# 檢查磁盤使用
echo "=== Disk Usage ==="
df -h

# 檢查內存使用
echo "=== Memory Usage ==="
free -h

# 檢查負載
echo "=== System Load ==="
uptime

# 檢查網絡連接
echo "=== Network Status ==="
ping -c 3 8.8.8.8
curl -f -s http://localhost:3004/api/health > /dev/null && echo "✅ API Server OK" || echo "❌ API Server Down"

# 檢查應用響應時間
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:3004/api/health)
echo "API Response Time: ${RESPONSE_TIME}s"
```

### 3. 日誌分析 Log Analysis

#### 日誌分析腳本
```bash
#!/bin/bash
# analyze-logs.sh

LOG_DATE=$(date +%Y-%m-%d)
LOG_FILE="/var/log/nginx/access_$LOG_DATE.log"

# 分析訪問統計
echo "=== Access Statistics ==="
echo "Total Requests: $(grep -c $LOG_FILE)"

# 分析錯誤日誌
echo "=== Error Analysis ==="
grep " 5[0-9][0-9] " $LOG_FILE | tail -20

# 分析熱門頁面
echo "=== Top Pages ==="
grep -oP 'GET \K([^"]+)' $LOG_FILE | sort | uniq -c | sort -nr | head -10

# 分析響應時間
echo "=== Response Time Analysis ==="
grep -oP 'response_time: \K(\d+\.\d+)' $LOG_FILE | awk '{sum+=$1; count++} END {print "Avg Response Time:", sum/count "seconds"}'
```

---

## 🚨 故障排除 Troubleshooting

### 常見問題及解決方案

#### 1. 應用加載緩慢
**問題**: 首屏加載超過3秒
**解決方案**:
```bash
# 檢查網絡延遲
ping api.your-domain.com

# 檢查資源加載
curl -w "@%{time_total},%{size_download}\n" -o /dev/null -s "https://your-domain.com/assets/vendor-l0sNRNKZ.js"

# 檢查資源大小
du -sh dist/assets/
```

**優化措施**:
- 啟用資源預加載
- 實施圖片懶加載
- 優化CSS和JS文件大小
- 使用CDN加速

#### 2. API連接失敗
**問題**: 無法連接到後端API
**解決方案**:
```bash
# 檢查API服務狀態
curl -f http://localhost:3004/api/health

# 檢查防火牆設置
sudo ufw status
sudo iptables -L

# 檢查代理配置
nginx -t
```

**解決步驟**:
1. 確認後端API服務運行
2. 檢查網絡連接和防火牆
3. 驗證代理配置
4. 檢查SSL證書有效性

#### 3. WebSocket 連接斷開
**問題**: 實時數據連接頻繁斷開
**解決方案**:
```bash
# 檢查WebSocket配置
curl -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     http://localhost:3004/ws

# 檢查代理設置
nginx -T | grep -A 10 -B 10 "location /ws/"
```

**優化措施**:
- 增加連接超時時間
- 實施自動重連機制
- 調整keep-alive設置
- 監控連接健康狀態

#### 4. 內存使用過高
**問題**: 瀏覽器內存使用超過500MB
**解決方案**:
```typescript
// 檢查內存洩漏
const checkMemoryLeaks = () => {
  setInterval(() => {
    if (performance.memory) {
      const memoryInfo = performance.memory;
      console.log('Memory Usage:', {
        used: `${(memoryInfo.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        total: `${(memoryInfo.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        limit: `${(memoryInfo.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
      });
    }
  }, 30000); // 每30秒檢查一次
};
```

**優化措施**:
- 清理不再使用的組件
- 優化數據結構
- 實施虛擬滾動
- 避免過度狀態管理

#### 5. 圖表渲染性能問題
**問題**: 大量數據圖表渲染緩慢
**解決方案**:
```typescript
// 實施數據抽樣
const sampleData = (data, maxPoints = 1000) => {
  if (data.length <= maxPoints) return data;
  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// 實施懶加載渲染
const useLazyRendering = (threshold = 100) => {
  const [visibleItems, setVisibleItems] = useState(threshold);

  const loadMore = useCallback(() => {
    setVisibleItems(prev => Math.min(prev + threshold, data.length));
  }, [data.length]);

  return { visibleItems, loadMore };
};
```

---

## ⚡ 性能優化 Performance Optimization

### 1. 前端優化

#### 代碼分割
```typescript
// 動態導入組件
const LazyComponent = React.lazy(() => import('./HeavyComponent'));

const App = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <LazyComponent />
  </Suspense>
);
```

#### 資源優化
```typescript
// 圖片預加載
const preloadImage = (src: string) => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = 'image';
  link.href = src;
  document.head.appendChild(link);
};

// 預加載關鍵資源
preloadImage('/images/charts/placeholder.png');
preloadImage('/icons/loading.gif');
```

### 2. 緩存優化

#### 瀋覽緩存策略
```typescript
// Service Worker 緩存
self.addEventListener('fetch', (event) => {
  if (event.request.method === 'GET') {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
```

#### 內存緩存策略
```typescript
// LRU 緩存實現
class LRUCache {
  private cache = new Map();
  private maxSize: number;

  constructor(maxSize: number) {
    this.maxSize = maxSize;
  }

  get(key: string): any {
    if (this.cache.has(key)) {
      const value = this.cache.get(key);
      this.cache.delete(key);
      this.cache.set(key, value);
      return value;
    }
    return null;
  }

  set(key: string, value: any): void {
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }
}
```

### 3. 網絡優化

#### HTTP/2 推送
```nginx
server {
    listen 443 ssl http2;
    http2_max_field_size 8k;
    http2_max_header_size 16k;

    # 資源推送
    location = / {
        http2_push /assets/vendor-l0sNRNKZ.js;
        http2_push /assets/charts-l0sNRNKZ.js;
    }
}
```

#### 壓縮優化
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types
    text/plain
    text/css
    text/xml
    application/javascript
    application/json
    application/xml+rss;

# Brotli 壓縮
brotli on;
brotli_types
    text/plain
    text/css
    application/javascript
    application/json;
```

---

## 📈 監控指標和報告 Monitoring Metrics & Reports

### 核心指標 Core Metrics
- **可用性**: 99.9% 目標
- **響應時間**: < 2秒目標
- **錯誤率**: < 0.1% 目標
- **併發率**: < 1000TPS 目標

### 報警設置 Alert Configuration
```typescript
// 錯誤率警
const ERROR_RATE_THRESHOLD = 0.001;
const RESPONSE_TIME_THRESHOLD = 2000;

// 監控檢查
const checkHealth = async () => {
  const metrics = await collectMetrics();

  if (metrics.errorRate > ERROR_RATE_THRESHOLD) {
    sendAlert('high_error_rate', metrics.errorRate);
  }

  if (metrics.avgResponseTime > RESPONSE_TIME_THRESHOLD) {
    sendAlert('slow_response', metrics.avgResponseTime);
  }
};
```

### 定期報告 Regular Reports
- **每日報告**: 系統健康狀態摘要
- **週報告**: 性能趨勢分析
- **月報告**: 容量規劃建議
- **事件報告**: 故障事件分析

---

## 🔒 安全性考慮 Security Considerations

### 安全檢查清單 Security Checklist

#### 基礎安全 Basic Security
- [ ] SSL/TLS 證證配置
- [ ] HTTP 強制重定向到 HTTPS
- [ ] 安全頭部配置
- [ ] 依賴項安全掃描

#### 應用程序安全 Application Security
- [ ] XSS 防護實施
- [ ] CSRF 令牌使用
- [ ] 輸入驗證和清理
- [� SQL 注入防護
- [ ] 權限控制正確實施

### 安全監控 Security Monitoring

#### 安全事件日誌
```typescript
// 安全事件記錄
const logSecurityEvent = (event: SecurityEvent) => {
  const securityLog = {
    timestamp: new Date().toISOString(),
    type: event.type,
    severity: event.severity,
    source: event.source,
    details: event.details,
    ip: event.ip,
    userAgent: event.userAgent
  };

  // 發送到安全監控服務
  fetch('/api/security/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(securityLog),
  });
};
```

#### 異常檢測 Anomaly Detection
```typescript
// 異常行為檢測
const detectAnomalies = () => {
  const recentRequests = getRecentRequests();

  // 檢查頻率限制
  const requestsPerSecond = recentRequests.length / 60;
  if (requestsPerSecond > 100) {
    sendAlert('high_frequency_requests', requestsPerSecond);
  }

  // 檢查異常用戶代理
  const uniqueIPs = new Set(recentRequests.map(req => req.ip));
  const requestsPerIP = uniqueIPs.size > 0 ?
    recentRequests.length / uniqueIPs.size : 0;

  if (requestsPerIP > 50) {
    sendAlert('potential_ddos', requestsPerIP);
  }
};
```

---

## 📞 緊急聯繫信息 Emergency Contacts

### 技術支持 Technical Support
- **開發團隊**: dev-team@cbsc.com
- **DevOps團隊**: ops-team@cbsc.com
- **安全團隊**: security@cbsc.com

### 運聯方式 Contact Methods
- **緊急電話**: +86-xxx-xxxx-xxxx
- **緊急郵件**: emergency@cbsc.com
- **Slack 通道**: #cbsc-emergency
- **監控平台**: https://monitoring.cbsc.com

### 升級流程 Escalation Process
1. **L1**: 自動監控和自動修復
2. **L2**: 值班工程師響應 (15分鐘內)
3. **L3**: 高級工程師介入 (1小時內)
4. **L4**: 架構師和主管協商 (4小時內)

---

## 📝 更新日誌 Changelog

### v1.0.0 (2025-12-20)
- ✅ 完成P0和P1任務開發
- ✅ 系統集成測試和驗證
- ✅ 生產環境部署準備
- ✅ 完整文檔和監控指南

### 更新歷史 Update History
- 詳略配置向導開發
- 移動端響應式優化
- 性能基準測試完成
- 部署文檔更新

---

## 🎯 未來規劃 Future Roadmap

### 短期目標 Short-term Goals
- 用戶反饋收集和改進
- 性能優化和調優
- 安全加固和合規檢查
- 監控系統完善

### 長期目標 Long-term Goals
- AI功能增強和集成
- 多語言和國際化支持
- 移動端原生應用開發
- 微服務架構轉型

---

**文檔版本**: 1.0
**維護者**: 開發團隊
**審核者**: 運維團隊
**批准者**: 技術主管

*最後更新: 2025-12-20*
*下次審核: 2026-01-20*