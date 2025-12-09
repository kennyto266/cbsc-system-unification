#!/usr / bin / env python3
"""
港股量化交易 AI Agent 系统 - 仪表板启动脚本

这个脚本解决了相对导入问题，可以直接运行仪表板系统。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(project_root))

# 导入必要的模块
from src.core import SystemConfig, setup_logging
from src.dashboard.dashboard_ui import DashboardUI
from src.dashboard.api_routes import DashboardAPI
import asyncio
import uvicorn
import logging

def create_mock_dashboard_api():
    """创建模拟的DashboardAPI用于测试"""
    class MockDashboardAPI:
        def __init__(self):
            self.logger = logging.getLogger("mock_dashboard_api")

        async def get_all_agents(self):
            """返回模拟的Agent数据"""
            from src.core import SystemConstants

            mock_agents = []
            for i, agent_type in enumerate(SystemConstants.AGENT_TYPES):
                agent_data = {
                    "agent_id": f"{agent_type}_{i + 1}",
                    "agent_type": agent_type,
                    "status": "running",
                    "last_activity": "2024 - 01 - 01T12:00:00Z",
                    "performance_metrics": {
                        "total_trades": 100 + i * 10,
                        "win_rate": 0.65 + i * 0.02,
                        "sharpe_ratio": 1.2 + i * 0.1,
                        "max_drawdown": 0.05 - i * 0.001
                    },
                    "current_strategy": f"Strategy_{i + 1}",
                    "risk_level": "medium" if i % 2 == 0 else "low"
                }

                # 创建简单的Agent对象
                class MockAgent:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)

                    def dict(self):
                        return {k: v for k, v in self.__dict__.items()}

                mock_agents.append(MockAgent(agent_data))

            return mock_agents

        async def get_system_status(self):
            """返回模拟的系统状态"""
            return {
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
                "last_update": "2024 - 01 - 01T12:00:00Z"
            }

    return MockDashboardAPI()

async def main():
    """主函数"""
    try:
        # 设置日志
        config = SystemConfig()
        setup_logging(config)
        logger = logging.getLogger("hk_quant_system.dashboard")

        logger.info("🚀 启动港股量化交易 AI Agent 仪表板...")

        # 创建模拟的DashboardAPI
        dashboard_api = create_mock_dashboard_api()

        # 创建仪表板UI
        dashboard_ui = DashboardUI(dashboard_api, config)

        # 启动仪表板
        await dashboard_ui.start()

        logger.info("✅ 仪表板服务启动成功")
        logger.info("🌐 访问地址: http://localhost:8001")
        logger.info("📊 功能: 多智能体监控、实时数据、性能分析")
        logger.info("⏹️ 按 Ctrl + C 停止系统")

        # 启动FastAPI服务器
        app = dashboard_ui.get_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )

    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号，正在关闭系统...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise
    finally:
        if 'dashboard_ui' in locals():
            await dashboard_ui.cleanup()
        logger.info("👋 系统已关闭")

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
