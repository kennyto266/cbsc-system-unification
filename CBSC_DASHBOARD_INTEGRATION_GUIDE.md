# CBSC 牛熊证 Dashboard 集成指南

## 概述

本指南说明如何将港交所 CBSC（牛熊证）数据集成到 http://localhost:3001/dashboard 中，实现实时市场监控和数据分析功能。

## 功能特性

### 1. 市场情绪指标
- 恐惧贪婪指数（Fear & Greed Index）
- 牛熊比率（Bull/Bear Ratio）
- 已实现波动率（Realized Volatility）
- RSI 技术指标
- 综合情绪评分（0-100）

### 2. 牛熊证前十名排行
- 实时更新的牛证（看涨）排行
- 实时更新的熊证（看跌）排行
- 显示价格、行使价、杠杆、成交量等关键信息
- 支持涨跌幅显示

### 3. 市场情绪趋势图表
- 支持 30 天历史数据查看
- 可切换不同指标（恐惧贪婪、牛熊比率、波动率、成交量）
- 实时更新的 Canvas 图表

### 4. 实时数据同步
- 每 30 秒自动刷新数据
- WebSocket 实时推送（需后端支持）
- 数据加载状态提示

## 技术架构

### 后端 API（Python FastAPI）

#### 1. CBSC 数据 API (`src/api/cbsc_data_api.py`)
```python
# 主要端点：
GET /api/cbsc/market-sentiment      # 获取市场情绪指标
GET /api/cbsc/top-contracts         # 获取牛熊证前十名
GET /api/cbsc/historical-data       # 获取历史数据
GET /api/cbsc/dashboard-summary     # 获取 Dashboard 综合数据
```

#### 2. 数据源
- 数据文件：`acquired_data/cbsc_real_data_20251205_205342.csv`
- 自动解析 CSV 文件并生成实时数据
- 支持数据格式转换和计算

### 前端组件（React TypeScript）

#### 1. 类型定义 (`src/types/cbsc.ts`)
```typescript
interface MarketSentiment {
  fear_greed_index: number;
  bull_bear_ratio: number;
  realized_volatility: number;
  rsi_signal: number;
  sentiment_score: number;
  sentiment_label: string;
}
```

#### 2. 服务层 (`src/services/cbscService.ts`)
- HTTP API 调用封装
- WebSocket 实时数据订阅
- 错误处理和重试机制

#### 3. UI 组件
- `MarketSentimentCard.tsx` - 市场情绪指标卡片
- `TopContractsTable.tsx` - 牛熊证前十名表格
- `SentimentTrendChart.tsx` - 市场情绪趋势图表
- `CBSCDashboard.tsx` - 综合仪表板组件
- `CBSCTabPage.tsx` - 标签页容器

## 安装步骤

### 1. 后端配置

确保后端已运行在 http://localhost:3001

```bash
# 启动 API 服务
cd src/api
python -m uvicorn main:app --reload --port 3001
```

### 2. 前端配置

确保前端开发服务器运行：

```bash
cd unified-dashboard
npm run dev
```

### 3. 验证 API 端点

访问以下 URL 验证 API 是否正常工作：

- http://localhost:3001/api/cbsc/market-sentiment
- http://localhost:3001/api/cbsc/top-contracts
- http://localhost:3001/api/cbsc/dashboard-summary

### 4. 访问 Dashboard

打开浏览器访问：http://localhost:3000/dashboard

点击 "CBSC牛熊证" 标签页查看集成功能。

## 数据格式说明

### CBSC CSV 数据格式

```csv
Date,HSIF_Close,HSIF_Return,Bull_Price,Bear_Price,Bull_Bear_Ratio,Fear_Greed_Index,Realized_Volatility,RSI_Signal,Volume
2024-01-01,18000,0.01,0.01,20.5,1.25,65,0.25,55,1000000
...
```

### 市场情绪计算逻辑

1. **恐惧贪婪指数**：0-100 分数
   - 0-25：极度恐惧
   - 25-45：恐惧
   - 45-60：中性
   - 60-75：贪婪
   - 75-100：极度贪婪

2. **牛熊比率**：
   - >1：市场偏多
   - <1：市场偏空

3. **波动率分级**：
   - >0.3：高波动
   - 0.2-0.3：中等波动
   - <0.2：低波动

## 自定义配置

### 1. 修改数据源

在 `src/api/cbsc_data_api.py` 中修改：

```python
# 数据文件路径
LATEST_DATA_FILE = DATA_DIR / "your_custom_data_file.csv"
```

### 2. 调整刷新频率

在 `src/components/cbsc/CBSCDashboard.tsx` 中修改：

```typescript
// 设置定时刷新间隔（毫秒）
const refreshInterval = setInterval(fetchInitialData, 30000); // 30秒
```

### 3. 自定义主题颜色

在组件中修改 Tailwind CSS 类名：

```typescript
// 例如，修改恐惧贪婪指数的颜色
const getSentimentColor = (score: number): string => {
  if (score >= 75) return 'text-purple-600'; // 改为紫色
  // ...
};
```

## 故障排除

### 常见问题

1. **API 无法访问**
   - 检查后端服务是否运行在 3001 端口
   - 查看 API 日志：`logs/api.log`

2. **前端无法加载数据**
   - 检查浏览器控制台错误
   - 确认 CORS 配置正确

3. **数据显示异常**
   - 验证 CSV 文件格式
   - 检查数据文件路径

4. **WebSocket 连接失败**
   - 确保 WebSocket 服务已启动
   - 检查防火墙设置

### 调试技巧

1. **启用调试日志**

```python
# 在 API 端添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **查看网络请求**

使用浏览器开发者工具查看 API 请求和响应。

3. **检查数据格式**

```python
# 添加数据验证
print(df.head())
print(df.info())
```

## 性能优化建议

1. **数据缓存**
   - 使用 Redis 缓存 API 响应
   - 实现客户端缓存策略

2. **数据分页**
   - 对于大量历史数据实现分页加载

3. **图表优化**
   - 使用数据采样减少渲染点数
   - 实现图表懒加载

## 扩展功能

### 1. 添加更多技术指标

```python
# 在 calculate_market_sentiment 中添加
def calculate_macd(df):
    # MACD 计算逻辑
    pass

def calculate_bollinger_bands(df):
    # 布林带计算逻辑
    pass
```

### 2. 集成更多数据源

- 港交所实时行情 API
- 新闻情感分析 API
- 社交媒体数据

### 3. 添加告警功能

```typescript
// 实现阈值告警
if (sentiment.fear_greed_index > 80) {
  triggerAlert('市场过热警告');
}
```

## 安全注意事项

1. **API 访问控制**
   - 实现身份验证
   - 添加请求频率限制

2. **数据隐私**
   - 不在前端存储敏感数据
   - 使用 HTTPS 传输

3. **输入验证**
   - 验证所有 API 参数
   - 防止注入攻击

## 联系支持

如遇到问题，请联系：
- 技术支持：dev-team@cbsc.com
- 文档：docs/api/cbsc.md

---

最后更新：2024-12-16
版本：1.0.0