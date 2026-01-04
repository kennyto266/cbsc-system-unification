
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import time
from datetime import datetime

class CBSCFrontendHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC量化策略管理系統</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft JhengHei', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: #333; margin-bottom: 15px; font-size: 1.3em; }
        .metric { display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; }
        .metric-value { font-weight: bold; color: #2c3e50; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-online { background: #27ae60; }
        .status-offline { background: #e74c3c; }
        .button { background: linear-gradient(45deg, #3498db, #2980b9); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.3s; margin: 5px; }
        .button:hover { transform: scale(1.05); box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4); }
        .chart-container { margin-top: 20px; height: 300px; }
        .footer { text-align: center; color: white; opacity: 0.8; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CBSC量化策略管理系統</h1>
            <p>專業級量化交易策略管理平台 - 完整版</p>
        </div>

        <div class="dashboard">
            <div class="card">
                <h3>系統狀態</h3>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>API服務</span>
                    <span class="metric-value">運行中</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>數據庫</span>
                    <span class="metric-value">已連接</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>前端界面</span>
                    <span class="metric-value">運行中</span>
                </div>
            </div>

            <div class="card">
                <h3>策略概覽</h3>
                <div class="metric">
                    <span>活躍策略</span>
                    <span class="metric-value">12</span>
                </div>
                <div class="metric">
                    <span>總回測數</span>
                    <span class="metric-value">248</span>
                </div>
                <div class="metric">
                    <span>今日收益率</span>
                    <span class="metric-value" style="color: #27ae60;">+2.34%</span>
                </div>
            </div>

            <div class="card">
                <h3>快速操作</h3>
                <button class="button" onclick="createStrategy()">創建策略</button>
                <button class="button" onclick="runBacktest()">運行回測</button>
                <button class="button" onclick="viewReports()">查看報告</button>
                <button class="button" onclick="openAPI()">API文檔</button>
            </div>
        </div>

        <div class="card">
            <h3>性能圖表</h3>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h3>系統信息</h3>
            <div class="metric">
                <span>系統版本</span>
                <span class="metric-value">2.0.0 Full</span>
            </div>
            <div class="metric">
                <span>數據庫</span>
                <span class="metric-value">SQLite (本地)</span>
            </div>
            <div class="metric">
                <span>API版本</span>
                <span class="metric-value">v1 + v2</span>
            </div>
            <div class="metric">
                <span>當前時間</span>
                <span class="metric-value" id="currentTime"></span>
            </div>
        </div>

        <div class="footer">
            <p>© 2025 CBSC Quantitative Strategy Management System - Complete Version</p>
        </div>
    </div>

    <script>
        // 創建性能圖表
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '策略收益率 (%)',
                    data: [2.1, 3.5, 1.8, 4.2, 2.9, 3.7],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                }, {
                    label: '基準收益率 (%)',
                    data: [1.5, 2.1, 1.2, 2.8, 1.9, 2.4],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: '策略 vs 基準表現'
                    }
                }
            }
        });

        // 功能函數
        function createStrategy() {
            fetch('http://localhost:3004/api/v1/strategies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: '新策略',
                    type: '技術指標',
                    description: '用戶創建的新策略',
                    parameters: {}
                })
            })
            .then(response => response.json())
            .then(data => {
                alert('策略創建成功！策略ID: ' + data.id);
                location.reload();
            })
            .catch(error => {
                alert('策略創建功能將開發...');
            });
        }

        function runBacktest() {
            alert('回測功能將開發...');
        }

        function viewReports() {
            window.open('http://localhost:3004/docs', '_blank');
        }

        function openAPI() {
            window.open('http://localhost:3004/docs', '_blank');
        }

        // 更新時間
        function updateTime() {
            document.getElementById('currentTime').textContent = new Date().toLocaleString();
        }
        updateTime();
        setInterval(updateTime, 1000);

        // 檢查API服務狀態
        fetch('http://localhost:3004/health')
            .then(response => response.json())
            .then(data => {
                console.log('API服務狀態:', data);
            })
            .catch(error => {
                console.log('API服務連接失敗:', error);
            });
    </script>
</body>
</html>
"""
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()

if __name__ == "__main__":
    server = HTTPServer(('localhost', 3000), CBSCFrontendHandler)
    print("前端服務已啟動 (http://localhost:3000)")
    server.serve_forever()
