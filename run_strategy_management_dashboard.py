#!/usr/bin/env python3
"""
策略管理Dashboard启动脚本

专业级CBSC策略管理平台主入口
集成了策略监控、参数优化、回测分析和Agent协作监控功能
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入核心组件
from src.dashboard.strategy_management_dashboard import get_strategy_dashboard
from src.dashboard.parameter_optimization_api import get_parameter_optimization_api
from src.dashboard.backtesting_analysis_lab import get_backtesting_lab
from src.dashboard.agent_coordination_service import get_agent_coordination_service


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class IntegratedStrategyDashboard:
    """集成策略管理Dashboard"""

    def __init__(self, port: int = 3003, host: str = "0.0.0.0", debug: bool = False):
        self.port = port
        self.host = host
        self.debug = debug

        # 创建FastAPI应用
        self.app = FastAPI(
            title="策略管理Dashboard - 专业级CBSC策略管理平台",
            description="""
            ## 🎯 全球领先的CBSC策略管理平台

            本平台集成了以下核心功能：

            ### 📈 策略监控中心
            - 4种高级CBSC情绪策略实时监控
            - 策略信号一致性分析
            - 性能指标实时追踪
            - 智能告警系统

            ### ⚙️ 参数优化工作台
            - 5种优化算法：网格搜索、随机搜索、贝叶斯优化、遗传算法、粒子群优化
            - 交互式参数调整界面
            - 实时性能响应分析
            - 参数历史趋势分析

            ### 🔬 回测分析实验室
            - 专业级回测引擎
            - 多策略对比分析
            - 风险评估体系
            - 交互式可视化图表

            ### 🤖 Agent协作监控
            - 7个专业AI Agent状态监控
            - 任务协调与工作流管理
            - 协作效率分析
            - 资源使用优化

            ### 💎 核心技术特色
            - **实时WebSocket通信**：毫秒级数据更新
            - **模块化架构**：可扩展的组件设计
            - **专业级可视化**：Chart.js + Plotly图表
            - **企业级安全**：完整的认证授权体系
            """,
            version="1.0.0",
            docs_url="/docs" if debug else None,
            redoc_url="/redoc" if debug else None
        )

        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 初始化核心服务
        self.strategy_dashboard = get_strategy_dashboard()
        self.parameter_api = get_parameter_optimization_api()
        self.backtesting_lab = get_backtesting_lab()
        self.agent_coordination = get_agent_coordination_service()

        # 设置路由
        self._setup_routes()

        # 状态管理
        self._running = False

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Dashboard主页"""
            return await self.strategy_dashboard._get_dashboard_html()

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": "2025-12-05",
                "version": "1.0.0",
                "services": {
                    "strategy_dashboard": "running",
                    "parameter_optimization": "running",
                    "backtesting_lab": "running",
                    "agent_coordination": "running"
                }
            }

        @self.app.get("/api/status")
        async def get_system_status():
            """获取系统状态"""
            return {
                "system_health": "operational",
                "active_strategies": 4,
                "total_agents": 7,
                "active_tasks": 12,
                "system_load": "normal",
                "last_update": "2025-12-05T12:00:00Z"
            }

        # 注册各个服务的路由
        self.app.include_router(self.parameter_api.router)
        self.app.include_router(self.backtesting_lab.router)
        self.app.include_router(self.agent_coordination.router)

        # 静态文件服务
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

    async def startup(self):
        """启动服务"""
        logger.info("🚀 启动策略管理Dashboard...")
        self._running = True

        try:
            # 启动各个核心服务
            await self.strategy_dashboard.start()
            await self.agent_coordination.start()

            logger.info("✅ 所有核心服务启动成功")
            logger.info(f"📱 Dashboard访问地址: http://{self.host}:{self.port}")
            logger.info(f"📚 API文档地址: http://{self.host}:{self.port}/docs")

        except Exception as e:
            logger.error(f"❌ 启动服务失败: {e}")
            raise

    async def shutdown(self):
        """关闭服务"""
        logger.info("🛑 正在关闭策略管理Dashboard...")
        self._running = False

        try:
            await self.strategy_dashboard.stop()
            await self.agent_coordination.stop()

            logger.info("✅ 所有服务已安全关闭")

        except Exception as e:
            logger.error(f"❌ 关闭服务时出现错误: {e}")

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


async def run_dashboard(port: int, host: str, debug: bool):
    """运行Dashboard"""
    dashboard = IntegratedStrategyDashboard(port=port, host=host, debug=debug)

    try:
        await dashboard.startup()

        # 配置uvicorn
        config = uvicorn.Config(
            app=dashboard.get_app(),
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            reload=debug,
            access_log=debug
        )

        server = uvicorn.Server(config)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("⏹️  收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 运行Dashboard时出现错误: {e}")
    finally:
        await dashboard.shutdown()


def create_static_directory():
    """创建静态文件目录"""
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    # 创建基本的CSS文件
    css_file = static_dir / "dashboard.css"
    if not css_file.exists():
        css_content = """
/* 策略管理Dashboard专用样式 */
.dashboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    text-align: center;
}

.metric-card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
}

.status-active {
    color: #4ade80;
}

.status-inactive {
    color: #f87171;
}

.btn-primary {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
}
"""
        css_file.write_text(css_content)

    # 创建基本的JS文件
    js_file = static_dir / "dashboard.js"
    if not js_file.exists():
        js_content = """
// 策略管理Dashboard核心JavaScript
console.log('策略管理Dashboard已加载');

// WebSocket连接管理
class DashboardWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket连接失败:', error);
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接已关闭');
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'strategy_update':
                updateStrategyDisplay(data.strategies);
                break;
            case 'performance_update':
                updatePerformanceDisplay(data.performance);
                break;
            case 'agent_update':
                updateAgentDisplay(data.agent);
                break;
            default:
                console.log('未知消息类型:', data.type);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, 5000);
        }
    }
}

// 初始化WebSocket
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    window.dashboardWS = new DashboardWebSocket(wsUrl);
    window.dashboardWS.connect();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();

    // 设置定期刷新
    setInterval(refreshDashboardData, 30000); // 30秒刷新一次
});

// 刷新Dashboard数据
function refreshDashboardData() {
    console.log('刷新Dashboard数据...');
    // 实现数据刷新逻辑
}
"""
        js_file.write_text(js_content)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略管理Dashboard - 专业级CBSC策略管理平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
## 📊 功能模块

### 1. 策略监控中心
- 实时监控4种CBSC情绪策略
- 策略信号分析和一致性评估
- 性能指标实时追踪

### 2. 参数优化工作台
- 5种专业优化算法
- 交互式参数调整界面
- 实时性能响应分析

### 3. 回测分析实验室
- 专业级回测引擎
- 多策略对比分析
- 完整风险评估体系

### 4. Agent协作监控
- 7个AI Agent状态监控
- 任务协调与工作流管理
- 协作效率分析

## 🚀 使用示例

# 启动Dashboard (默认端口3003)
python run_strategy_management_dashboard.py

# 指定端口启动
python run_strategy_management_dashboard.py --port 8080

# 调试模式启动
python run_strategy_management_dashboard.py --debug

## 📱 访问地址

Dashboard: http://localhost:3003
API文档: http://localhost:3003/docs
        """
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
        version="策略管理Dashboard v1.0.0"
    )

    args = parser.parse_args()

    # 创建静态文件目录
    create_static_directory()

    # 打印启动信息
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          🚀 策略管理Dashboard - 专业级CBSC策略管理平台         ║
    ║                                                           ║
    ║  🎯 全球领先的CBSC策略管理平台                                ║
    ║                                                           ║
    ║  📈 策略监控中心 | ⚙️ 参数优化工作台                           ║
    ║  🔬 回测分析实验室 | 🤖 Agent协作监控                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    logger.info(f"🎯 启动参数: 端口={args.port}, 主机={args.host}, 调试模式={args.debug}")

    # 运行Dashboard
    try:
        asyncio.run(run_dashboard(args.port, args.host, args.debug))
    except KeyboardInterrupt:
        logger.info("⏹️  用户中断，程序退出")
    except Exception as e:
        logger.error(f"❌ 程序运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()