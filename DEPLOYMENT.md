# CBSC Strategy Management System Deployment Guide
# CBSC 策略管理系統部署指南

## 📋 Table of Contents / 目錄

1. [Overview / 概述](#overview)
2. [Prerequisites / 先決條件](#prerequisites)
3. [Environment Configuration / 環境配置](#environment-configuration)
4. [Deployment Steps / 部署步驟](#deployment-steps)
5. [SSL Configuration / SSL 配置](#ssl-configuration)
6. [Monitoring Setup / 監控設置](#monitoring-setup)
7. [Backup Strategy / 備份策略](#backup-strategy)
8. [Troubleshooting / 故障排除](#troubleshooting)
9. [Maintenance / 維護](#maintenance)

## 📖 Overview / 概述

This guide provides step-by-step instructions for deploying the CBSC Strategy Management System to a production environment. The system uses Docker containers with the following components:

本指南提供了將 CBSC 策略管理系統部署到生產環境的逐步說明。系統使用 Docker 容器，包含以下組件：

- **Backend API**: FastAPI application
- **Frontend**: React application
- **Database**: PostgreSQL
- **Cache**: Redis
- **Time Series DB**: InfluxDB
- **Monitoring**: Prometheus + Grafana
- **Reverse Proxy**: Nginx

## 🔧 Prerequisites / 先決條件

### Hardware Requirements / 硬件要求

- **CPU**: 4+ cores
- **Memory**: 16GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps connection

### Software Requirements / 軟件要求

- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.0+
- **OpenSSL**: 1.1.1+ (for SSL certificates)

### User Permissions / 用戶權限

- sudo or root access
- Docker daemon access
- SSH access for remote deployment

## ⚙️ Environment Configuration / 環境配置

### 1. Clone Repository / 複製存儲庫

```bash
sudo mkdir -p /opt/cbsc
cd /opt/cbsc
sudo git clone https://github.com/your-org/cbsc-strategy-management.git .
```

### 2. Environment Variables / 環境變量

Copy and configure the production environment file:

複製並配置生產環境文件：

```bash
sudo cp .env.prod.example .env.prod
sudo nano .env.prod
```

**Critical configuration items / 關鍵配置項目：**

```bash
# Database passwords / 數據庫密碼
POSTGRES_PASSWORD=your_strong_postgres_password
REDIS_PASSWORD=your_strong_redis_password

# Application secrets / 應用程序密鑰
JWT_SECRET=your_jwt_secret_key_here
SECRET_KEY=your_application_secret_key_here

# Domain configuration / 域名配置
DOMAIN=your-domain.com

# SSL certificates / SSL 證書
SSL_CERT_PATH=/path/to/your/cert.pem
SSL_KEY_PATH=/path/to/your/key.pem
```

### 3. Generate Strong Passwords / 生成強密碼

```bash
# Generate random passwords / 生成隨機密碼
openssl rand -base64 32  # PostgreSQL password
openssl rand -base64 32  # Redis password
openssl rand -base64 64  # JWT secret
```

## 🚀 Deployment Steps / 部署步驟

### Option 1: Automated Deployment / 自動化部署

Use the provided deployment script:

使用提供的部署腳本：

```bash
# Make script executable / 使腳本可執行
chmod +x scripts/deploy.sh

# Run deployment / 運行部署
sudo ./scripts/deploy.sh .env.prod
```

### Option 2: Manual Deployment / 手動部署

#### Step 1: Prepare Directories / 準備目錄

```bash
sudo mkdir -p /opt/cbsc/{logs,ssl,backups}
sudo mkdir -p /opt/cbsc/config/{nginx,prometheus,grafana}
```

#### Step 2: Set Up SSL Certificates / 設置 SSL 證書

```bash
# Option A: Self-signed certificates (for testing) / 自簽名證書（用於測試）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/cbsc/ssl/key.pem \
    -out /opt/cbsc/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Option B: Let's Encrypt certificates (recommended for production) / Let's Encrypt 證書（生產推薦）
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/cbsc/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/cbsc/ssl/key.pem
```

#### Step 3: Deploy Services / 部署服務

```bash
cd /opt/cbsc

# Load environment variables / 加載環境變量
sudo cp .env.prod .env

# Start core services first / 首先啟動核心服務
sudo docker-compose -f docker-compose.prod.yml up -d postgres redis influxdb

# Wait for services to be ready / 等待服務就緒
sleep 60

# Run database migrations / 運行數據庫遷移
sudo docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start application services / 啟動應用程序服務
sudo docker-compose -f docker-compose.prod.yml up -d backend monitoring

# Start frontend and proxy / 啟動前端和代理
sudo docker-compose -f docker-compose.prod.yml up -d frontend nginx

# Start monitoring services / 啟動監控服務
sudo docker-compose -f docker-compose.prod.yml up -d prometheus grafana
```

#### Step 4: Verify Deployment / 驗證部署

```bash
# Check service status / 檢查服務狀態
sudo docker-compose -f docker-compose.prod.yml ps

# Check logs / 檢查日誌
sudo docker-compose -f docker-compose.prod.yml logs -f

# Health checks / 健康檢查
curl -f http://localhost:3004/health  # Backend API / 後端 API
curl -f http://localhost:3000        # Frontend / 前端
curl -f https://your-domain.com      # Production site / 生產站點
```

## 🔐 SSL Configuration / SSL 配置

### Nginx SSL Configuration / Nginx SSL 配置

Update the Nginx configuration for your domain:

為您的域名更新 Nginx 配置：

```bash
sudo nano config/nginx/conf.d/default.conf
```

Key SSL settings / 關鍵 SSL 設置：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates / SSL 證書
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL configuration / SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS / HTTP 嚴格傳輸安全
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### Auto-renew SSL with Let's Encrypt / Let's Encrypt 自動續期

```bash
# Add cron job for auto-renewal / 添加自動續期的 cron 任務
sudo crontab -e

# Add this line / 添加此行
0 3 * * * /usr/bin/certbot renew --quiet && docker-compose -f /opt/cbsc/docker-compose.prod.yml restart nginx
```

## 📊 Monitoring Setup / 監控設置

### Grafana Configuration / Grafana 配置

1. Access Grafana: `https://your-domain.com/grafana`
   - Default username: `admin`
   - Default password: Check `.env.prod` file

2. Configure data sources / 配置數據源：
   - Prometheus: `http://prometheus:9090`
   - InfluxDB: `http://influxdb:8086`

3. Import dashboards / 導入儀表板：
   - System metrics
   - Application performance
   - Database performance

### Prometheus Alerts / Prometheus 警報

Configure alerts in `config/prometheus/rules/`:

在 `config/prometheus/rules/` 中配置警報：

```yaml
# alert.yml
groups:
  - name: CBSC Alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"
```

## 💾 Backup Strategy / 備份策略

### Automated Backups / 自動化備份

Use the provided backup script:

使用提供的備份腳本：

```bash
# Make backup script executable / 使備份腳本可執行
chmod +x scripts/backup.sh

# Run backup manually / 手動運行備份
sudo ./scripts/backup.sh

# Add to cron for daily backups / 添加到 cron 以進行每日備份
sudo crontab -e
```

Add this line for daily backups at 2 AM:

為每日凌晨 2 點備份添加此行：

```bash
0 2 * * * /opt/cbsc/scripts/backup.sh
```

### Backup Contents / 備份內容

- PostgreSQL database
- Redis data
- InfluxDB time-series data
- Configuration files
- SSL certificates
- Application logs

### Recovery / 恢復

```bash
# List available backups / 列出可用備份
sudo ls -la /opt/cbsc/backups/

# Restore from backup / 從備份恢復
sudo ./scripts/restore.sh /opt/cbsc/backups/backup-YYYYMMDD-HHMMSS
```

## 🔧 Troubleshooting / 故障排除

### Common Issues / 常見問題

#### Service Won't Start / 服務無法啟動

```bash
# Check logs / 檢查日誌
sudo docker-compose -f docker-compose.prod.yml logs [service-name]

# Check resource usage / 檢查資源使用
sudo docker stats

# Check disk space / 檢查磁盤空間
df -h

# Restart service / 重啟服務
sudo docker-compose -f docker-compose.prod.yml restart [service-name]
```

#### Database Connection Issues / 數據庫連接問題

```bash
# Check PostgreSQL status / 檢查 PostgreSQL 狀態
sudo docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check database logs / 檢查數據庫日誌
sudo docker-compose -f docker-compose.prod.yml logs postgres

# Test connection from backend / 從後端測試連接
sudo docker-compose -f docker-compose.prod.yml exec backend python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://user:pass@postgres:5432/db')
    print('Connection successful')
except Exception as e:
    print(f'Connection failed: {e}')
"
```

#### SSL Certificate Issues / SSL 證書問題

```bash
# Check certificate validity / 檢查證書有效性
openssl x509 -in /opt/cbsc/ssl/cert.pem -text -noout

# Check certificate expiry / 檢查證書過期時間
openssl x509 -in /opt/cbsc/ssl/cert.pem -noout -dates

# Test SSL configuration / 測試 SSL 配置
sudo nginx -t
```

#### Performance Issues / 性能問題

```bash
# Check system resources / 檢查系統資源
htop
iotop

# Check Docker resource usage / 檢查 Docker 資源使用
sudo docker stats --no-stream

# Check database performance / 檢查數據庫性能
sudo docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT * FROM pg_stat_activity WHERE state = 'active';
"
```

### Log Locations / 日誌位置

- **Application logs**: `/opt/cbsc/logs/`
- **Docker logs**: `docker-compose logs`
- **System logs**: `/var/log/syslog`
- **Nginx logs**: Docker container logs

## 🔧 Maintenance / 維護

### Regular Tasks / 定期任務

1. **Daily / 每日**
   - Check system health
   - Review backups
   - Monitor alerts

2. **Weekly / 每週**
   - Update Docker images
   - Review security patches
   - Clean up old logs

3. **Monthly / 每月**
   - Update dependencies
   - Performance review
   - Capacity planning

### System Updates / 系統更新

```bash
# Update Docker images / 更新 Docker 鏡像
sudo docker-compose -f docker-compose.prod.yml pull
sudo docker-compose -f docker-compose.prod.yml up -d

# Update OS packages / 更新操作系統包
sudo apt update && sudo apt upgrade -y

# Restart services if needed / 如需要重啟服務
sudo docker-compose -f docker-compose.prod.yml restart
```

### Security Hardening / 安全加固

1. **Regular password rotation / 定期密碼輪換**
2. **SSL certificate monitoring / SSL 證書監控**
3. **Security scan execution / 安全掃描執行**
4. **Access review / 訪問權限審查**

## 📞 Support / 支持

For deployment issues and questions:

有關部署問題和問題，請聯繫：

- **Email**: dev-support@cbsc.example.com
- **Documentation**: https://docs.cbsc.example.com
- **Issues**: https://github.com/your-org/cbsc-strategy-management/issues

---

*Last updated: 2025-12-18*
*Version: 1.0*