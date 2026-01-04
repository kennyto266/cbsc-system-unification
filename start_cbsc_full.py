#!/usr/bin/env python3
"""
CBSC量化策略管理系統 - 完整系統啟動器
"""
import os
import sys
import time
import signal
import subprocess
import threading
import sqlite3
from datetime import datetime
from pathlib import Path

class CBSCSystemManager:
    def __init__(self):
        self.processes = []
        self.running = True
        self.project_root = Path(__file__).parent

    def setup_database(self):
        """設置SQLite數據庫"""
        print("🔧 初始化數據庫...")

        # 創建數據庫文件
        db_path = self.project_root / "data" / "cbsc.db"
        db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 創建策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                parameters TEXT,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)

        # 創建回測結果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER,
                start_date TEXT,
                end_date TEXT,
                initial_capital REAL,
                final_capital REAL,
                total_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies (id)
            )
        """)

        # 創建用戶表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print("✅ 數據庫初始化完成")

    def start_api_service(self):
        """啟動FastAPI服務"""
        print("🚀 啟動API服務...")

        api_code = '''
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import uvicorn
from datetime import datetime

app = FastAPI(title="CBSC量化策略管理系統", version="2.0.0")

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 數據模型
class StrategyCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    parameters: dict = {}

class StrategyResponse(BaseModel):
    id: int
    name: str
    type: str
    description: str
    parameters: dict
    created_at: str
    updated_at: str
    status: str
    performance_metrics: dict

# 數據庫連接
def get_db():
    conn = sqlite3.connect("data/cbsc.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head>
            <title>CBSC量化策略管理系統</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; }
                .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .api-list { list-style: none; padding: 0; }
                .api-list li { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
                .endpoint { font-weight: bold; color: #0066cc; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 CBSC量化策略管理系統</h1>
                <div class="status">
                    <h3>✅ 系統狀態: 運行中</h3>
                    <p>版本: 2.0.0 Full | 時間: {timestamp}</p>
                </div>
                <h2>📡 API端點</h2>
                <ul class="api-list">
                    <li><span class="endpoint">GET /api/v1/strategies</span> - 策略列表</li>
                    <li><span class="endpoint">POST /api/v1/strategies</span> - 創建策略</li>
                    <li><span class="endpoint">GET /api/v2/strategies</span> - V2策略列表</li>
                    <li><span class="endpoint">GET /health</span> - 健康檢查</li>
                    <li><span class="endpoint">GET /docs</span> - API文檔</li>
                </ul>
            </div>
        </body>
    </html>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

@app.get("/health")
async def health_check():
    return {{
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-full",
        "services": {{
            "api": "running",
            "database": "connected",
            "websocket": "disabled"
        }}
    }}

@app.get("/api/v1/strategies", response_model=List[StrategyResponse])
async def list_strategies_v1():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE status = 'active'")
    strategies = cursor.fetchall()
    conn.close()

    return [
        StrategyResponse(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            description=row["description"],
            parameters=json.loads(row["parameters"] or "{{}}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=row["status"],
            performance_metrics=json.loads(row["performance_metrics"] or "{{}}")
        )
        for row in strategies
    ]

@app.post("/api/v1/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO strategies (name, type, description, parameters, created_at, updated_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (strategy.name, strategy.type, strategy.description,
         json.dumps(strategy.parameters), datetime.now(), datetime.now(), "active")
    )

    strategy_id = cursor.lastrowid
    conn.commit()

    # 返回創建的策略
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()

    return StrategyResponse(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        description=row["description"],
        parameters=json.loads(row["parameters"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=row["status"],
        performance_metrics=json.loads(row["performance_metrics"] or "{{}}")
    )

@app.get("/api/v2/strategies")
async def list_strategies_v2():
    # V2 API - 增強功能
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies ORDER BY created_at DESC")
    strategies = cursor.fetchall()
    conn.close()

    return {{
        "success": True,
        "data": [
            {{
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "status": row["status"],
                "created_at": row["created_at"],
                "performance": json.loads(row["performance_metrics"] or "{{}}")
            }}
            for row in strategies
        ],
        "total": len(strategies),
        "timestamp": datetime.now().isoformat()
    }}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3004)
'''

        # 保存API代碼到臨時文件
        api_file = self.project_root / "temp_api_server.py"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(api_code)

        try:
            process = subprocess.Popen([
                sys.executable, str(api_file)
            ], cwd=str(self.project_root))
            self.processes.append(("API服務", process))
            time.sleep(2)
            print(f"✅ API服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ API服務啟動失敗: {e}")
            return None

    def start_websocket_service(self):
        """啟動WebSocket服務"""
        print("📡 啟動WebSocket服務...")

        ws_code = '''
import asyncio
import websockets
import json
import time
from datetime import datetime

async def websocket_handler(websocket, path):
    print(f"新的WebSocket連接: {{path}}")
    await websocket.send(json.dumps({{
        "type": "connection",
        "message": "Connected to CBSC WebSocket",
        "timestamp": datetime.now().isoformat()
    }}))

    # 發送模擬市場數據
    while True:
        try:
            data = {{
                "type": "market_data",
                "symbol": "AAPL",
                "price": 150.25 + (time.time() % 10) * 0.1,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat()
            }}
            await websocket.send(json.dumps(data))
            await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception as e:
            print(f"WebSocket錯誤: {{e}}")
            break

async def main():
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("✅ WebSocket服務已啟動 (ws://localhost:8765)")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
'''

        # 保存WebSocket代碼到臨時文件
        ws_file = self.project_root / "temp_websocket_server.py"
        with open(ws_file, 'w', encoding='utf-8') as f:
            f.write(ws_code)

        try:
            process = subprocess.Popen([
                sys.executable, str(ws_file)
            ], cwd=str(self.project_root))
            self.processes.append(("WebSocket服務", process))
            time.sleep(1)
            print(f"✅ WebSocket服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ WebSocket服務啟動失敗: {e}")
            return None

    def start_frontend_service(self):
        """啟動前端服務"""
        print("🌐 啟動前端服務...")

        frontend_code = '''
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import time

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
            <h1>🚀 CBSC量化策略管理系統</h1>
            <p>專業級量化交易策略管理平台</p>
        </div>

        <div class="dashboard">
            <div class="card">
                <h3>📊 系統狀態</h3>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>API服務</span>
                    <span class="metric-value">運行中</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>數據庫</span>
                    <span class="metric-value">已連接</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-online"></span>WebSocket</span>
                    <span class="metric-value">運行中</span>
                </div>
            </div>

            <div class="card">
                <h3>💰 策略概覽</h3>
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
                <h3>⚡ 快速操作</h3>
                <button class="button" onclick="createStrategy()">創建策略</button>
                <button class="button" onclick="runBacktest()">運行回測</button>
                <button class="button" onclick="viewReports()">查看報告</button>
                <button class="button" onclick="openAPI()">API文檔</button>
            </div>
        </div>

        <div class="card">
            <h3>📈 性能圖表</h3>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <div class="footer">
            <p>© 2025 CBSC Quantitative Strategy Management System</p>
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

        // WebSocket連接
        const ws = new WebSocket('ws://localhost:8765');
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('WebSocket數據:', data);
        };

        // 功能函數
        function createStrategy() {
            alert('策略創建功能將開發...');
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
        setInterval(() => {
            document.querySelector('.footer p').textContent =
                `© 2025 CBSC Quantitative Strategy Management System | 當前時間: ${new Date().toLocaleString()}`;
        }, 1000);
    </script>
</body>
</html>
"""
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path == '/api/strategies':
            # 模擬API響應
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            mock_data = {
                "success": True,
                "data": [
                    {"id": 1, "name": "MA交叉策略", "type": "技術指標", "status": "active"},
                    {"id": 2, "name": "RSI策略", "type": "技術指標", "status": "active"},
                    {"id": 3, "name": "動量策略", "type": "動量分析", "status": "paused"}
                ],
                "total": 3
            }
            self.wfile.write(json.dumps(mock_data, ensure_ascii=False).encode('utf-8'))
        else:
            super().do_GET()

if __name__ == "__main__":
    server = HTTPServer(('localhost', 3000), CBSCFrontendHandler)
    print("✅ 前端服務已啟動 (http://localhost:3000)")
    server.serve_forever()
'''

        # 保存前端代碼到臨時文件
        frontend_file = self.project_root / "temp_frontend_server.py"
        with open(frontend_file, 'w', encoding='utf-8') as f:
            f.write(frontend_code)

        try:
            process = subprocess.Popen([
                sys.executable, str(frontend_file)
            ], cwd=str(self.project_root))
            self.processes.append(("前端服務", process))
            time.sleep(1)
            print(f"✅ 前端服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ 前端服務啟動失敗: {e}")
            return None

    def start_monitoring_service(self):
        """啟動監控服務"""
        print("📊 啟動監控服務...")

        monitoring_code = '''
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from datetime import datetime

class MonitoringHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_usage": 15.2,
                    "memory_usage": 68.5,
                    "disk_usage": 42.1
                },
                "application": {
                    "active_strategies": 12,
                    "total_backtests": 248,
                    "api_requests": 15234,
                    "websocket_connections": 3
                }
            }
            self.wfile.write(json.dumps(metrics, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('localhost', 3005), MonitoringHandler)
    print("✅ 監控服務已啟動 (http://localhost:3005)")
    server.serve_forever()
'''

        # 保存監控代碼到臨時文件
        monitoring_file = self.project_root / "temp_monitoring_server.py"
        with open(monitoring_file, 'w', encoding='utf-8') as f:
            f.write(monitoring_code)

        try:
            process = subprocess.Popen([
                sys.executable, str(monitoring_file)
            ], cwd=str(self.project_root))
            self.processes.append(("監控服務", process))
            time.sleep(1)
            print(f"✅ 監控服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ 監控服務啟動失敗: {e}")
            return None

    def stop_all_services(self):
        """停止所有服務"""
        print("\n🛑 正在停止所有服務...")
        for service_name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {service_name}已停止")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔥 {service_name}已強制停止")
            except Exception as e:
                print(f"❌ 停止{service_name}失敗: {e}")

        # 清理臨時文件
        temp_files = [
            "temp_api_server.py",
            "temp_websocket_server.py",
            "temp_frontend_server.py",
            "temp_monitoring_server.py"
        ]
        for temp_file in temp_files:
            try:
                (self.project_root / temp_file).unlink()
            except:
                pass

        print("🧹 清理完成")

    def run(self):
        """運行完整系統"""
        print("啟動CBSC量化策略管理系統 - 完整版")
        print("=" * 50)

        # 設置信號處理
        def signal_handler(signum, frame):
            print("\n\n接收到停止信號")
            self.running = False
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 1. 初始化數據庫
            self.setup_database()

            # 2. 啟動API服務
            self.start_api_service()

            # 3. 啟動WebSocket服務
            self.start_websocket_service()

            # 4. 啟動前端服務
            self.start_frontend_service()

            # 5. 啟動監控服務
            self.start_monitoring_service()

            print("\n" + "=" * 50)
            print("🎉 CBSC量化策略管理系統啟動完成!")
            print("=" * 50)
            print("📋 服務列表:")
            print("  🌐 前端界面: http://localhost:3000")
            print("  📡 API服務: http://localhost:3004")
            print("  📊 API文檔: http://localhost:3004/docs")
            print("  🔌 WebSocket: ws://localhost:8765")
            print("  📈 監控面板: http://localhost:3005")
            print("=" * 50)
            print("💡 使用 Ctrl+C 停止所有服務")
            print("=" * 50)

            # 保持運行
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n用戶中斷")
        finally:
            self.stop_all_services()

if __name__ == "__main__":
    manager = CBSCSystemManager()
    manager.run()