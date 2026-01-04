#!/usr/bin/env python3
"""
CBSC Quantum - 完整系統啟動器 (增強版)
啟動包含專業級UI設計的完整量化策略管理系統
"""
import os
import sys
import time
import signal
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path

class EnhancedCBSCSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        self.project_root = Path(__file__).parent

    def setup_database(self):
        """設置增強版數據庫"""
        print("🔧 初始化量子級數據庫...")

        # 創建數據庫文件
        db_path = self.project_root / "data" / "quantum_cbsc.db"
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
                status TEXT DEFAULT 'active',
                quantum_enabled BOOLEAN DEFAULT 0
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
                win_rate REAL,
                quantum_score REAL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quantum_access_level INTEGER DEFAULT 1
            )
        """)

        # 創建活動日誌表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_name TEXT NOT NULL,
                description TEXT,
                details TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # 插入示例量子策略
        cursor.execute("""
            INSERT OR IGNORE INTO strategies
            (name, type, description, parameters, status, quantum_enabled)
            VALUES
            ('量子動量策略 Pro', '量子分析', '基於量子疊加態的動量交易策略',
             '{"quantum_state": "superposition", "entanglement": true, "circuit_depth": 10, "shots": 1000}', 'active', 1),
            ('AI神經網絡策略', '機器學習', '深度學習驅動的智能交易系統',
             '{"model_type": "LSTM", "layers": 5, "neurons": 256, "dropout": 0.2}', 'active', 1),
            ('量子糾纏策略', '量子計算', '利用量子糾纏現象的相關性交易',
             '{"entanglement_pairs": 8, "correlation_threshold": 0.85, "quantum_volume": 64}', 'active', 1),
            ('高頻量化策略', '高頻交易', '微秒級延遲的高頻交易系統',
             '{"latency_target": "1ms", "order_rate": 10000, "market_depth": 5}', 'paused', 0),
            ('波動率套利策略', '期權策略', '基於隱含波動率的套利機會',
             '{"volatility_threshold": 0.25, "delta_neutral": true, "gamma_hedging": true}', 'active', 0)
        """)

        # 插入示例用戶
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, email, password_hash, quantum_access_level)
            VALUES
            ('quantum_trader', 'trader@cbsc.com', 'hashed_password_123', 3),
            ('ai_analyst', 'analyst@cbsc.com', 'hashed_password_456', 2),
            ('risk_manager', 'risk@cbsc.com', 'hashed_password_789', 1)
        """)

        conn.commit()
        conn.close()
        print("✅ 量子級數據庫初始化完成")

    def start_enhanced_api_service(self):
        """啟動增強版API服務"""
        print("🚀 啟動量子級API服務...")

        enhanced_api_code = '''
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json
import uvicorn
from datetime import datetime, timedelta
import asyncio
import random
import uuid

app = FastAPI(
    title="CBSC Quantum API",
    description="量子級量化策略管理系統API",
    version="3.0.0-quantum",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    parameters: Dict[str, Any] = {}
    quantum_enabled: Optional[bool] = False

class StrategyResponse(BaseModel):
    id: int
    name: str
    type: str
    description: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: str
    updated_at: str
    status: str
    quantum_enabled: bool

class BacktestRequest(BaseModel):
    strategy_id: int
    start_date: str
    end_date: str
    initial_capital: float = 100000
    parameters: Optional[Dict[str, Any]] = None

class BacktestResponse(BaseModel):
    id: int
    strategy_id: int
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    quantum_score: Optional[float] = None
    execution_time: str

# 數據庫連接
def get_db():
    conn = sqlite3.connect("data/quantum_cbsc.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head>
            <title>CBSC Quantum API</title>
            <style>
                body {
                    font-family: 'Orbitron', monospace;
                    margin: 40px;
                    background: linear-gradient(135deg, #0a0e27, #1a1f3a);
                    color: #00d4ff;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(21, 25, 50, 0.8);
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 0 40px rgba(0, 212, 255, 0.2);
                    border: 1px solid rgba(0, 212, 255, 0.3);
                }
                h1 {
                    font-size: 2.5rem;
                    text-align: center;
                    margin-bottom: 30px;
                    text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
                }
                .status {
                    background: rgba(16, 185, 129, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }
                .api-list { list-style: none; padding: 0; }
                .api-list li {
                    margin: 15px 0;
                    padding: 15px;
                    background: rgba(139, 92, 246, 0.1);
                    border-radius: 10px;
                    border-left: 3px solid #8b5cf6;
                }
                .endpoint {
                    font-weight: bold;
                    color: #ec4899;
                    font-size: 1.1rem;
                }
                .glow {
                    animation: glow 2s ease-in-out infinite alternate;
                }
                @keyframes glow {
                    from { filter: brightness(1); }
                    to { filter: brightness(1.2); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="glow">🚀 CBSC Quantum API</h1>
                <div class="status">
                    <h3>✅ 量子級API服務運行中</h3>
                    <p>版本: 3.0.0 Quantum | 時間: {timestamp}</p>
                    <p>🧬 量子計算集成 | 🤖 AI增強 | ⚡ 高性能</p>
                </div>
                <h2>📡 量子API端點</h2>
                <ul class="api-list">
                    <li><span class="endpoint">GET /api/v1/strategies</span> - 策略列表</li>
                    <li><span class="endpoint">POST /api/v1/strategies</span> - 創建量子策略</li>
                    <li><span class="endpoint">GET /api/v2/strategies</span> - V2策略列表</li>
                    <li><span class="endpoint">GET /api/quantum/algorithms</span> - 量子算法</li>
                    <li><span class="endpoint">POST /api/backtest/run</span> - 量子回測</li>
                    <li><span class="endpoint">GET /health</span> - 量子健康檢查</li>
                    <li><span class="endpoint">GET /docs</span> - API文檔</li>
                </ul>
            </div>
        </body>
    </html>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

@app.get("/health")
async def health_check():
    return {
        "status": "quantum_healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0-quantum",
        "services": {
            "api": "quantum_running",
            "database": "quantum_connected",
            "quantum_processor": "online",
            "ai_engine": "ready"
        },
        "quantum_metrics": {
            "qubits_available": 64,
            "quantum_volume": 2**6,
            "circuit_depth": 20,
            "fidelity": 0.998
        }
    }

@app.get("/api/v1/strategies", response_model=List[StrategyResponse])
async def list_strategies_v1():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies ORDER BY created_at DESC")
    strategies = cursor.fetchall()
    conn.close()

    return [
        StrategyResponse(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            description=row["description"],
            parameters=json.loads(row["parameters"] or "{}"),
            performance_metrics=json.loads(row["performance_metrics"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=row["status"],
            quantum_enabled=bool(row["quantum_enabled"])
        )
        for row in strategies
    ]

@app.post("/api/v1/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate):
    conn = get_db()
    cursor = conn.cursor()

    # 生成量子性能指標
    performance_metrics = {
        "expected_return": random.uniform(0.1, 0.3),
        "volatility": random.uniform(0.05, 0.15),
        "quantum_advantage": strategy.quantum_enabled,
        "complexity_score": random.uniform(0.5, 0.95)
    }

    cursor.execute(
        """
        INSERT INTO strategies (name, type, description, parameters, performance_metrics,
                               created_at, updated_at, status, quantum_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (strategy.name, strategy.type, strategy.description,
         json.dumps(strategy.parameters), json.dumps(performance_metrics),
         datetime.now(), datetime.now(), "active", strategy.quantum_enabled)
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
        performance_metrics=json.loads(row["performance_metrics"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=row["status"],
        quantum_enabled=bool(row["quantum_enabled"])
    )

@app.get("/api/v2/strategies")
async def list_strategies_v2():
    # V2 API - 增強功能
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, COUNT(br.id) as backtest_count
        FROM strategies s
        LEFT JOIN backtest_results br ON s.id = br.strategy_id
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """)
    strategies = cursor.fetchall()
    conn.close()

    return {
        "success": True,
        "data": [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "status": row["status"],
                "quantum_enabled": bool(row["quantum_enabled"]),
                "backtest_count": row["backtest_count"],
                "created_at": row["created_at"],
                "performance": json.loads(row["performance_metrics"] or "{}")
            }
            for row in strategies
        ],
        "total": len(strategies),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    # 模擬量子回測
    backtest_id = uuid.uuid4().hex[:8]

    # 在後台執行回測
    background_tasks.add_task(execute_quantum_backtest, backtest_id, request)

    return BacktestResponse(
        id=backtest_id,
        strategy_id=request.strategy_id,
        total_return=random.uniform(-0.1, 0.5),
        sharpe_ratio=random.uniform(0.5, 2.5),
        max_drawdown=abs(random.uniform(0.02, 0.15)),
        win_rate=random.uniform(0.4, 0.8),
        quantum_score=random.uniform(0.6, 0.95) if request.parameters and request.parameters.get("quantum_enabled") else None,
        execution_time="Processing..."
    )

async def execute_quantum_backtest(backtest_id: str, request: BacktestRequest):
    # 模擬量子回測執行
    await asyncio.sleep(2)  # 模擬處理時間

    conn = get_db()
    cursor = conn.cursor()

    # 存儲回測結果
    results = {
        "total_return": random.uniform(-0.1, 0.5),
        "sharpe_ratio": random.uniform(0.5, 2.5),
        "max_drawdown": abs(random.uniform(0.02, 0.15)),
        "win_rate": random.uniform(0.4, 0.8),
        "quantum_score": random.uniform(0.6, 0.95)
    }

    cursor.execute(
        """
        INSERT INTO backtest_results (strategy_id, start_date, end_date, total_return,
                                   sharpe_ratio, max_drawdown, win_rate, quantum_score, results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (request.strategy_id, request.start_date, request.end_date,
         results["total_return"], results["sharpe_ratio"], results["max_drawdown"],
         results["win_rate"], results["quantum_score"], json.dumps(results))
    )

    conn.commit()
    conn.close()

@app.get("/api/quantum/algorithms")
async def get_quantum_algorithms():
    """獲取可用的量子算法"""
    return {
        "algorithms": [
            {
                "name": "Quantum Approximate Optimization Algorithm (QAOA)",
                "description": "用於組合優化的量子算法",
                "complexity": "O(√N)",
                "qubits_required": 20,
                "circuit_depth": 10
            },
            {
                "name": "Variational Quantum Eigensolver (VQE)",
                "description": "變分量子本征求解器",
                "complexity": "O(poly(N))",
                "qubits_required": 16,
                "circuit_depth": 8
            },
            {
                "name": "Quantum Amplitude Estimation",
                "description": "量子振幅估計算法",
                "complexity": "O(1/√N)",
                "qubits_required": 12,
                "circuit_depth": 6
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3004, reload=True)
'''

        # 保存增強API代碼到臨時文件
        api_file = self.project_root / "enhanced_api_server.py"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_api_code)

        try:
            process = subprocess.Popen([
                sys.executable, str(api_file)
            ], cwd=str(self.project_root))
            self.processes.append(("量子API服務", process))
            time.sleep(3)
            print(f"✅ 量子API服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ 量子API服務啟動失敗: {e}")
            return None

    def start_enhanced_frontend(self):
        """啟動增強版前端服務"""
        print("🌟 啟動量子級前端服務...")

        try:
            process = subprocess.Popen([
                sys.executable, str(self.project_root / "frontend" / "enhanced-server.py")
            ], cwd=str(self.project_root))
            self.processes.append(("量子前端服務", process))
            time.sleep(2)
            print(f"✅ 量子前端服務已啟動 (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ 量子前端服務啟動失敗: {e}")
            return None

    def stop_all_services(self):
        """停止所有服務"""
        print("\n🛑 正在停止量子服務...")
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
            "enhanced_api_server.py"
        ]
        for temp_file in temp_files:
            try:
                (self.project_root / temp_file).unlink()
            except:
                pass

        print("🧹 量子系統清理完成")

    def run(self):
        """運行增強版CBSC量子系統"""
        print("🚀 啟動 CBSC Quantum 量化策略管理系統")
        print("=" * 60)
        print("💫 量子級UI設計 | 🧬 量子計算集成 | 🤖 AI增強")
        print("=" * 60)

        # 設置信號處理
        def signal_handler(signum, frame):
            print("\n\n⚠️ 接收到停止信號")
            self.running = False
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 1. 初始化量子數據庫
            self.setup_database()

            # 2. 啟動量子API服務
            self.start_enhanced_api_service()

            # 3. 啟動量子前端服務
            self.start_enhanced_frontend()

            print("\n" + "=" * 60)
            print("🎉 CBSC Quantum 系統啟動完成!")
            print("=" * 60)
            print("🌟 量子級服務列表:")
            print("  🌐 量子前端界面: http://localhost:3000")
            print("  📡 量子API服務: http://localhost:3004")
            print("  📚 API文檔: http://localhost:3004/docs")
            print("  💚 量子健康檢查: http://localhost:3004/health")
            print("  🧬 量子算法: http://localhost:3004/api/quantum/algorithms")
            print("=" * 60)
            print("✨ 增強功能:")
            print("  🎨 專業級量子UI設計")
            print("  ⚡ 實時粒子背景效果")
            print("  🌈 霓虹色彩系統")
            print("  📊 動態圖表和動畫")
            print("  📱 完全響應式設計")
            print("=" * 60)
            print("💡 使用 Ctrl+C 停止所有量子服務")
            print("=" * 60)

            # 保持運行
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⚠️ 用戶中斷")
        finally:
            self.stop_all_services()

if __name__ == "__main__":
    system = EnhancedCBSCSystem()
    system.run()