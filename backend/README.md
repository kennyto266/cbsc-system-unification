# CBSC WebSocket 後端服務

這是 CBSC 量化交易系統的 WebSocket 後端服務，提供實時數據推送功能。

## 功能特性

- **實時數據推送**: 支持多個數據頻道的實時推送
- **多客戶端支持**: 同時服務多個前端連接
- **自動重連**: 客戶端斷開自動重連機制
- **心跳檢測**: 定期 ping/pong 確保連接穩定
- **頻道訂閱**: 客戶端可選擇性訂閱特定數據頻道

## 支持的數據頻道

1. `strategy_performance` - 策略表現數據（每5秒更新）
2. `market_data` - 實時市場數據（每2秒更新）
3. `hibor_rates` - HIBOR 利率數據（每30秒更新）
4. `cbsc_contracts` - 牛熊證合約數據（每10秒更新）
5. `government_data` - 政府宏觀數據（每60秒更新）
6. `system_status` - 系統狀態（按需推送）

## 快速開始

### 1. 安裝依賴

```bash
# 安裝 Python 依賴
pip install -r requirements.txt
```

### 2. 啟動服務器

#### Windows:
```bash
# 使用批處理文件
start_server.bat
```

#### Linux/Mac:
```bash
# 使用 Shell 腳本
chmod +x start_server.sh
./start_server.sh
```

#### 直接運行:
```bash
python main.py
```

服務器將在端口 3004 啟動，WebSocket 端點：`ws://localhost:3004/ws`

## API 端點

### WebSocket
- **端點**: `/ws`
- **協議**: WebSocket
- **用途**: 實時數據推送

### HTTP
- **健康檢查**: `GET /health`
- **系統狀態**: `GET /api/status`

## WebSocket 消息協議

### 客戶端到服務器

#### 訂閱頻道
```json
{
  "type": "subscribe",
  "channel": "strategy_performance"
}
```

#### 取消訂閱
```json
{
  "type": "unsubscribe",
  "channel": "market_data"
}
```

#### 心跳響應
```json
{
  "type": "pong"
}
```

### 服務器到客戶端

#### 訂閱確認
```json
{
  "type": "subscribed",
  "channel": "strategy_performance",
  "message": "Successfully subscribed to strategy_performance"
}
```

#### 數據推送
```json
{
  "type": "data",
  "channel": "strategy_performance",
  "timestamp": "2025-12-16T03:00:00Z",
  "payload": {
    "strategies": [
      {
        "name": "DirectRSIStrategy",
        "sharpe_ratio": 1.23,
        "max_drawdown": 0.15,
        "total_return": 0.25,
        "win_rate": 0.68,
        "signal_count": 150,
        "status": "enabled"
      }
    ]
  }
}
```

## 前端集成

### 環境變量配置

在前端項目的 `.env.local` 文件中添加：

```env
NEXT_PUBLIC_WS_URL=ws://localhost:3004/ws
```

### 使用示例

```javascript
import { websocketService, WS_CHANNELS } from '@/lib/websocket';

// 連接並訂閱策略數據
await websocketService.connect();
websocketService.subscribe(WS_CHANNELS.STRATEGY_PERFORMANCE, (data) => {
  console.log('收到策略數據:', data);
});
```

## 測試

使用提供的測試腳本：

```bash
# 回到項目根目錄
cd CODEX--

# 運行測試
python test-websocket.py
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3004"]
```

### 系統服務部署

創建 systemd 服務文件 `/etc/systemd/system/cbsc-websocket.service`：

```ini
[Unit]
Description=CBSC WebSocket Server
After=network.target

[Service]
Type=simple
User=cbsc
WorkingDirectory=/opt/cbsc/backend
ExecStart=/opt/cbsc/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 故障排除

### 連接被拒絕
- 確保服務器在端口 3004 運行
- 檢查防火牆設置

### 數據不更新
- 確認客戶端已訂閱正確的頻道
- 查看服務器日誌確認數據生成

### 性能問題
- 監控連接數，避免過多連接
- 考慮增加數據推送間隔

## 開發

### 添加新數據頻道

1. 在 `DataGenerator` 類中添加生成方法
2. 在 `data_pusher` 任務中添加推送邏輯
3. 更新支持的頻道列表

### 自定義數據格式

修改 `DataGenerator` 中的數據結構，確保與前端一致。

## 監控

服務器提供健康檢查端點，可用於監控：

```bash
curl http://localhost:3004/health
```

## 許可證

MIT License