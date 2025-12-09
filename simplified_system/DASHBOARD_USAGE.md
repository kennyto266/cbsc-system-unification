# 交互式性能仪表板使用指南

## 概述

专业级量化交易实时仪表板，提供全面的投资组合监控、性能分析和风险管理功能。

## 核心功能

### 1. 实时数据监控
- **实时价格更新**: 支持港股实时行情数据
- **技术指标计算**: 自动计算RSI、MACD、布林带等指标
- **政府经济数据**: 集成HIBOR、汇率等宏观经济指标

### 2. 交互式图表
- **K线图**: 专业的OHLCV价格走势图
- **技术指标叠加**: SMA、EMA、布林带可视化
- **成交量分析**: 实时成交量柱状图
- **相关性热力图**: 资产间相关性分析
- **月度收益热力图**: 历史收益表现分析

### 3. 性能指标
- **关键指标卡片**: 总回报率、Sharpe比率、最大回撤等
- **性能雷达图**: 多维度性能对比
- **风险收益散点图**: 策略风险收益分析
- **回撤分析**: 详细的回撤时间和幅度分析

### 4. 策略回测
- **多种策略**: RSI均值回归、MACD交叉、布林带等
- **实时回测**: 一键运行策略回测
- **性能对比**: 策略与基准对比分析
- **参数优化**: 自动化参数寻优

## 安装要求

### 系统依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 仪表板专用依赖
pip install dash>=2.14.0
pip install dash-bootstrap-components>=1.5.0
pip install plotly>=5.17.0
pip install websockets>=12.0
```

### 核心组件
- **VectorBT**: 高性能回测引擎
- **Plotly**: 交互式图表库
- **Dash**: Web应用框架
- **Pandas**: 数据处理
- **NumPy**: 数值计算

## 快速开始

### 1. 基础测试
```bash
cd simplified_system
python test_dashboard_simple.py
```

### 2. 启动仪表板
```bash
# 方式1: 快速启动
python run_dashboard.py

# 方式2: 完整演示
python dashboard_demo.py

# 方式3: 编程方式
python -c "
from src.dashboard import run_dashboard
run_dashboard(debug=True, port=8050)
"
```

### 3. 访问仪表板
打开浏览器访问: http://127.0.0.1:8050

## 使用指南

### 控制面板操作

#### 股票选择
1. 点击"选择股票"下拉菜单
2. 选择目标股票（如腾讯控股 0700.HK）
3. 系统自动获取历史数据

#### 时间范围设置
- **1个月**: 短期技术分析
- **3个月**: 中期趋势分析
- **6个月**: 中长期分析
- **1年**: 长期性能分析
- **2年**: 历史表现回顾

#### 策略配置
- **RSI均值回归**: 适用于震荡市场
- **MACD交叉**: 趋势跟踪策略
- **布林带**: 波动率突破策略
- **双移动平均**: 经典趋势策略
- **动量突破**: 强势股策略
- **波动率突破**: 高波动策略

#### 基准比较
- **恒生指数**: 港股市场基准
- **沪深300**: A股市场基准
- **无基准**: 绝对收益分析

### 实时模式

#### 启用实时更新
1. 点击"实时模式"按钮
2. 系统开始自动更新数据
3. 图表和指标实时刷新

#### 实时数据源
- **股票API**: 中央API实时港股数据
- **政府数据**: HIBOR利率等经济指标
- **技术指标**: 实时计算技术分析指标

### 图表交互

#### 价格走势图
- **缩放**: 鼠标滚轮缩放
- **平移**: 拖拽移动时间窗口
- **悬停**: 显示详细数据点信息
- **指标切换**: 点击图例显示/隐藏指标

#### 性能雷达图
- **策略对比**: 多策略性能对比
- **基准对比**: 与市场基准对比
- **指标权重**: 可调整指标权重

#### 热力图
- **颜色编码**: 绿色=正收益，红色=负收益
- **悬停详情**: 显示具体数值
- **时间筛选**: 可选择时间段

### 回测功能

#### 运行回测
1. 选择股票和时间范围
2. 配置策略参数
3. 点击"运行回测"
4. 查看回测结果

#### 回测结果
- **性能指标**: 回报率、Sharpe、最大回撤等
- **交易记录**: 详细买卖点记录
- **风险分析**: 胜率、盈亏比等
- **图表展示**: 权益曲线、回撤图等

## 高级功能

### 自定义策略

#### 添加新策略
```python
from src.backtest.vectorbt_engine import VectorBTEngine

# 自定义策略参数
custom_params = {
    'period': 20,
    'threshold': 0.02
}

# 运行回测
engine = VectorBTEngine()
result = engine.backtest_strategy(
    data=data,
    strategy='CUSTOM_STRATEGY',
    parameters=custom_params
)
```

#### 技术指标扩展
```python
from src.indicators.core_indicators import CoreIndicators

indicators = CoreIndicators()

# 计算自定义指标
custom_indicator = indicators.calculate_custom_indicator(
    data['close'],
    period=14
)
```

### 实时数据监控

#### 设置监控列表
```python
from src.dashboard import create_real_time_updater

updater = create_real_time_updater(update_interval=30)

# 添加监控股票
updater.add_symbol('0700.HK')
updater.add_symbol('09988.HK')
updater.add_symbol('03690.HK')

# 启动实时更新
updater.start()
```

#### 自定义回调函数
```python
def my_callback(data):
    """自定义数据更新回调"""
    print(f"Received update: {data['timestamp']}")

updater.add_callback(my_callback)
```

### 数据导出

#### 导出图表
```python
import plotly.graph_objects as go

# 导出为HTML
fig.write_html("chart.html")

# 导出为PNG
fig.write_image("chart.png")

# 导出为PDF
fig.write_image("chart.pdf")
```

#### 导出数据
```python
# 导出回测结果
result.to_csv("backtest_results.csv")

# 导出性能指标
metrics = result.to_dict()
import json
with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

## 性能优化

### 内存管理
- **数据缓存**: 自动缓存常用数据
- **延迟加载**: 按需加载历史数据
- **定期清理**: 自动清理过期缓存

### 响应速度
- **异步更新**: 使用异步数据更新
- **图表优化**: 优化大数据量图表渲染
- **批量处理**: 批量处理技术指标计算

### 网络优化
- **压缩传输**: 数据压缩减少传输时间
- **增量更新**: 只传输变化的数据
- **连接复用**: 复用HTTP连接

## 故障排除

### 常见问题

#### 1. 仪表板无法启动
```bash
# 检查依赖
pip install -r requirements.txt

# 检查端口占用
netstat -ano | findstr :8050

# 更换端口
python -c "
from src.dashboard import run_dashboard
run_dashboard(port=8051)
"
```

#### 2. 数据获取失败
```bash
# 检查网络连接
ping 18.180.162.113

# 检查API状态
curl http://18.180.162.113:9191/inst/getInst?symbol=0700.hk

# 使用测试数据
python test_dashboard_simple.py
```

#### 3. 图表显示异常
```bash
# 更新Plotly
pip install --upgrade plotly

# 检查浏览器控制台
# 查看JavaScript错误信息

# 重启仪表板服务
python run_dashboard.py
```

#### 4. 实时更新不工作
```python
# 检查更新器状态
from src.dashboard import get_global_updater
updater = get_global_updater()
stats = updater.get_statistics()
print(stats)

# 重启更新器
updater.stop()
updater.start()
```

### 调试模式

#### 启用调试
```python
# 开发模式启动
python run_dashboard.py

# 或者
python -c "
from src.dashboard import run_dashboard
run_dashboard(debug=True)
"
```

#### 日志查看
```bash
# 查看应用日志
tail -f logs/dashboard.log

# 查看详细错误
python dashboard_demo.py
```

## 扩展开发

### 添加新图表
```python
from src.dashboard.performance_charts import PerformanceCharts

class CustomCharts(PerformanceCharts):
    def create_custom_chart(self, data):
        """自定义图表"""
        fig = go.Figure()
        # 添加自定义图表逻辑
        return fig
```

### 添加新数据源
```python
from src.dashboard.real_time_updater import RealTimeUpdater

class CustomUpdater(RealTimeUpdater):
    def _update_custom_data(self):
        """自定义数据源更新"""
        # 添加自定义数据源逻辑
        pass
```

### 添加新策略
```python
from src.backtest.vectorbt_engine import VectorBTEngine

class CustomEngine(VectorBTEngine):
    def _custom_strategy_signals(self, data, params):
        """自定义策略信号"""
        # 添加自定义策略逻辑
        return signals
```

## 最佳实践

### 使用建议
1. **数据范围**: 建议使用1-2年数据进行分析
2. **更新频率**: 实时模式建议30-60秒更新间隔
3. **策略选择**: 根据市场环境选择合适策略
4. **风险控制**: 设置合理的止损止盈参数

### 性能建议
1. **内存使用**: 避免加载过多历史数据
2. **并发处理**: 使用异步处理提高响应速度
3. **缓存策略**: 合理使用缓存减少计算
4. **图表优化**: 大数据量时使用采样显示

### 安全建议
1. **网络安全**: 使用HTTPS连接
2. **数据安全**: 定期备份重要数据
3. **访问控制**: 设置适当的访问权限
4. **监控告警**: 配置异常情况告警

## 技术支持

### 文档资源
- **API文档**: 查看详细的API接口说明
- **示例代码**: 参考examples目录中的示例
- **测试用例**: 查看test目录中的测试

### 联系支持
- **问题反馈**: 通过GitHub Issues提交
- **功能建议**: 提交Feature Request
- **技术讨论**: 参与项目讨论

---

**更新日期**: 2025-11-23
**版本**: 1.0.0
**维护者**: 量化交易系统团队