#!/usr/bin/env python3
"""
Simple Dashboard Server
Serves the CBSC Strategy Dashboard
"""

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="CBSC Dashboard Server",
    description="Serves the CBSC Strategy Management Dashboard",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(SCRIPT_DIR, "src", "api", "static")

# Mount static files if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    """Root endpoint redirects to dashboard"""
    return {"message": "CBSC Dashboard Server", "dashboard": "/web_dashboard.html"}

@app.get("/web_dashboard.html")
async def dashboard():
    """Serve the dashboard HTML file"""
    dashboard_path = os.path.join(STATIC_DIR, "dashboard.html")

    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        # Create a simple dashboard if not found
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC 策略管理系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background: rgba(0, 255, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .api-link {
            display: block;
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            text-decoration: none;
            color: white;
            transition: background 0.3s;
        }
        .api-link:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 CBSC 量化交易策略管理系统</h1>

        <div class="status">
            ✅ 系统状态: 运行中
        </div>

        <h2>📊 系统功能</h2>
        <a href="http://localhost:3004/api/v1/strategies/" class="api-link" target="_blank">
            策略管理 API (v1.0)
        </a>
        <a href="http://localhost:3004/docs" class="api-link" target="_blank">
            API 文档
        </a>
        <a href="http://localhost:3004/health" class="api-link" target="_blank">
            系统健康检查
        </a>

        <h2>🎯 个人使用场景</h2>
        <p>这是一个专为个人股票策略回测设计的系统，帮助您：</p>
        <ul>
            <li>创建和管理量化交易策略</li>
            <li>进行历史数据回测</li>
            <li>分析 Sharpe Ratio (SR) 和最大回撤 (MDD)</li>
            <li>优化策略参数</li>
        </ul>

        <div style="margin-top: 30px; padding: 20px; background: rgba(255, 255, 255, 0.1); border-radius: 10px;">
            <h3>📈 快速开始</h3>
            <p>1. 访问 API 文档了解接口</p>
            <p>2. 创建您的第一个策略</p>
            <p>3. 运行回测分析</p>
            <p>4. 查看 SR 和 MDD 指标</p>
        </div>
    </div>
</body>
</html>
        """
        return FileResponse(
            path=os.path.join(SCRIPT_DIR, "temp_dashboard.html"),
            filename="dashboard.html"
        )

@app.get("/web_dashboard.html")
async def dashboard():
    """Serve the dashboard HTML file"""
    dashboard_path = os.path.join(STATIC_DIR, "dashboard.html")

    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        # Return table dashboard if not found
        return FileResponse(
            path=os.path.join(SCRIPT_DIR, "strategy_table_dashboard.html"),
            filename="dashboard.html"
        )

@app.get("/strategy_table.html")
async def strategy_table():
    """Serve the strategy table view"""
    return FileResponse(
        path=os.path.join(SCRIPT_DIR, "strategy_table_dashboard.html"),
        filename="strategy_table.html"
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CBSC Dashboard"}

if __name__ == "__main__":
    print("Starting CBSC Dashboard Server...")
    print(f"Static directory: {STATIC_DIR}")
    print(f"Dashboard URL: http://localhost:3007/web_dashboard.html")
    print(f"API Base URL: http://localhost:3004")

    # Write temporary dashboard file
    temp_dashboard_path = os.path.join(SCRIPT_DIR, "temp_dashboard.html")
    with open(temp_dashboard_path, "w", encoding="utf-8") as f:
        f.write("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC 策略管理系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background: rgba(0, 255, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .api-link {
            display: block;
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            text-decoration: none;
            color: white;
            transition: background 0.3s;
        }
        .api-link:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 CBSC 量化交易策略管理系统</h1>

        <div class="status">
            ✅ 系统状态: 运行中
        </div>

        <h2>📊 系统功能</h2>
        <a href="http://localhost:3004/api/v1/strategies/" class="api-link" target="_blank">
            策略管理 API (v1.0)
        </a>
        <a href="http://localhost:3004/docs" class="api-link" target="_blank">
            API 文档
        </a>
        <a href="http://localhost:3004/health" class="api-link" target="_blank">
            系统健康检查
        </a>

        <h2>🎯 个人使用场景</h2>
        <p>这是一个专为个人股票策略回测设计的系统，帮助您：</p>
        <ul>
            <li>创建和管理量化交易策略</li>
            <li>进行历史数据回测</li>
            <li>分析 Sharpe Ratio (SR) 和最大回撤 (MDD)</li>
            <li>优化策略参数</li>
        </ul>

        <div style="margin-top: 30px; padding: 20px; background: rgba(255, 255, 255, 0.1); border-radius: 10px;">
            <h3>📈 快速开始</h3>
            <p>1. 访问 API 文档了解接口</p>
            <p>2. 创建您的第一个策略</p>
            <p>3. 运行回测分析</p>
            <p>4. 查看 SR 和 MDD 指标</p>
        </div>
    </div>
</body>
</html>
        """)

    uvicorn.run(app, host="0.0.0.0", port=3008)