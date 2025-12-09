#!/usr/bin/env python3
"""
策略管理Dashboard测试脚本

验证所有核心功能是否正常工作
"""

import asyncio
import sys
import requests
import json
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入测试需要的组件
from src.dashboard.strategy_management_dashboard import get_strategy_dashboard
from src.dashboard.parameter_optimization_api import get_parameter_optimization_api
from src.dashboard.backtesting_analysis_lab import get_backtesting_lab
from src.dashboard.agent_coordination_service import get_agent_coordination_service


class DashboardTester:
    """Dashboard测试器"""

    def __init__(self, base_url: str = "http://localhost:3003"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        print(f"🧪 运行测试: {test_name}")
        try:
            start_time = datetime.now()
            result = test_func()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            test_result = {
                "name": test_name,
                "status": "✅ PASSED" if result else "❌ FAILED",
                "duration": f"{duration:.2f}s",
                "timestamp": end_time.isoformat()
            }

            self.test_results.append(test_result)
            print(f"   {test_result['status']} ({test_result['duration']})")

            return result

        except Exception as e:
            test_result = {
                "name": test_name,
                "status": f"❌ ERROR: {str(e)}",
                "duration": "0.00s",
                "timestamp": datetime.now().isoformat()
            }

            self.test_results.append(test_result)
            print(f"   {test_result['status']}")
            return False

    def test_health_check(self):
        """测试健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        return response.status_code == 200 and response.json().get("status") == "healthy"

    def test_system_status(self):
        """测试系统状态"""
        response = self.session.get(f"{self.base_url}/api/status")
        return response.status_code == 200

    def test_strategies_api(self):
        """测试策略API"""
        response = self.session.get(f"{self.base_url}/api/strategies")
        return response.status_code == 200 and "strategies" in response.json()

    def test_performance_summary(self):
        """测试性能摘要API"""
        response = self.session.get(f"{self.base_url}/api/performance/summary")
        return response.status_code == 200

    def test_agents_status(self):
        """测试Agent状态API"""
        response = self.session.get(f"{self.base_url}/api/agents/status")
        return response.status_code == 200 and "agents" in response.json()

    def test_parameter_optimization(self):
        """测试参数优化API"""
        # 获取策略参数
        response = self.session.get(f"{self.base_url}/api/optimization/parameters/direct_rsi")
        return response.status_code == 200

    def test_backtesting_templates(self):
        """测试回测模板API"""
        response = self.session.get(f"{self.base_url}/api/backtesting/templates")
        return response.status_code == 200 and "templates" in response.json()

    def test_agent_workflows(self):
        """测试Agent工作流API"""
        response = self.session.get(f"{self.base_url}/api/agents/workflows")
        return response.status_code == 200 and "workflows" in response.json()

    def test_collaboration_efficiency(self):
        """测试协作效率API"""
        response = self.session.get(f"{self.base_url}/api/agents/collaboration/efficiency")
        return response.status_code == 200

    async def test_service_initialization(self):
        """测试服务初始化"""
        try:
            # 测试各个服务的初始化
            strategy_dashboard = get_strategy_dashboard()
            parameter_api = get_parameter_optimization_api()
            backtesting_lab = get_backtesting_lab()
            agent_service = get_agent_coordination_service()

            # 验证服务实例已创建
            return all([
                strategy_dashboard is not None,
                parameter_api is not None,
                backtesting_lab is not None,
                agent_service is not None
            ])

        except Exception as e:
            print(f"   服务初始化错误: {e}")
            return False

    def test_component_integration(self):
        """测试组件集成"""
        try:
            # 测试各个组件的集成
            from src.dashboard.strategy_management_dashboard import StrategyType, SignalType

            # 验证枚举类型
            strategy_types = [stype.value for stype in StrategyType]
            signal_types = [stype.value for stype in SignalType]

            return (len(strategy_types) == 4 and
                   len(signal_types) >= 4 and
                   "direct_rsi" in strategy_types)

        except Exception as e:
            print(f"   组件集成错误: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          🧪 策略管理Dashboard功能测试                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
        """)

        # 同步测试
        sync_tests = [
            ("健康检查", self.test_health_check),
            ("系统状态", self.test_system_status),
            ("策略API", self.test_strategies_api),
            ("性能摘要", self.test_performance_summary),
            ("Agent状态", self.test_agents_status),
            ("参数优化API", self.test_parameter_optimization),
            ("回测模板", self.test_backtesting_templates),
            ("Agent工作流", self.test_agent_workflows),
            ("协作效率", self.test_collaboration_efficiency),
            ("组件集成", self.test_component_integration),
        ]

        for test_name, test_func in sync_tests:
            self.run_test(test_name, test_func)

        # 异步测试
        self.run_test("服务初始化", lambda: asyncio.run(self.test_service_initialization()))

        # 生成测试报告
        self.generate_test_report()

    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)

        passed = len([r for r in self.test_results if "PASSED" in r["status"]])
        failed = len([r for r in self.test_results if "FAILED" in r["status"] or "ERROR" in r["status"]])
        total = len(self.test_results)

        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"成功率: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if "FAILED" in result["status"] or "ERROR" in result["status"]:
                    print(f"   • {result['name']}: {result['status']}")

        print(f"\n⏱️  总耗时: {sum(float(r['duration'].rstrip('s')) for r in self.test_results):.2f}s")
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 保存测试报告
        report_file = Path("dashboard_test_report.json")
        report_data = {
            "test_summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": passed/total*100
            },
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📄 详细报告已保存: {report_file}")


async def run_service_tests():
    """运行服务相关测试"""
    print("🔧 运行服务组件测试...")

    tester = DashboardTester()

    # 测试服务实例化
    try:
        strategy_dashboard = get_strategy_dashboard()
        parameter_api = get_parameter_optimization_api()
        backtesting_lab = get_backtesting_lab()
        agent_service = get_agent_coordination_service()

        print("✅ 所有服务组件实例化成功")

        # 测试基本功能
        print("🧪 测试基本服务功能...")

        # 测试策略管理Dashboard
        if hasattr(strategy_dashboard, 'get_app'):
            app = strategy_dashboard.get_app()
            print("✅ 策略管理Dashboard应用获取成功")

        # 测试参数优化API
        if hasattr(parameter_api, 'router'):
            print("✅ 参数优化API路由获取成功")

        # 测试回测实验室
        if hasattr(backtesting_lab, 'router'):
            print("✅ 回测实验室路由获取成功")

        # 测试Agent协作服务
        if hasattr(agent_service, 'router'):
            print("✅ Agent协作服务路由获取成功")

        print("✅ 所有服务组件测试通过")

    except Exception as e:
        print(f"❌ 服务组件测试失败: {e}")
        raise


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          🧪 策略管理Dashboard测试套件                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    import argparse

    parser = argparse.ArgumentParser(description="策略管理Dashboard测试套件")
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:3003",
        help="Dashboard URL (默认: http://localhost:3003)"
    )
    parser.add_argument(
        "--services-only", "-s",
        action="store_true",
        help="仅测试服务组件，不测试HTTP API"
    )

    args = parser.parse_args()

    if args.services_only:
        # 仅运行服务测试
        asyncio.run(run_service_tests())
    else:
        # 运行完整测试套件
        tester = DashboardTester(args.url)

        # 检查服务是否运行
        try:
            response = requests.get(f"{args.url}/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Dashboard服务未运行在 {args.url}")
                print("💡 请先启动Dashboard: python run_strategy_management_dashboard.py")
                sys.exit(1)
        except requests.exceptions.RequestException:
            print(f"❌ 无法连接到Dashboard服务 {args.url}")
            print("💡 请先启动Dashboard: python run_strategy_management_dashboard.py")
            sys.exit(1)

        # 运行所有测试
        tester.run_all_tests()


if __name__ == "__main__":
    main()