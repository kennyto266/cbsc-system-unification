# CBSC量化交易系統監控運維手冊

## 目錄
1. [系統概述](#系統概述)
2. [監控架構](#監控架構)
3. [日常運維操作](#日常運維操作)
4. [告警處理流程](#告警處理流程)
5. [故障排查指南](#故障排查指南)
6. [性能優化](#性能優化)
7. [容量規劃](#容量規劃)
8. [應急預案](#應急預案)
9. [聯繫方式](#聯繫方式)

## 系統概述

### 監控範圍
- **CBSC API服務** (端口3004) - 核心業務API
- **477技術指標引擎** - 實時指標計算
- **WebSocket服務** - 實時數據推送
- **React前端** - 用戶界面
- **PostgreSQL數據庫** - 數據存儲
- **Redis緩存** - 緩存服務
- **系統資源** - CPU、內存、磁盤、網絡

### 監控工具
- **Prometheus** (9090) - 指標收集和存儲
- **Grafana** (3010) - 可視化儀表板
- **AlertManager** (9093) - 告警管理
- **Node Exporter** (9100) - 系統指標
- **cAdvisor** (8080) - 容器指標

### 關鍵SLO
- **服務可用性**: ≥99.9%
- **API響應時間**: P95 < 500ms
- **WebSocket延遲**: < 50ms
- **477指標計算**: P95 < 2s
- **錯誤率**: < 0.1%

## 監控架構

```
┌─────────────────────────────────────────────────────────────┐
│                    CBSC監控架構                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Grafana    │    │   AlertMgr   │    │    Loki      │  │
│  │   (3010)     │    │   (9093)     │    │   (3100)     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Prometheus   │    │  Promtail    │    │   Nginx      │  │
│  │   (9090)     │    │ (日志收集)   │    │   (反向代理)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                           │         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ NodeExporter │    │ cAdvisor     │    │ Blackbox     │  │
│  │   (9100)     │    │   (8080)     │    │   (9115)     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 日常運維操作

### 1. 服務狀態檢查

#### 檢查所有服務狀態
```bash
# 檢查Docker容器狀態
docker ps -a | grep cbsc

# 檢查服務健康狀態
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3010/api/health  # Grafana
curl http://localhost:9093/-/healthy  # AlertManager
```

#### 查看服務日誌
```bash
# Prometheus日誌
docker logs cbsc-prometheus -f

# Grafana日誌
docker logs cbsc-grafana -f

# AlertManager日誌
docker logs cbsc-alertmanager -f
```

### 2. 數據備份

#### Prometheus數據備份
```bash
#!/bin/bash
# 備份Prometheus數據
BACKUP_DIR="/backup/prometheus/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

docker cp cbsc-prometheus:/prometheus "$BACKUP_DIR"
tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

# 保留最近30天的備份
find /backup/prometheus -name "*.tar.gz" -mtime +30 -delete
```

#### Grafana配置備份
```bash
#!/bin/bash
# 備份Grafana配置和儀表板
BACKUP_DIR="/backup/grafana/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

docker cp cbsc-grafana:/var/lib/grafana "$BACKUP_DIR"
docker cp cbsc-grafana:/etc/grafana "$BACKUP_DIR"
tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"
```

### 3. 配置更新

#### 更新Prometheus配置
```bash
# 編輯配置文件
vim monitoring/prometheus/prometheus.yml

# 重新加載配置
curl -X POST http://localhost:9090/-/reload

# 驗證配置
curl http://localhost:9090/api/v1/status/config
```

#### 更新Grafana數據源
```bash
# 通過API更新數據源（需認證）
curl -X POST \
  http://admin:password@localhost:3010/api/datasources \
  -H 'Content-Type: application/json' \
  -d @datasource-config.json
```

### 4. 性能監控

#### 檢查Prometheus性能
```bash
# 查看Prometheus指標
curl http://localhost:9090/metrics | grep prometheus_

# 查查數據庫狀態
curl http://localhost:9090/api/v1/status/tsdb
```

#### 檢查Grafana性能
```bash
# 查看Grafana指標
curl http://localhost:3010/metrics

# 查看用戶會話
curl http://localhost:3010/api/users
```

## 告警處理流程

### 1. 告警級別定義

#### Critical (P0) - 立即響應
- 服務完全宕機
- 數據庫連接失敗
- 安全事件
- 響應時間: < 5分鐘

#### Warning (P1) - 1小時內響應
- 高錯誤率 (>5%)
- 響應時間過長
- 資源使用率高
- 響應時間: < 1小時

#### Info (P2) - 24小時內響應
- 性能趨勢異常
- 容量預警
- 配置更新提醒
- 響應時間: < 24小時

### 2. 告警處理流程

```
告警觸發 → 分類定級 → 通知相關人員 → 問題定位 → 實施修復 → 驗證恢復 → 根因分析 → 改進措施
```

#### 處理步驟

1. **接收告警**
   - 檢查郵件/Slack/SMS通知
   - 確認告警詳情和影響範圍

2. **初步評估**
   - 判斷告警級別和緊急程度
   - 確定影響的服務和用戶

3. **問題定位**
   - 登錄相應監控系統
   - 分析日誌和指標
   - 確定問題根因

4. **實施修復**
   - 按照預案執行修復
   - 如無預案，按最佳實踐處理
   - 記錄操作過程

5. **驗證恢復**
   - 確認服務恢復正常
   - 檢查關鍵指標
   - 驗證用戶功能

6. **根因分析**
   - 深入分析問題原因
   - 評估影響程度
   - 制定預防措施

7. **改進措施**
   - 更新監控規則
   - 完善自動化腳本
   - 改進流程文檔

### 3. 告警預案

#### 服務宕機預案
1. **立即檢查**
   ```bash
   # 檢查容器狀態
   docker ps | grep cbsc

   # 檢查服務端口
   netstat -tlnp | grep :3004
   ```

2. **重啟服務**
   ```bash
   # 重啟API服務
   cd /path/to/cbsc && docker-compose restart api

   # 重啟監控服務
   cd monitoring && docker-compose restart
   ```

3. **擴容處理**
   ```bash
   # 擴展API實例
   docker-compose up -d --scale api=2
   ```

#### 高錯誤率預案
1. **分析錯誤日誌**
   ```bash
   # 查看API錯誤日誌
   docker logs cbsc-api | grep ERROR | tail -100

   # 分析錯誤模式
   grep "ERROR" /var/log/cbsc/api.log | awk '{print $NF}' | sort | uniq -c
   ```

2. **檢查依賴服務**
   ```bash
   # 檢查數據庫連接
   docker exec cbsc-api python -c "from db import engine; print(engine.execute('SELECT 1').scalar())"

   # 檢查緩存服務
   docker exec cbsc-api redis-cli ping
   ```

3. **性能優化**
   ```bash
   # 增加API實例
   docker-compose up -d --scale api=3

   # 調整資源限制
   docker-compose up -d --memory=2g api
   ```

## 故障排查指南

### 1. 常見問題診斷

#### Prometheus無法啟動
**症狀**: Prometheus容器啟動失敗或無法訪問

**排查步驟**:
```bash
# 1. 檢查配置文件語法
docker run --rm -v $(pwd)/prometheus:/etc/prometheus \
  prom/prometheus:latest --config.file=/etc/prometheus/prometheus.yml --dry-run

# 2. 檢查端口佔用
netstat -tlnp | grep 9090

# 3. 查看詳細錯誤
docker logs cbsc-prometheus

# 4. 檢查磁盤空間
df -h /var/lib/docker/volumes/

# 5. 檢查權限
ls -la monitoring/data/prometheus/
```

**常見解決方案**:
- 修復配置文件語法錯誤
- 釋放被佔用端口
- 清理磁盤空間
- 調整文件權限
- 重新創建數據卷

#### Grafana無法連接數據源
**症狀**: Grafana儀表板顯示"數據源錯誤"

**排查步驟**:
```bash
# 1. 檢查Prometheus連通性
curl http://prometheus:9090/api/v1/query?query=up

# 2. 檢查Grafana網絡
docker exec cbsc-grafana ping prometheus

# 3. 驗證數據源配置
curl -u admin:password \
  http://localhost:3010/api/datasources/1

# 4. 查看Grafana日誌
docker logs cbsc-grafana | grep -i datasource
```

**常見解決方案**:
- 更新數據源URL
- 檢查網絡連接
- 重啟Grafana服務
- 驗證認證配置

#### 告警未觸發
**症狀**: 明顯異常但未收到告警

**排查步驟**:
```bash
# 1. 檢查告警規則
curl http://localhost:9090/api/v1/rules

# 2. 驗證規則表達式
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up{job="cbsc-api"}==0'

# 3. 檢查AlertManager配置
curl http://localhost:9093/api/v1/status

# 4. 查看告警狀態
curl http://localhost:9093/api/v1/alerts
```

**常見解決方案**:
- 調整告警閾值
- 修復規則表達式
- 重啟AlertManager
- 檢查通知配置

### 2. 性能問題診斷

#### Prometheus查詢慢
**症狀**: Grafana儀表板加載緩慢或超時

**排查步驟**:
```bash
# 1. 檢查查詢性能
curl -G http://localhost:9090/api/v1/query_range \
  --data-urlencode 'query=rate(http_requests_total[5m])' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T01:00:00Z' \
  --data-urlencode 'step=15'

# 2. 檢查數據庫狀態
curl http://localhost:9090/api/v1/status/tsdb

# 3. 監控資源使用
docker stats cbsc-prometheus

# 4. 分析慢查詢
grep "query=.*slow" /var/log/prometheus/prometheus.log
```

**優化方案**:
- 添加記錄規則預計算
- 調整採樣間隔
- 增加內存限制
- 優化查詢表達式

#### Grafana響應慢
**症狀**: 儀表板加載和查詢緩慢

**排查步驟**:
```bash
# 1. 檢查Grafana性能
curl http://localhost:3010/metrics | grep grafana_

# 2. 分析慢查詢
curl http://localhost:3010/api/datasources/proxy/1/api/v1/query_range \
  -d 'query=up&start=now-1h&end=now&step=15'

# 3. 檢查會話數量
curl http://localhost:3010/api/admin/stats

# 4. 監控資源使用
docker stats cbsc-grafana
```

**優化方案**:
- 啟用查詢緩存
- 調整併發限制
- 優化儀表板查詢
- 增加實例數量

### 3. 數據問題診斷

#### 指標缺失
**症狀**: 預期指標不出現在儀表板中

**排查步驟**:
```bash
# 1. 檢查目標服務狀態
curl http://localhost:9090/api/v1/targets

# 2. 驗證指標端點
curl http://localhost:3004/metrics

# 3. 檢查標籤匹配
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up{job="cbsc-api"}'

# 4. 查看最近的採樣
curl http://localhost:9090/api/v1/query \
  --data-urlencode 'query=time() - up_timestamp'
```

**常見解決方案**:
- 檢查服務發現配置
- 驗證指標暴露
- 調整採樣配置
- 檢查網絡連通性

## 性能優化

### 1. Prometheus優化

#### 配置優化
```yaml
# prometheus.yml
global:
  # 調整採樣間隔
  scrape_interval: 15s
  evaluation_interval: 15s

  # 啟用壓縮
  enable_compression: true

# 存儲優化
storage:
  tsdb:
    # 調整保留時間
    retention.time: 30d

    # 啟用WAL壓縮
    wal_compression: true

    # 調整內存映射
    max_memory_chunks: 1048576
```

#### 查詢優化
```yaml
# recording-rules.yml
groups:
- name: cbsc-recording-rules
  interval: 30s
  rules:
  # 預計算常用指標
  - record: cbsc:http_requests:rate5m
    expr: rate(http_requests_total{job=~"cbsc-.*"}[5m])

  # 預計算錯誤率
  - record: cbsc:error_rate:5m
    expr: rate(http_requests_total{job=~"cbsc-.*",status_code=~"5.."}[5m]) /
       rate(http_requests_total{job=~"cbsc-.*"}[5m])
```

### 2. Grafana優化

#### 緩存配置
```ini
# grafana.ini
[database]
# 啟用查詢緓存
cache_provider = redis

[redis]
# Redis緩存配置
addr = 127.0.0.1:6379
db = 1
password =

[explore]
# 啟用查詢歷史
enable_history = true
```

#### 儀表板優化
- 使用相對時間範圍
- 減少查詢數量
- 使用記錄規則
- 啟用面板緩存

### 3. 系統優化

#### 資源配置
```yaml
# docker-compose.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  grafana:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

#### 存儲優化
```bash
# 使用SSD存儲
mkfs.ext4 /dev/nvme0n1
mount -o noatime /dev/nvme0n1 /data/prometheus

# 配置日誌輪轉
vim /etc/logrotate.d/prometheus
```

## 容量規劃

### 1. 存儲容量規劃

#### Prometheus數據量估算
```
原始數據量 = 指標數量 × 採樣頻率 × 數據點大小 × 保留時間

假設：
- 指標數量：100,000
- 採樣頻率：15秒
- 數據點大小：2字節
- 保留時間：30天

計算：
原始數據量 = 100,000 × 3600 × 24 × 30 / 15 × 2 = 345.6GB
壓縮後 ≈ 100GB
```

#### 存儲配置建議
```yaml
# 不同環境的存儲配置
development:
  retention: 7d
  storage: 50GB

testing:
  retention: 15d
  storage: 200GB

production:
  retention: 30d
  storage: 1TB

# 遠程存儲配置
remote_write:
  - url: "http://thanos-receive:19291/api/v1/receive"
    queue_config:
      max_samples_per_send: 2000
      max_shards: 200
```

### 2. 計算資源規劃

#### CPU需求估算
```
採樣目標數 × 0.001 = CPU核心數

假設：
- 採樣目標：1000
- 計算：1000 × 0.001 = 1核心

建議配置：
- 基礎配置：2核心
- 推薦配置：4核心
- 高負載：8核心
```

#### 內存需求估算
```
基礎內存 = 1GB
指標內存 = 指標數量 × 0.001GB
查詢內存 = 併發查詢數 × 0.5GB

總計 = 基礎內存 + 指標內存 + 查詢內存

示例：
基礎內存 = 1GB
指標內存 = 100,000 × 0.001GB = 100GB
查詢內存 = 10 × 0.5GB = 5GB
總計 ≈ 16GB（考慮壓縮）
```

### 3. 網絡帶寬規劃

#### 帶寬需求計算
```
網絡流量 = 採樣目標數 × 採樣頻率 × 響應大小

假設：
- 採樣目標：1000
- 採樣頻率：15秒
- 平均響應大小：20KB

計算：
網絡流量 = 1000 × 3600 × 20KB / 15 = 4.8GB/hour = 115GB/day

建議帶寬：1Gbps
```

## 應急預案

### 1. 服務完全宕機

#### 恢復步驟
```bash
# 1. 快速診斷
docker ps -a
docker logs cbsc-api --tail=100

# 2. 重啟服務
cd /path/to/cbsc
docker-compose down
docker-compose up -d

# 3. 驗證服務
curl http://localhost:3004/health
curl http://localhost:3010/api/health

# 4. 檢查監控
curl http://localhost:9090/api/v1/query?query=up
```

#### 降級方案
```bash
# 關閉非核心功能
curl -X POST http://localhost:3004/api/v1/maintenance/enable

# 啟用緩存模式
curl -X POST http://localhost:3004/api/v1/cache/force-enable

# 限制API速率
docker-compose up -d --scale api=1
```

### 2. 數據庫故障

#### 主從切換
```bash
# 檢查主庫狀態
docker exec postgres pg_isready

# 啟動從庫
docker-compose up -d postgres-slave

# 更新連接配置
vim config/database.yml
```

#### 數據恢復
```bash
# 從備份恢復
pg_restore -h localhost -U postgres -d cbsc_db backup.sql

# 驗證數據完整性
docker exec postgres psql -U postgres -d cbsc_db -c "SELECT COUNT(*) FROM strategies;"
```

### 3. 監控系統故障

#### Prometheus故障恢復
```bash
# 1. 備份當前數據
docker cp cbsc-prometheus:/prometheus /tmp/prometheus-backup

# 2. 重新初始化
docker-compose down prometheus
rm -rf data/prometheus/*
docker-compose up -d prometheus

# 3. 恢復配置
docker cp /tmp/prometheus-backup/prometheus.yml cbsc-prometheus:/etc/prometheus/
docker exec cbsc-prometheus kill -HUP 1
```

#### Grafana故障恢復
```bash
# 1. 備份配置
docker cp cbsc-grafana:/etc/grafana /tmp/grafana-backup

# 2. 重置數據庫
docker-compose down grafana
docker volume rm grafana_data
docker-compose up -d grafana

# 3. 恢復配置
docker cp /tmp/grafana-backup/* cbsc-grafana:/etc/grafana/
docker-compose restart grafana
```

## 聯繫方式

### 運維團隊
- **值班電話**: +852-XXXX-XXXX
- **緊急郵箱**: oncall@cbsc.com
- **Slack頻道**: #cbsc-oncall

### 相關團隊
- **DevOps團隊**: devops@cbsc.com
- **開發團隊**: dev@cbsc.com
- **安全團隊**: security@cbsc.com
- **數據庫團隊**: dba@cbsc.com

### 外部支持
- **Prometheus社區**: https://prometheus.io/community/
- **Grafana社區**: https://community.grafana.com/
- **雲服務商**: 阿里雲/騰訊雲/AWS技術支持

### 文檔資源
- **監控文檔**: https://docs.cbsc.com/monitoring
- **API文檔**: http://localhost:3004/docs
- **故障知識庫**: https://kb.cbsc.com/incidents

---

**文檔版本**: v2.0
**最後更新**: 2025-01-17
**維護負責人**: CBSC DevOps Team