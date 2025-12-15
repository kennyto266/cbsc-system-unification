#!/usr/bin/env python3
"""
CBSC Strategy API - Complete Web Server
Includes API endpoints and static file serving for the dashboard
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# Create FastAPI app
app = FastAPI(
    title='CBSC Strategy API - Web Server',
    description='Complete strategy management system with web interface',
    version='1.0.0'
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include strategy routes if available
try:
    from api.strategies import router as strategies_router
    app.include_router(strategies_router, prefix='/api/v1', tags=['Strategy Management v1'])
    print('[OK] Strategy router loaded successfully')
except Exception as e:
    print(f'[WARN] Strategy router not available: {e}')

# Demo API endpoints for testing
@app.get('/', response_class=JSONResponse)
async def root():
    """Root endpoint"""
    return {
        'message': 'CBSC Strategy API - Web Server',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'api': '/api/v1/strategies/',
            'docs': '/docs',
            'dashboard': '/web_dashboard.html',
            'health': '/health'
        }
    }

@app.get('/health', response_class=JSONResponse)
async def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'CBSC Strategy API Web Server',
        'timestamp': datetime.now().isoformat()
    }

# Demo strategy endpoints (when main router not available)
@app.get('/api/v1/strategies/', response_class=JSONResponse)
async def list_strategies():
    """List strategies with demo data"""
    return {
        'strategies': [
            {
                'id': 1,
                'name': '移動平均線策略',
                'description': '基於移動平均線的趨勢追蹤策略',
                'status': 'active',
                'created_at': '2024-01-15T10:00:00Z',
                'performance': {
                    'total_return': 15.3,
                    'sharpe_ratio': 1.24,
                    'max_drawdown': -8.7
                }
            },
            {
                'id': 2,
                'name': 'RSI均值回歸',
                'description': '利用RSI指標進行均值回歸交易',
                'status': 'testing',
                'created_at': '2024-01-10T09:30:00Z',
                'performance': {
                    'total_return': 8.9,
                    'sharpe_ratio': 0.95,
                    'max_drawdown': -4.2
                }
            },
            {
                'id': 3,
                'name': '布林帶突破',
                'description': '基於布林帶的突破策略',
                'status': 'inactive',
                'created_at': '2024-01-05T14:20:00Z',
                'performance': {
                    'total_return': 12.1,
                    'sharpe_ratio': 1.08,
                    'max_drawdown': -6.3
                }
            }
        ],
        'total': 3,
        'timestamp': datetime.now().isoformat()
    }

@app.get('/api/v1/strategies/templates/', response_class=JSONResponse)
async def list_strategy_templates():
    """List strategy templates"""
    return [
        {
            'id': 'template_ma_crossover',
            'name': '移動平均線交叉模板',
            'description': '經典的移動平均線交叉策略模板',
            'category': 'trend_following',
            'parameters': [
                {'name': 'fast_period', 'type': 'integer', 'default': 10},
                {'name': 'slow_period', 'type': 'integer', 'default': 20}
            ]
        },
        {
            'id': 'template_rsi_mean',
            'name': 'RSI均值回歸模板',
            'description': 'RSI超買超賣的均值回歸策略模板',
            'category': 'mean_reversion',
            'parameters': [
                {'name': 'rsi_period', 'type': 'integer', 'default': 14},
                {'name': 'oversold', 'type': 'float', 'default': 30.0},
                {'name': 'overbought', 'type': 'float', 'default': 70.0}
            ]
        }
    ]

@app.get('/api/v1/strategies/personal/dashboard', response_class=JSONResponse)
async def get_personal_dashboard():
    """Get personal dashboard data"""
    return {
        'user_stats': {
            'total_strategies': 5,
            'active_strategies': 2,
            'total_pnl': 12500.00,
            'monthly_return': 3.2
        },
        'recent_activities': [
            {'action': '策略執行', 'strategy': '移動平均線策略', 'time': '10分鐘前'},
            {'action': '參數調整', 'strategy': 'RSI均值回歸', 'time': '1小時前'},
            {'action': '策略創建', 'strategy': '新策略草案', 'time': '2天前'}
        ]
    }

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Web dashboard endpoint
@app.get("/web_dashboard.html", response_class=HTMLResponse)
async def get_web_dashboard():
    """Serve the web dashboard HTML"""
    dashboard_path = Path("web_dashboard.html")
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding='utf-8'))

    # Fallback dashboard if file not found
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC Strategy API - Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; }
        .status.active { background: #d4edda; color: #155724; }
        .status.testing { background: #fff3cd; color: #856404; }
        .status.inactive { background: #f8d7da; color: #721c24; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .metric { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .api-test { margin-top: 20px; }
        .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .result { margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CBSC Strategy API Dashboard</h1>
            <p>量化交易策略管理系統 - 生產就緒</p>
        </div>

        <div class="card">
            <h2>📊 系統狀態</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">3</div>
                    <div>總策略數</div>
                </div>
                <div class="metric">
                    <div class="metric-value">1</div>
                    <div>活躍策略</div>
                </div>
                <div class="metric">
                    <div class="metric-value">15.3%</div>
                    <div>總收益率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">1.24</div>
                    <div>夏普比率</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📋 策略列表</h2>
            <div class="strategy-list">
                <div class="strategy-item">
                    <h3>移動平均線策略 <span class="status active">活躍</span></h3>
                    <p>基於移動平均線的趨勢追蹤策略</p>
                    <p>總收益: 15.3% | 夏普比率: 1.24 | 最大回撤: -8.7%</p>
                </div>
                <div class="strategy-item">
                    <h3>RSI均值回歸 <span class="status testing">測試中</span></h3>
                    <p>利用RSI指標進行均值回歸交易</p>
                    <p>總收益: 8.9% | 夏普比率: 0.95 | 最大回撤: -4.2%</p>
                </div>
                <div class="strategy-item">
                    <h3>布林帶突破 <span class="status inactive">停用</span></h3>
                    <p>基於布林帶的突破策略</p>
                    <p>總收益: 12.1% | 夏普比率: 1.08 | 最大回撤: -6.3%</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🔧 API 測試</h2>
            <div class="api-test">
                <button class="btn" onclick="testAPI('/health')">測試健康檢查</button>
                <button class="btn" onclick="testAPI('/api/v1/strategies/')">測試策略列表</button>
                <button class="btn" onclick="testAPI('/api/v1/strategies/templates/')">測試策略模板</button>
                <div id="api-result" class="result" style="display:none;"></div>
            </div>
        </div>

        <div class="card">
            <h2>📚 系統信息</h2>
            <ul>
                <li><strong>API 文檔:</strong> <a href="/docs" target="_blank">/docs</a> (Swagger UI)</li>
                <li><strong>API 端點:</strong> /api/v1/strategies/</li>
                <li><strong>健康檢查:</strong> /health</li>
                <li><strong>狀態:</strong> <span style="color: green;">✅ 生產就緒</span></li>
            </ul>
        </div>
    </div>

    <script>
        async function testAPI(endpoint) {
            const resultDiv = document.getElementById('api-result');
            resultDiv.style.display = 'block';
            resultDiv.textContent = '載入中...';

            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                resultDiv.textContent = 'Status: ' + response.status + '\\n\\n' + JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = '錯誤: ' + error.message;
            }
        }
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("CBSC Strategy API - Web Server")
    print("=" * 60)
    print("服務地址: http://localhost:3004")
    print("Web Dashboard: http://localhost:3004/web_dashboard.html")
    print("API 文檔: http://localhost:3004/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=3004)