# CBSC 量化交易系统性能测试套件

全面的性能测试框架，用于测试CBSC量化交易策略管理系统的前端和后端性能。

## 📁 目录结构

```
tests/performance/
├── README.md                      # 本文档
├── package.json                   # 前端性能测试依赖
├── requirements.txt               # Python性能测试依赖
├── run-all-tests.sh              # 运行所有测试的脚本
│
├── frontend/                      # 前端性能测试
│   ├── performance.spec.js       # Jest性能测试套件
│   ├── bundle-analyzer.js        # Bundle大小分析工具
│   ├── memory-leak-detector.js   # 内存泄漏检测工具
│   └── lighthouse.config.js      # Lighthouse配置
│
├── load/                          # 负载测试
│   ├── load-test-config.yml      # Artillery配置
│   └── locustfile.py             # Locust负载测试脚本
│
├── stress/                        # 压力测试
│   └── stress-test.py           # 压力测试脚本
│
├── api-performance-test.py       # API性能测试
├── performance-monitor.py        # 性能监控系统
├── benchmark-collector.py        # 基准数据收集工具
└── performance-dashboard.html    # 性能监控仪表板
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装所有测试依赖
./run-all-tests.sh --install

# 或手动安装
npm install -g artillery
pip3 install -r tests/performance/requirements.txt
```

### 2. 启动服务

确保系统服务正在运行：

```bash
# 启动后端服务 (端口3003)
cd src/api
python -m uvicorn main:app --reload --port 3003

# 启动前端服务 (端口3000)
cd frontend
npm run dev
```

### 3. 运行所有测试

```bash
# 运行所有性能测试
./run-all-tests.sh

# 运行特定测试类型
./run-all-tests.sh --frontend   # 前端测试
./run-all-tests.sh --backend    # 后端测试
./run-all-tests.sh --load       # 负载测试
./run-all-tests.sh --stress     # 压力测试
```

## 📊 测试类型

### 1. 前端性能测试

#### Lighthouse 审计
```bash
# 运行Lighthouse性能审计
cd frontend
npx lhci autorun

# 手动运行特定页面
npx lighthouse http://localhost:3000/dashboard --output html --output-path lighthouse-report.html
```

#### Jest 性能测试
测试内容包括：
- 页面加载性能
- 大数据集处理 (10,000+ 记录)
- 图表渲染性能
- 内存使用和泄漏检测
- Bundle大小分析

```bash
cd frontend
npm run test:performance
```

#### Bundle 分析
```bash
# 分析前端打包大小
node tests/performance/bundle-analyzer.js
```

#### 内存泄漏检测
```bash
# 检测前端内存泄漏
node tests/performance/memory-leak-detector.js
```

### 2. 后端性能测试

#### API性能测试
```bash
# 运行API性能测试
python3 tests/performance/api-performance-test.py
```

测试目标：
- API响应时间 < 200ms (P95)
- 成功率 > 95%
- 并发处理能力

### 3. 负载测试

#### Artillery 负载测试
```bash
# 运行Artillery负载测试
artillery run tests/load/load-test-config.yml
```

测试场景：
- 正常负载 (100并发用户)
- 峰值负载 (500并发用户)
- 压力测试 (1000+并发用户)

#### Locust 负载测试
```bash
# Web界面模式
locust -f tests/load/locustfile.py --host http://localhost:3003

# 命令行模式
locust -f tests/load/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s
```

### 4. 压力测试

```bash
# 运行压力测试
python3 tests/stress/stress-test.py
```

测试内容：
- 最大并发用户数测试
- 资源耗尽测试
- 突发流量测试
- 持续高负载测试
- 内存泄漏压力测试

### 5. 基准数据收集

```bash
# 收集性能基准
python3 tests/performance/benchmark-collector.py

# 生成基准报告
python3 -c "
from benchmark_collector import BenchmarkCollector
collector = BenchmarkCollector()
collector.generate_benchmark_report()
"
```

### 6. 实时性能监控

```bash
# 启动性能监控系统
python3 tests/performance/performance-monitor.py

# 查看性能监控仪表板
open tests/performance/performance-dashboard.html
```

## 📈 性能指标和目标

### 前端性能目标
- **First Contentful Paint (FCP)**: < 1.5秒
- **Largest Contentful Paint (LCP)**: < 2.5秒
- **First Input Delay (FID)**: < 100ms
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Bundle大小**: < 500KB (gzipped)

### 后端性能目标
- **API响应时间**: < 200ms (P95)
- **API成功率**: > 99%
- **并发用户**: 1000+
- **吞吐量**: 2000+ req/s

### 系统资源目标
- **CPU使用率**: < 80%
- **内存使用率**: < 85%
- **磁盘使用率**: < 90%
- **正常运行时间**: > 99.9%

## 📊 报告和可视化

### 生成的报告文件

1. **性能测试报告**
   - `api-performance-results.json` - API性能测试结果
   - `api-performance-charts.png` - 性能图表
   - `stress-test-results.json` - 压力测试结果
   - `stress-test-charts.png` - 压力测试图表

2. **Lighthouse报告**
   - `lighthouse-results/` - Lighthouse审计结果目录

3. **基准测试报告**
   - `benchmark_report_YYYYMMDD_HHMMSS.html` - 综合基准报告
   - `benchmarks_export_YYYYMMDD_HHMMSS.json` - 导出的基准数据

4. **监控数据**
   - `performance_data.db` - SQLite数据库存储历史性能数据
   - `performance_report_YYYYMMDD_HHMMSS.html` - 性能监控报告

### 查看报告

```bash
# 生成综合报告
python3 tests/performance/performance-monitor.py
# 然后访问生成的HTML报告
```

## 🔧 配置

### Lighthouse配置
编辑 `frontend/tests/performance/lighthouse.config.js` 来自定义：
- 测试URL
- 性能阈值
- 测试参数

### Artillery配置
编辑 `tests/load/load-test-config.yml` 来自定义：
- 负载测试场景
- 并发用户数
- 测试持续时间

### Locust配置
编辑 `tests/load/locustfile.py` 来自定义：
- 用户行为模式
- 权重分布
- 测试端点

### 监控配置
创建 `monitoring_config.json` 来配置：
- 监控间隔
- 告警阈值
- 邮件通知

示例配置：
```json
{
  "monitoring_interval": 5,
  "alert_thresholds": {
    "response_time_ms": 200,
    "error_rate_percent": 5,
    "cpu_usage_percent": 80,
    "memory_usage_percent": 85
  },
  "email_alerts": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "recipients": ["admin@cbsc.com"]
  }
}
```

## 🛠️ 故障排除

### 常见问题

1. **服务未运行**
   ```
   错误: Connection refused
   解决: 确保后端(3003)和前端(3000)服务正在运行
   ```

2. **端口冲突**
   ```
   错误: Address already in use
   解决: 更改端口或停止占用端口的进程
   ```

3. **内存不足**
   ```
   错误: Out of memory
   解决: 减少并发用户数或增加系统内存
   ```

4. **依赖缺失**
   ```
   错误: Module not found
   解决: 运行 ./run-all-tests.sh --install
   ```

### 调试模式

```bash
# 启用详细日志
DEBUG=1 ./run-all-tests.sh

# 单独运行测试进行调试
python3 -m pdb tests/performance/api-performance-test.py
```

## 📝 最佳实践

1. **定期运行测试**
   - 每日自动运行基础性能测试
   - 每周运行完整负载测试
   - 每月运行压力测试

2. **版本控制**
   - 跟踪性能基准变化
   - 为每个版本保存基准报告
   - 设置性能回归检测

3. **持续集成**
   - 将性能测试集成到CI/CD流水线
   - 设置性能阈值作为发布门禁
   - 自动生成性能报告

4. **监控告警**
   - 配置实时性能监控
   - 设置关键指标告警
   - 建立性能问题响应流程

## 📞 支持和反馈

如有问题或建议，请联系：
- 开发团队: dev-team@cbsc.com
- 性能优化: performance@cbsc.com

## 📄 许可证

本性能测试套件遵循项目主许可证。