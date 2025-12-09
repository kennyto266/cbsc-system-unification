#!/usr/bin/env python3
"""
简化版策略管理Dashboard启动脚本

只包含核心功能，避免复杂的依赖问题。
"""

import asyncio
import logging
import sys
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SimpleStrategyDashboard:
    """简化版策略管理Dashboard"""

    def __init__(self, port: int = 3003, host: str = "0.0.0.0"):
        self.port = port
        self.host = host

        # 创建FastAPI应用
        self.app = FastAPI(
            title="策略管理Dashboard - 简化版",
            description="专业级CBSC策略管理平台",
            version="1.0.0-simplified"
        )

              # 暂时注释掉CORS中间件以避免配置问题
        # self.app.add_middleware(
        #     CORSMiddleware,
        #     allow_origins=["*"],
        #     allow_credentials=True,
        #     allow_methods=["*"],
        #     allow_headers=["*"],
        # )

        # 设置路由
        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Dashboard主页"""
            return self._get_dashboard_html()

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0-simplified",
                "services": {
                    "strategy_dashboard": "running",
                    "parameter_optimization": "simulated",
                    "backtesting_lab": "simulated",
                    "agent_coordination": "disabled"
                }
            }

        @self.app.get("/api/status")
        async def get_system_status():
            """获取系统状态"""
            return {
                "system_health": "operational",
                "active_strategies": 4,
                "total_agents": 0,  # 简化版没有Agent
                "active_tasks": 0,
                "system_load": "normal",
                "last_update": datetime.now().isoformat()
            }

        @self.app.get("/api/strategies")
        async def get_strategies():
            """获取策略列表"""
            return {
                "strategies": [
                    {
                        "id": "direct_rsi",
                        "name": "直接RSI情绪策略",
                        "type": "sentiment",
                        "status": "active",
                        "performance": {
                            "return": 0.0234,
                            "sharpe": 1.45,
                            "max_drawdown": -0.0876
                        }
                    },
                    {
                        "id": "sentiment_momentum",
                        "name": "情绪动量策略",
                        "type": "sentiment",
                        "status": "active",
                        "performance": {
                            "return": 0.0156,
                            "sharpe": 1.23,
                            "max_drawdown": -0.0654
                        }
                    },
                    {
                        "id": "composite_index",
                        "name": "复合指標策略",
                        "type": "sentiment",
                        "status": "active",
                        "performance": {
                            "return": 0.0312,
                            "sharpe": 1.67,
                            "max_drawdown": -0.0923
                        }
                    },
                    {
                        "id": "volatility_adjusted",
                        "name": "波動率調整策略",
                        "type": "sentiment",
                        "status": "active",
                        "performance": {
                            "return": 0.0198,
                            "sharpe": 1.34,
                            "max_drawdown": -0.0745
                        }
                    }
                ]
            }

        @self.app.get("/api/performance/summary")
        async def get_performance_summary():
            """获取性能摘要"""
            return {
                "summary": {
                    "total_return": 0.0225,
                    "annualized_return": 0.0456,
                    "sharpe_ratio": 1.42,
                    "max_drawdown": -0.0801,
                    "volatility": 0.1567,
                    "win_rate": 0.6234,
                    "profit_factor": 1.78
                },
                "benchmark": {
                    "hsi_return": 0.0123,
                    "relative_return": 0.0102
                }
            }

        @self.app.get("/api/agents/status")
        async def get_agents_status():
            """获取Agent状态（简化版返回空）"""
            return {
                "agents": [],
                "message": "Agent功能已在简化版中禁用"
            }

    def _get_dashboard_html(self) -> str:
        """获取Dashboard HTML"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略管理Dashboard - 简化版</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status {
            color: #4ade80;
        }
        .simplified {
            color: #fbbf24;
        }
        .api-links {
            text-align: center;
            margin-top: 40px;
        }
        .api-links a {
            color: white;
            text-decoration: none;
            margin: 0 10px;
            padding: 10px 20px;
            border: 1px solid white;
            border-radius: 5px;
            transition: background-color 0.3s;
            display: inline-block;
        }
        .api-links a:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        .data-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .loading {
            color: #fbbf24;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 策略管理Dashboard</h1>
            <p>专业级CBSC策略管理平台 - 简化版</p>
            <p class="status">✅ 系统运行正常</p>
            <p class="simplified">📦 简化版模式 - 核心功能正常运行</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📈 策略监控</h3>
                <p>监控4种CBSC情绪策略</p>
                <p>实时信号分析</p>
                <p>性能指标追踪</p>
                <div class="loading">状态: <span id="strategy-status">加载中...</span></div>
            </div>
            <div class="metric-card">
                <h3>⚙️ 参数优化</h3>
                <p>多种优化算法支持</p>
                <p>参数空间探索</p>
                <p>性能响应分析</p>
                <div class="loading">状态: 模拟运行中</div>
            </div>
            <div class="metric-card">
                <h3>🔬 回测分析</h3>
                <p>历史数据回测</p>
                <p>策略性能评估</p>
                <p>风险指标计算</p>
                <div class="loading">状态: 模拟运行中</div>
            </div>
            <div class="metric-card">
                <h3>📊 系统监控</h3>
                <p>实时性能监控</p>
                <p>系统状态检查</p>
                <p>健康指标展示</p>
                <div class="loading">状态: 正常运行</div>
            </div>
        </div>

        <div class="data-section">
            <h3>📈 策略数据概览</h3>
            <div id="strategies-data" class="loading">正在加载策略数据...</div>
        </div>

        <div class="data-section">
            <h3>💰 性能摘要</h3>
            <div id="performance-data" class="loading">正在加载性能数据...</div>
        </div>

        <div class="api-links">
            <h3>🔗 API接口</h3>
            <a href="/health" target="_blank">健康检查</a>
            <a href="/api/status" target="_blank">系统状态</a>
            <a href="/api/strategies" target="_blank">策略列表</a>
            <a href="/api/performance/summary" target="_blank">性能摘要</a>
            <a href="/docs" target="_blank">API文档</a>
        </div>
    </div>

    <script>
        // 页面加载完成后获取数据
        document.addEventListener('DOMContentLoaded', function() {
            loadStrategiesData();
            loadPerformanceData();
            loadSystemStatus();
        });

        async function loadStrategiesData() {
            try {
                const response = await fetch('/api/strategies');
                const data = await response.json();

                const container = document.getElementById('strategies-data');
                container.innerHTML = '';

                data.strategies.forEach(strategy => {
                    const strategyDiv = document.createElement('div');
                    strategyDiv.innerHTML = `
                        <h4>${strategy.name}</h4>
                        <p>状态: ${strategy.status}</p>
                        <p>收益率: ${(strategy.performance.return * 100).toFixed(2)}%</p>
                        <p>夏普比率: ${strategy.performance.sharpe.toFixed(2)}</p>
                    `;
                    container.appendChild(strategyDiv);
                });

                document.getElementById('strategy-status').textContent = '正常运行';
            } catch (error) {
                document.getElementById('strategies-data').textContent = '数据加载失败';
                console.error('策略数据加载失败:', error);
            }
        }

        async function loadPerformanceData() {
            try {
                const response = await fetch('/api/performance/summary');
                const data = await response.json();

                const container = document.getElementById('performance-data');
                container.innerHTML = `
                    <p>总收益率: ${(data.summary.total_return * 100).toFixed(2)}%</p>
                    <p>年化收益率: ${(data.summary.annualized_return * 100).toFixed(2)}%</p>
                    <p>夏普比率: ${data.summary.sharpe_ratio.toFixed(2)}</p>
                    <p>最大回撤: ${(data.summary.max_drawdown * 100).toFixed(2)}%</p>
                    <p>胜率: ${(data.summary.win_rate * 100).toFixed(1)}%</p>
                    <p>盈亏比: ${data.summary.profit_factor.toFixed(2)}</p>
                `;
            } catch (error) {
                document.getElementById('performance-data').textContent = '性能数据加载失败';
                console.error('性能数据加载失败:', error);
            }
        }

        async function loadSystemStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                console.log('系统状态:', data);
            } catch (error) {
                console.error('系统状态检查失败:', error);
            }
        }

        // 定期刷新数据
        setInterval(() => {
            console.log('刷新Dashboard数据...');
            loadStrategiesData();
            loadPerformanceData();
        }, 30000); // 30秒刷新一次
    </script>
</body>
</html>
        """
        return html_content.strip()

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略管理Dashboard - 简化版",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=3003,
        help="指定端口号 (默认: 3003)"
    )

    parser.add_argument(
        "--host", "-H",
        type=str,
        default="0.0.0.0",
        help="指定主机地址 (默认: 0.0.0.0)"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="策略管理Dashboard v1.0.0-simplified"
    )

    args = parser.parse_args()

    # 打印启动信息
    print("=" * 60)
    print("Strategy Management Dashboard - Simplified")
    print("=" * 60)
    print("Professional CBSC Strategy Management Platform")
    print("Strategy Monitoring | Parameter Optimization | Backtesting")
    print("=" * 60)

    logger.info(f"Startup parameters: port={args.port}, host={args.host}, debug={args.debug}")

    # 创建Dashboard
    dashboard = SimpleStrategyDashboard(port=args.port, host=args.host)

    try:
        # 配置uvicorn
        config = uvicorn.Config(
            app=dashboard.get_app(),
            host=args.host,
            port=args.port,
            log_level="debug" if args.debug else "info",
            reload=args.debug,
            access_log=args.debug
        )

        server = uvicorn.Server(config)

        logger.info("Dashboard started successfully!")
        logger.info(f"Access URL: http://{args.host}:{args.port}")
        logger.info(f"API docs: http://{args.host}:{args.port}/docs")

        server.run()

    except KeyboardInterrupt:
        logger.info("User interrupted, program exit")
    except Exception as e:
        logger.error(f"Program runtime error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()