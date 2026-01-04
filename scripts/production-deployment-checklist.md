# 🚀 VectorBT 多進程回測系統生產部署檢查清單

## 📋 部署前準備

### 🔒 安全配置
- [ ] 更新所有默認密碼
  - [ ] PostgreSQL 密碼 (`.env.prod` `POSTGRES_PASSWORD`)
  - [ ] Redis 密碼 (`.env.prod` `REDIS_PASSWORD`)
  - [ ] InfluxDB 密碼 (`.env.prod` `INFLUXDB_PASSWORD`)
  - [ ] JWT 密鑰 (`.env.prod` `JWT_SECRET`)
  - [ ] 應用密鑰 (`.env.prod` `SECRET_KEY`)
  - [ ] Grafana 密碼 (`.env.prod` `GRAFANA_PASSWORD`)

- [ ] 配置 SSL/TLS 證書
  - [ ] 生成或獲取 SSL 證書
  - [ ] 將證書放置在 `./ssl/` 目錄
  - [ ] 更新 `.env.prod` 中的域名配置

- [ ] 配置防火牆規則
  - [ ] 開放必要端口: 80, 443, 3000-3005, 5432, 6379, 8086, 9090, 3001
  - [ ] 限制資料庫端口訪問 (僅內部網絡)
  - [ ] 配置入侵檢測和防護

### 🖥️ 系統要求
- [ ] **硬體配置檢查**
  - [ ] CPU: 8核心或以上
  - [ ] 內存: 32GB 或以上
  - [ ] 存儲: 500GB SSD 或以上
  - [ ] 網絡: 1Gbps 帶寬

- [ ] **軟件環境檢查**
  - [ ] Docker 20.10+ 已安裝
  - [ ] Docker Compose 2.0+ 已安裝
  - [ ] Git 已安裝和配置
  - [ ] OpenSSH 已配置

- [ ] **網絡配置檢查**
  - [ ] 靜態 IP 地址已配置
  - [ ] 域名 DNS 已正確指向
  - [ ] 反向代理配置就緒

## 📦 部署執行

### 1️⃣ 環境準備
```bash
# 複製生產環境配置
cp .env.prod .env

# 驗證配置文件
./scripts/validate-production-config.sh

# 創建必要目錄
mkdir -p logs ssl uploads static
chmod 755 logs ssl uploads static
```

### 2️⃣ 啟動服務
```bash
# 拉取最新鏡像
docker-compose -f docker-compose.prod.yml pull

# 構建和啟動服務
docker-compose -f docker-compose.prod.yml up -d --build

# 檢查服務狀態
docker-compose -f docker-compose.prod.yml ps
```

### 3️⃣ 數據庫初始化
```bash
# 等待資料庫啟動
sleep 30

# 運行資料庫遷移
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# 創建初始管理員用戶
docker-compose -f docker-compose.prod.yml exec backend python scripts/create-admin.py
```

### 4️⃣ 服務驗證
```bash
# 健康檢查
curl -f http://localhost/api/health || echo "Backend health check failed"
curl -f http://localhost/health || echo "Nginx health check failed"

# 檢查日誌
docker-compose -f docker-compose.prod.yml logs --tail=50 backend
docker-compose -f docker-compose.prod.yml logs --tail=50 postgres
docker-compose -f docker-compose.prod.yml logs --tail=50 redis
```

## 🔍 部署後驗證

### 🌐 Web 應用驗證
- [ ] 前端應用可正常訪問: `https://your-domain.com`
- [ ] 後端 API 正常響應: `https://your-domain.com/api/docs`
- [ ] WebSocket 連接正常工作
- [ ] 用戶註冊和登錄功能正常
- [ ] 策略配置和回測功能正常

### 📊 監控系統驗證
- [ ] Grafana 儀表板可訪問: `https://your-domain.com/grafana`
- [ ] Prometheus 指標收集正常: `http://your-domain.com:9090`
- [ ] 系統指標監控正常運行
- [ ] 應用指標監控正常運行
- [ ] 告警規則已配置並測試

### 🗄️ 數據庫驗證
- [ ] PostgreSQL 連接正常
- [ ] Redis 緩存服務正常
- [ ] InfluxDB 時序數據庫正常
- [ ] 數據備份配置已設置
- [ ] 數據持久化存儲正常

### 🚀 性能驗證
- [ ] 基本功能響應時間 < 2秒
- [ ] 並發用戶測試通過
- [ ] 大數據量處理測試通過
- [ ] 內存使用在預期範圍內
- [ ] CPU 使用率在合理範圍內

## 📈 監控和告警配置

### 🎯 關鍵指標監控
- [ ] **系統指標**
  - [ ] CPU 使用率 > 90% 告警
  - [ ] 內存使用率 > 85% 告警
  - [ ] 磁盤使用率 > 80% 告警
  - [ ] 網絡延遲 > 100ms 告警

- [ ] **應用指標**
  - [ ] API 錯誤率 > 5% 告警
  - [ ] API 響應時間 > 1s 告警
  - [ ] WebSocket 連接數異常告警
  - [ ] 回測任務失敗率 > 10% 告警

- [ ] **業務指標**
  - [ ] 活躍用戶數異常變化告警
  - [ ] 回測任務處理時間異常告警
  - [ ] 策略執行成功率監控

### 📧 告警通知配置
- [ ] 郵件通知已配置
- [ ] Slack/Teams 通知已配置
- [ ] 短信通知已配置 (可選)
- [ ] 告警級別分類已設置

## 🔄 維護和備份

### 📅 定期維護任務
- [ ] **每日任務**
  - [ ] 檢查系統日誌錯誤
  - [ ] 監控磁盤空間使用
  - [ ] 驗證備份任務執行
  - [ ] 檢查性能指標異常

- [ ] **每週任務**
  - [ ] 執行完整系統備份
  - [ ] 更新安全補丁
  - [ ] 檢查 SSL 證書有效期
  - [ ] 分析性能趨勢

- [ ] **每月任務**
  - [ ] 執行災難恢復測試
  - [ ] 更新文檔和操作手冊
  - [ ] 優化系統配置
  - [ ] 檢查和清理日誌文件

### 💾 備份策略
- [ ] 數據庫自動備份已配置
- [ ] 配置文件版本控制已設置
- [ ] 備份存儲異地保護已配置
- [ ] 備份恢復流程已測試

## 🚨 應急響應程序

### 🆘 緊急聯繫信息
- [ ] 技術負責人聯繫方式已記錄
- [ ] 運維團隊聯繫方式已記錄
- [ ] 第三方技術支持聯繫方式已記錄
- [ ] 應急響應流程已制定

### 🛠️ 故障處理程序
- [ ] 服務重啟程序已文檔化
- [ ] 數據恢復程序已測試
- [ ] 降級方案已準備
- [ ] 滾動更新程序已測試

---

## ✅ 部署完成確認

部署完成後，請在下方確認所有項目：

- [ ] 所有安全配置已正確設置
- [ ] 所有服務正常啟動運行
- [ ] 所有監控和告警已配置
- [ ] 所有備份策略已實施
- [ ] 所有文檔已更新完成
- [ ] 團隊培訓已完成
- [ ] 用戶驗收測試通過

**部署日期**: _______________
**部署人員**: _______________
**審核人員**: _______________

---
*此檢查清單應與版本控制系統一起維護，每次部署時更新*