"""
策略管理Dashboard - 前端界面

提供Dashboard的前端界面功能。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class DashboardUI:
    """Dashboard前端界面"""

    def __init__(self, config = None):
        self.config = config
        self.logger = logging.getLogger("strategy_dashboard.dashboard_ui")

    async def get_dashboard_html(self) -> str:
        """获取Dashboard HTML"""
        # 简单的HTML界面
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略管理Dashboard</title>
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
        }
        .status {
            color: #4ade80;
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
        }
        .api-links a:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 策略管理Dashboard</h1>
            <p>专业级CBSC策略管理平台</p>
            <p class="status">✅ 系统运行正常</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📈 策略监控</h3>
                <p>实时监控4种CBSC情绪策略</p>
                <p>策略信号分析</p>
                <p>性能指标追踪</p>
            </div>
            <div class="metric-card">
                <h3>⚙️ 参数优化</h3>
                <p>5种优化算法</p>
                <p>交互式参数调整</p>
                <p>实时性能分析</p>
            </div>
            <div class="metric-card">
                <h3>🔬 回测分析</h3>
                <p>专业级回测引擎</p>
                <p>多策略对比</p>
                <p>风险评估体系</p>
            </div>
            <div class="metric-card">
                <h3>📊 系统监控</h3>
                <p>实时性能监控</p>
                <p>系统状态检查</p>
                <p>健康指标展示</p>
            </div>
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
        // 简单的状态检查
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                console.log('系统状态:', data);
            })
            .catch(error => {
                console.error('健康检查失败:', error);
            });

        // 定期刷新数据
        setInterval(() => {
            console.log('刷新数据...');
        }, 30000);
    </script>
</body>
</html>
        """
        return html_content.strip()