# Security Implementation Guide
安全實施指南

## 概述

本文檔描述了CBSC量化交易策略管理系統中實施的安全功能，包括API限流、安全審計日誌和異常檢測系統。

## 安全功能架構

### 1. API限流系統 (API Rate Limiting)

#### 位置：`src/middleware/rate_limit_middleware.py`

#### 功能特性：
- **Redis基礎的滑動窗口限流**：使用Redis存儲限流狀態，支持分佈式環境
- **用戶級和IP級限流**：支持基於用戶ID和IP地址的獨立限流
- **動態限流策略**：根據用戶層級（basic/premium/institutional/admin）調整限流參數
- **違規懲罰機制**：對超限行為實施漸進式懲罰
- **特殊端點限流**：對認證、導出等敏感端點設置更嚴格的限制

#### 配置參數：
```python
# 用戶層級限流配置
user_limits = {
    'basic': {
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
        'requests_per_day': 10000
    },
    'premium': {
        'requests_per_minute': 120,
        'requests_per_hour': 2400,
        'requests_per_day': 24000
    },
    'institutional': {
        'requests_per_minute': 300,
        'requests_per_hour': 6000,
        'requests_per_day': 60000
    },
    'admin': {
        'requests_per_minute': 1000,
        'requests_per_hour': 20000,
        'requests_per_day': 200000
    }
}
```

#### API端點：
- `GET /api/v1/security/rate-limit/status?identifier={user_id|ip}` - 查詢限流狀態

### 2. 安全審計日誌系統 (Security Audit Logging)

#### 位置：`src/security/audit_logger.py`

#### 功能特性：
- **全面的審計事件記錄**：覆蓋認證、授權、數據訪問、系統事件等
- **SQLite + Redis混合存儲**：本地SQLite存儲詳細記錄，Redis提供快速索引
- **事件嚴重性分級**：LOW/MEDIUM/HIGH/CRITICAL四個級別
- **合規報告生成**：支持生成安全、訪問、數據等各類合規報告
- **自動數據清理**：可配置的數據保留策略

#### 審計事件類型：
- 認證事件：登錄、登出、密碼修改、MFA設置
- 授權事件：角色變更、權限授予/拒絕、特權升級
- 數據訪問事件：數據讀取、創建、更新、刪除、導出
- 系統事件：啟動/關機、配置變更、備份/恢復
- 安全事件：安全違規、可疑活動、入侵嘗試

#### API端點：
- `GET /api/v1/security/audit/events` - 獲取審計事件
- `GET /api/v1/security/audit/user/{user_id}/summary` - 用戶活動摘要
- `POST /api/v1/security/compliance/report` - 生成合規報告

### 3. 異常檢測系統 (Anomaly Detection)

#### 位置：`src/security/anomaly_detector.py`

#### 功能特性：
- **用戶行為基線建立**：學習和跟蹤正常用戶行為模式
- **實時異常檢測**：檢測異常登錄模式、訪問行為、數據使用
- **多維度風險評估**：綜合考慮多個因素計算用戶風險分數
- **自動響應機制**：對高危異常觸發自動防護措施
- **攻擊模式識別**：識別暴力破解、DDoS等攻擊模式

#### 檢測的異常類型：
- 多次失敗登錄嘗試
- 異常時間/IP登錄
- 數據訪問量異常激增
- 併發會話異常
- 地理位置異常

#### API端點：
- `GET /api/v1/security/anomalies/recent` - 獲取最近異常
- `GET /api/v1/security/risk/assessment/{user_id}` - 用戶風險評估

### 4. 安全審計中間件 (Security Audit Middleware)

#### 位置：`src/middleware/security_audit_middleware.py`

#### 功能特性：
- **全面的請求記錄**：記錄所有HTTP請求的詳細信息
- **可疑模式檢測**：檢測SQL注入、XSS、命令注入等攻擊模式
- **IP臨時封禁**：對惡意IP實施自動封禁
- **安全頭部添加**：自動添加安全相關的HTTP頭部
- **會話跟蹤**：跟蹤用戶會話活動

#### 檢測的安全威脅：
- SQL注入模式
- XSS攻擊模式
- 路徑遍歷攻擊
- 命令注入
- 暴力破解攻擊
- 可疑User-Agent

## 部署指南

### 1. 依賴要求

```bash
# Python依賴
pip install redis fastapi uvicorn[standard] sqlalchemy
```

### 2. 環境配置

```env
# Redis配置
REDIS_URL=redis://localhost:6379

# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost/cbsc_db

# 安全配置
JWT_SECRET=your-jwt-secret
APP_SECRET_KEY=your-app-secret-key
```

### 3. Redis配置建議

```redis.conf
# 持久化配置
save 900 1
save 300 10
save 60 10000

# 內存配置
maxmemory 2gb
maxmemory-policy allkeys-lru

# 網絡配置
protected-mode yes
requirepass your-redis-password
```

### 4. 啟動服務

```bash
# 啟動Redis
redis-server /path/to/redis.conf

# 啟動應用
cd src
python main.py
```

## 監控和維護

### 1. 安全指標監控

通過以下API端點獲取安全指標：
- `GET /api/v1/security/metrics/security` - 安全指標總覽

關鍵指標包括：
- 總事件數
- 失敗登錄次數
- 安全違規次數
- 可疑活動次數
- 獨特用戶/IP數
- 高風險事件數

### 2. 日誌管理

審計日誌位置：
- SQLite數據庫：`audit_logs.db`
- Redis緩存：配置的Redis實例

日誌清理：
```python
# 清理90天前的日誌
await audit_logger.cleanup_old_logs(retention_days=90)
```

### 3. 警報配置

建議配置以下警報：
- 高風險異常檢測
- IP封禁事件
- 系統錯誤率超過閾值
- 資源使用率異常

## 最佳實踐

### 1. 限流配置

- 根據業務需求調整各層級用戶的限流參數
- 對關鍵端點設置更嚴格的限制
- 定期審查和更新限流策略

### 2. 審計日誌

- 確保所有敏感操作都有審計記錄
- 定期備份審計日誌
- 實施日誌完整性檢查

### 3. 異常檢測

- 定期更新異常檢測規則
- 調整檢測閾值以平衡準確率和誤報率
- 實施人工審核流程驗證高風險告警

### 4. 安全更新

- 定期更新依賴包
- 監控安全漏洞信息
- 及時應用安全補丁

## 故障排除

### 常見問題

1. **Redis連接失敗**
   - 檢查Redis服務狀態
   - 驗證連接配置
   - 檢查網絡連通性

2. **限流不生效**
   - 確認中間件正確加載
   - 檢查Redis連接
   - 驗證用戶識別邏輯

3. **審計日誌缺失**
   - 檢查數據庫連接
   - 驗證寫入權限
   - 查看錯誤日誌

### 調試命令

```bash
# 檢查Redis連接
redis-cli -u your-redis-url ping

# 查看限流狀態
curl "http://localhost:8000/api/v1/security/rate-limit/status?identifier=test_user"

# 獲取最近異常
curl "http://localhost:8000/api/v1/security/anomalies/recent?limit=10"
```

## 聯系信息

如有問題或建議，請聯系安全團隊：
- 郵箱：security@cbsc.com
- 內部工單系統：創建安全類工單