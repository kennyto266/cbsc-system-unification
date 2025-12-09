"""
HTML模板生成器

负责生成各种仪表板页面的HTML内容
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class HTMLGenerator:
    """HTML模板生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.html_generator")
    
    def get_dashboard_html(self, agent_data: Dict[str, Any] = None) -> str:
        """生成主仪表板HTML"""
        agent_data = agent_data or {}
        
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>港股量化交易 AI Agent 仪表板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        {self._get_dashboard_css()}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> HK Quant AI Agents
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/performance">绩效分析</a>
                <a class="nav-link" href="/system">系统状态</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2 class="mb-4">
                    <i class="fas fa-tachometer-alt"></i> 实时监控仪表板
                </h2>
            </div>
        </div>

        <div class="row" id="agent-cards">
            {self._generate_agent_cards(agent_data)}
        </div>

        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> 系统性能</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="performanceChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> 系统告警</h5>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> 系统运行正常
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        {self._get_dashboard_js()}
    </script>
</body>
</html>
        """
    
    def get_agent_detail_html(self, agent_id: str, agent_data: Dict[str, Any] = None) -> str:
        """生成Agent详情页面HTML"""
        agent_data = agent_data or {}
        
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent详情 - {agent_id}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-arrow-left"></i> 返回仪表板
            </a>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-robot"></i> Agent详情: {agent_id}</h2>
            </div>
        </div>

        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Agent状态</h5>
                    </div>
                    <div class="card-body">
                        <div id="agent-status">
                            {self._generate_agent_status(agent_data)}
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>快速操作</h5>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-primary btn-sm mb-2" onclick="startAgent('{agent_id}')">
                            <i class="fas fa-play"></i> 启动
                        </button>
                        <button class="btn btn-warning btn-sm mb-2" onclick="stopAgent('{agent_id}')">
                            <i class="fas fa-stop"></i> 停止
                        </button>
                        <button class="btn btn-info btn-sm mb-2" onclick="restartAgent('{agent_id}')">
                            <i class="fas fa-redo"></i> 重启
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        {self._get_agent_detail_js()}
    </script>
</body>
</html>
        """
    
    def get_strategy_detail_html(self, agent_id: str, strategy_data: Dict[str, Any] = None) -> str:
        """生成策略详情页面HTML"""
        strategy_data = strategy_data or {}
        
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略详情 - {agent_id}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/agent/{agent_id}">
                <i class="fas fa-arrow-left"></i> 返回Agent详情
            </a>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-chart-line"></i> 策略详情: {agent_id}</h2>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>策略参数</h5>
                    </div>
                    <div class="card-body">
                        {self._generate_strategy_params(strategy_data)}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>绩效指标</h5>
                    </div>
                    <div class="card-body">
                        {self._generate_performance_metrics(strategy_data)}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
    
    def get_performance_html(self) -> str:
        """生成绩效分析页面HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>绩效分析</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-arrow-left"></i> 返回仪表板
            </a>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-chart-bar"></i> 绩效分析</h2>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <canvas id="performanceChart" width="800" height="400"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
        """
    
    def get_system_status_html(self) -> str:
        """生成系统状态页面HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统状态</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-arrow-left"></i> 返回仪表板
            </a>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-server"></i> 系统状态</h2>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>系统资源</h5>
                    </div>
                    <div class="card-body">
                        <div class="progress mb-2">
                            <div class="progress-bar" role="progressbar" style="width: 25%">CPU: 25%</div>
                        </div>
                        <div class="progress mb-2">
                            <div class="progress-bar bg-success" role="progressbar" style="width: 60%">内存: 60%</div>
                        </div>
                        <div class="progress">
                            <div class="progress-bar bg-info" role="progressbar" style="width: 40%">磁盘: 40%</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>服务状态</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>数据库连接</span>
                            <span class="badge bg-success">正常</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>消息队列</span>
                            <span class="badge bg-success">正常</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>API服务</span>
                            <span class="badge bg-success">正常</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
    
    def _get_dashboard_css(self) -> str:
        """获取仪表板CSS样式"""
        return """
        .agent-card {
            transition: transform 0.2s;
        }
        .agent-card:hover {
            transform: translateY(-5px);
        }
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .status-error { color: #ffc107; }
        """
    
    def _get_dashboard_js(self) -> str:
        """获取仪表板JavaScript代码"""
        return """
        // WebSocket连接
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            // 更新仪表板数据
            console.log('Dashboard updated:', data);
        }
        
        // 初始化图表
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '收益率',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            }
        });
        """
    
    def _get_agent_detail_js(self) -> str:
        """获取Agent详情页面JavaScript代码"""
        return """
        function startAgent(agentId) {
            fetch(`/api/agents/${agentId}/start`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Agent启动成功');
                        location.reload();
                    } else {
                        alert('Agent启动失败: ' + data.error);
                    }
                });
        }
        
        function stopAgent(agentId) {
            fetch(`/api/agents/${agentId}/stop`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Agent停止成功');
                        location.reload();
                    } else {
                        alert('Agent停止失败: ' + data.error);
                    }
                });
        }
        
        function restartAgent(agentId) {
            fetch(`/api/agents/${agentId}/restart`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Agent重启成功');
                        location.reload();
                    } else {
                        alert('Agent重启失败: ' + data.error);
                    }
                });
        }
        """
    
    def _generate_agent_cards(self, agent_data: Dict[str, Any]) -> str:
        """生成Agent卡片HTML"""
        cards = []
        for agent_id, data in agent_data.items():
            status_class = f"status-{data.get('status', 'stopped')}"
            cards.append(f"""
            <div class="col-md-4 mb-3">
                <div class="card agent-card">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-robot"></i> {agent_id}
                        </h5>
                        <p class="card-text">
                            <span class="{status_class}">
                                <i class="fas fa-circle"></i> {data.get('status', 'stopped')}
                            </span>
                        </p>
                        <a href="/agent/{agent_id}" class="btn btn-primary btn-sm">查看详情</a>
                    </div>
                </div>
            </div>
            """)
        return "".join(cards)
    
    def _generate_agent_status(self, agent_data: Dict[str, Any]) -> str:
        """生成Agent状态HTML"""
        return f"""
        <div class="row">
            <div class="col-md-6">
                <strong>状态:</strong> {agent_data.get('status', 'unknown')}
            </div>
            <div class="col-md-6">
                <strong>运行时间:</strong> {agent_data.get('uptime', '0')}秒
            </div>
        </div>
        <div class="row mt-2">
            <div class="col-md-6">
                <strong>CPU使用率:</strong> {agent_data.get('cpu_usage', '0')}%
            </div>
            <div class="col-md-6">
                <strong>内存使用率:</strong> {agent_data.get('memory_usage', '0')}%
            </div>
        </div>
        """
    
    def _generate_strategy_params(self, strategy_data: Dict[str, Any]) -> str:
        """生成策略参数HTML"""
        params = strategy_data.get('parameters', {})
        html = "<ul class='list-unstyled'>"
        for key, value in params.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html
    
    def _generate_performance_metrics(self, strategy_data: Dict[str, Any]) -> str:
        """生成绩效指标HTML"""
        metrics = strategy_data.get('metrics', {})
        html = "<ul class='list-unstyled'>"
        for key, value in metrics.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html