#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 简化仪表板

这是一个简化版本的仪表板，避免复杂的依赖问题。
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from datetime import datetime
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hk_quant_system")

# 创建FastAPI应用
app = FastAPI(
    title="港股量化交易 AI Agent 仪表板",
    description="实时监控和管理7个AI Agent的量化交易系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据
MOCK_AGENTS = [
    {
        "agent_id": "quant_analyst_1",
        "agent_type": "量化分析师",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 150,
            "win_rate": 0.68,
            "sharpe_ratio": 1.35,
            "max_drawdown": 0.045
        },
        "current_strategy": "SMA交叉策略",
        "risk_level": "medium"
    },
    {
        "agent_id": "quant_trader_1",
        "agent_type": "量化交易员",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 200,
            "win_rate": 0.72,
            "sharpe_ratio": 1.45,
            "max_drawdown": 0.038
        },
        "current_strategy": "动量策略",
        "risk_level": "low"
    },
    {
        "agent_id": "portfolio_manager_1",
        "agent_type": "投资组合经理",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 80,
            "win_rate": 0.75,
            "sharpe_ratio": 1.28,
            "max_drawdown": 0.032
        },
        "current_strategy": "多因子模型",
        "risk_level": "low"
    },
    {
        "agent_id": "risk_analyst_1",
        "agent_type": "风险分析师",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 60,
            "win_rate": 0.80,
            "sharpe_ratio": 1.52,
            "max_drawdown": 0.025
        },
        "current_strategy": "风险平价策略",
        "risk_level": "low"
    },
    {
        "agent_id": "data_scientist_1",
        "agent_type": "数据科学家",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 120,
            "win_rate": 0.70,
            "sharpe_ratio": 1.40,
            "max_drawdown": 0.040
        },
        "current_strategy": "机器学习策略",
        "risk_level": "medium"
    },
    {
        "agent_id": "quant_engineer_1",
        "agent_type": "量化工程师",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 90,
            "win_rate": 0.73,
            "sharpe_ratio": 1.38,
            "max_drawdown": 0.035
        },
        "current_strategy": "高频交易策略",
        "risk_level": "high"
    },
    {
        "agent_id": "research_analyst_1",
        "agent_type": "研究分析师",
        "status": "running",
        "last_activity": "2024-01-01T12:00:00Z",
        "performance_metrics": {
            "total_trades": 110,
            "win_rate": 0.69,
            "sharpe_ratio": 1.33,
            "max_drawdown": 0.042
        },
        "current_strategy": "基本面策略",
        "risk_level": "medium"
    }
]

MOCK_SYSTEM_STATUS = {
    "system_health": "healthy",
    "total_agents": 7,
    "active_agents": 7,
    "system_uptime": "24h 15m",
    "total_trades": 1250,
    "system_performance": {
        "cpu_usage": 25.5,
        "memory_usage": 2048,
        "disk_usage": 15.2
    },
    "last_update": datetime.now().isoformat()
}

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """仪表板主页"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>港股量化交易 AI Agent 仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header { 
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 { 
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .tab {
            flex: 1;
            padding: 15px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #6c757d;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        
        .tab.active {
            color: #667eea;
            background: white;
            border-bottom-color: #667eea;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab-content {
            display: none;
            padding: 30px;
            min-height: 500px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .agent-card {
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .agent-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .agent-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #6c757d;
        }
        
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #6c757d; }
        
        .system-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .overview-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e1e8ed;
        }
        
        .overview-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .overview-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        
        .chart-container {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            border: 1px solid #e1e8ed;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 港股量化交易 AI Agent 仪表板</h1>
            <p>实时监控和管理7个专业AI Agent的量化交易系统</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('overview')">📊 系统概览</button>
            <button class="tab" onclick="switchTab('agents')">🤖 Agent状态</button>
            <button class="tab" onclick="switchTab('performance')">📈 性能分析</button>
            <button class="tab" onclick="switchTab('monitoring')">🔍 实时监控</button>
        </div>
        
        <!-- 系统概览标签页 -->
        <div id="overview" class="tab-content active">
            <div class="system-overview">
                <div class="overview-card">
                    <div class="overview-value" id="totalAgents">7</div>
                    <div class="overview-label">总Agent数</div>
                </div>
                <div class="overview-card">
                    <div class="overview-value" id="activeAgents">7</div>
                    <div class="overview-label">活跃Agent</div>
                </div>
                <div class="overview-card">
                    <div class="overview-value" id="totalTrades">1,250</div>
                    <div class="overview-label">总交易数</div>
                </div>
                <div class="overview-card">
                    <div class="overview-value" id="systemHealth">健康</div>
                    <div class="overview-label">系统状态</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>📊 系统性能监控</h3>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <!-- Agent状态标签页 -->
        <div id="agents" class="tab-content">
            <div class="agent-grid" id="agentGrid">
                <div class="loading">⏳ 正在加载Agent数据...</div>
            </div>
        </div>
        
        <!-- 性能分析标签页 -->
        <div id="performance" class="tab-content">
            <div class="chart-container">
                <h3>📈 交易性能分析</h3>
                <canvas id="tradingChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <!-- 实时监控标签页 -->
        <div id="monitoring" class="tab-content">
            <div class="chart-container">
                <h3>🔍 实时系统监控</h3>
                <canvas id="monitoringChart" width="400" height="300"></canvas>
            </div>
        </div>
    </div>

    <script>
        let performanceChart = null;
        let tradingChart = null;
        let monitoringChart = null;
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function loadAgentData() {
            try {
                const response = await fetch('/api/agents');
                const agents = await response.json();
                
                const agentGrid = document.getElementById('agentGrid');
                agentGrid.innerHTML = '';
                
                agents.forEach(agent => {
                    const card = createAgentCard(agent);
                    agentGrid.appendChild(card);
                });
            } catch (error) {
                console.error('加载Agent数据失败:', error);
                document.getElementById('agentGrid').innerHTML = 
                    '<div class="loading">❌ 加载Agent数据失败</div>';
            }
        }
        
        function createAgentCard(agent) {
            const card = document.createElement('div');
            card.className = 'agent-card';
            
            const riskColor = agent.risk_level === 'low' ? 'positive' : 
                            agent.risk_level === 'medium' ? 'neutral' : 'negative';
            
            card.innerHTML = `
                <div class="agent-header">
                    <div class="agent-name">${agent.agent_type}</div>
                    <div class="agent-status status-running">运行中</div>
                </div>
                <div class="agent-metrics">
                    <div class="metric">
                        <span class="metric-label">总交易数</span>
                        <span class="metric-value">${agent.performance_metrics.total_trades}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">胜率</span>
                        <span class="metric-value positive">${(agent.performance_metrics.win_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">夏普比率</span>
                        <span class="metric-value positive">${agent.performance_metrics.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">最大回撤</span>
                        <span class="metric-value negative">${(agent.performance_metrics.max_drawdown * 100).toFixed(2)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">当前策略</span>
                        <span class="metric-value">${agent.current_strategy}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">风险等级</span>
                        <span class="metric-value ${riskColor}">${agent.risk_level}</span>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function initCharts() {
            // 性能监控图表
            const perfCtx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'CPU使用率 (%)',
                        data: [20, 25, 30, 25, 22, 28],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.1
                    }, {
                        label: '内存使用率 (%)',
                        data: [60, 65, 70, 68, 62, 66],
                        borderColor: '#764ba2',
                        backgroundColor: 'rgba(118, 75, 162, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            // 交易性能图表
            const tradingCtx = document.getElementById('tradingChart').getContext('2d');
            tradingChart = new Chart(tradingCtx, {
                type: 'bar',
                data: {
                    labels: ['量化分析师', '量化交易员', '投资组合经理', '风险分析师', '数据科学家', '量化工程师', '研究分析师'],
                    datasets: [{
                        label: '夏普比率',
                        data: [1.35, 1.45, 1.28, 1.52, 1.40, 1.38, 1.33],
                        backgroundColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            // 实时监控图表
            const monitoringCtx = document.getElementById('monitoringChart').getContext('2d');
            monitoringChart = new Chart(monitoringCtx, {
                type: 'doughnut',
                data: {
                    labels: ['运行中', '维护中', '错误'],
                    datasets: [{
                        data: [7, 0, 0],
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        // 页面加载完成后初始化
        window.onload = function() {
            loadAgentData();
            initCharts();
        };
    </script>
</body>
</html>
    """

@app.get("/api/agents")
async def get_agents():
    """获取所有Agent数据"""
    return MOCK_AGENTS

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    return MOCK_SYSTEM_STATUS

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

def main():
    """主函数"""
    logger.info("🚀 启动港股量化交易 AI Agent 仪表板...")
    logger.info("🌐 访问地址: http://localhost:8001")
    logger.info("📊 功能: 多智能体监控、实时数据、性能分析")
    logger.info("⏹️ 按 Ctrl+C 停止系统")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )

if __name__ == "__main__":
    main()
