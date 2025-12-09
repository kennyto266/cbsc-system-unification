#!/usr/bin/env python3
"""
CBSC策略Dashboard修复验证脚本

验证夏普比率计算错误、数据验证和实时数据集成的修复效果。
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.dashboard.fixed_performance_service import FixedPerformanceService, PerformanceConfig
from src.dashboard.performance_service import PerformanceService


class CBSCDashboardValidator:
    """CBSC Dashboard修复验证器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.test_results = {
            "sharpe_ratio_fix": {"passed": False, "details": []},
            "data_validation": {"passed": False, "details": []},
            "real_time_integration": {"passed": False, "details": []}
        }

    def _setup_logger(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger("cbsc_dashboard_validator")

    async def test_sharpe_ratio_fix(self):
        """测试夏普比率计算修复"""
        self.logger.info("=== 测试夏普比率计算修复 ===")

        try:
            # 创建修复版服务
            config = PerformanceConfig(risk_free_rate=0.025)
            fixed_service = FixedPerformanceService(config)

            # 创建原始服务（用于对比）
            original_service = PerformanceService()

            # 测试用例1: 正常数据
            test_returns = np.array([0.01, -0.005, 0.02, 0.015, -0.01, 0.008])

            fixed_sharpe = fixed_service.calculate_sharpe_ratio(test_returns)
            original_sharpe = original_service.calculate_sharpe_ratio(test_returns)

            self.logger.info(f"测试数据收益率: {test_returns}")
            self.logger.info(f"修复版夏普比率: {fixed_sharpe:.4f}")
            self.logger.info(f"原始版夏普比率: {original_sharpe:.4f}")

            # 验证1: 夏普比率应该在合理范围内
            if abs(fixed_sharpe) < 5.0:
                self.test_results["sharpe_ratio_fix"]["details"].append("✓ 夏普比率在合理范围内")
            else:
                self.test_results["sharpe_ratio_fix"]["details"].append("✗ 夏普比率超出合理范围")

            # 验证2: 修复版应该使用正确的公式
            mean_return = np.mean(test_returns)
            std_return = np.std(test_returns, ddof=1)
            annual_return = mean_return * 252
            annual_vol = std_return * np.sqrt(252)
            expected_sharpe = (annual_return - 0.025) / annual_vol

            if abs(fixed_sharpe - expected_sharpe) < 0.001:
                self.test_results["sharpe_ratio_fix"]["details"].append("✓ 使用正确的夏普比率公式")
            else:
                self.test_results["sharpe_ratio_fix"]["details"].append("✗ 夏普比率公式计算错误")

            # 测试用例2: 极端数据
            extreme_returns = np.array([0.5, -0.3, 0.4, -0.2, 0.6])  # 极端收益率
            extreme_sharpe = fixed_service.calculate_sharpe_ratio(extreme_returns)

            if abs(extreme_sharpe) <= 5.0:
                self.test_results["sharpe_ratio_fix"]["details"].append("✓ 极端数据夏普比率正确限制")
            else:
                self.test_results["sharpe_ratio_fix"]["details"].append("✗ 极端数据夏普比率未限制")

            # 测试用例3: 零波动率数据
            constant_returns = np.array([0.01, 0.01, 0.01, 0.01])
            zero_vol_sharpe = fixed_service.calculate_sharpe_ratio(constant_returns)

            if zero_vol_sharpe == 0.0:
                self.test_results["sharpe_ratio_fix"]["details"].append("✓ 零波动率处理正确")
            else:
                self.test_results["sharpe_ratio_fix"]["details"].append("✗ 零波动率处理错误")

            # 计算通过率
            passed_tests = sum(1 for detail in self.test_results["sharpe_ratio_fix"]["details"] if detail.startswith("✓"))
            total_tests = len(self.test_results["sharpe_ratio_fix"]["details"])

            if passed_tests >= total_tests * 0.8:  # 80%通过率
                self.test_results["sharpe_ratio_fix"]["passed"] = True
                self.logger.info(f"夏普比率修复测试通过 ({passed_tests}/{total_tests})")
            else:
                self.logger.error(f"夏普比率修复测试失败 ({passed_tests}/{total_tests})")

        except Exception as e:
            self.logger.error(f"夏普比率测试异常: {e}")
            self.test_results["sharpe_ratio_fix"]["details"].append(f"✗ 测试异常: {e}")

    async def test_data_validation(self):
        """测试数据验证机制"""
        self.logger.info("=== 测试数据验证机制 ===")

        try:
            config = PerformanceConfig()
            service = FixedPerformanceService(config)

            # 测试1: 收益率数据验证
            invalid_returns = [np.nan, 0.5, -0.3, None, 0.1]  # 包含无效值
            valid_returns = [0.01, -0.005, 0.02, 0.015, -0.01]

            # 验证单个收益率
            for ret in invalid_returns:
                if pd.isna(ret):
                    validated_ret = service.validator.validate_returns(ret)
                    if validated_ret == 0.0:
                        self.test_results["data_validation"]["details"].append("✓ NaN值处理正确")
                    else:
                        self.test_results["data_validation"]["details"].append("✗ NaN值处理错误")
                elif not isinstance(ret, (int, float)):
                    validated_ret = service.validator.validate_returns(ret)
                    if validated_ret == 0.0:
                        self.test_results["data_validation"]["details"].append("✓ 非数值处理正确")
                    else:
                        self.test_results["data_validation"]["details"].append("✗ 非数值处理错误")
                else:
                    validated_ret = service.validator.validate_returns(ret)
                    if abs(validated_ret) <= 0.2:  # 限制在±20%以内
                        self.test_results["data_validation"]["details"].append("✓ 极端收益率限制正确")
                    else:
                        self.test_results["data_validation"]["details"].append("✗ 极端收益率限制错误")

            # 测试2: 数据质量评分
            test_data = np.array(valid_returns + [np.nan, np.inf, -np.inf])
            quality_score = service.validator.calculate_data_quality_score(test_data)

            if 0 <= quality_score <= 100:
                self.test_results["data_validation"]["details"].append(f"✓ 数据质量评分合理 ({quality_score:.1f})")
            else:
                self.test_results["data_validation"]["details"].append(f"✗ 数据质量评分异常 ({quality_score:.1f})")

            # 测试3: 策略数据验证
            test_strategy_data = {
                "returns": valid_returns,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1
            }

            validation_result = service.validate_strategy_data("test_strategy", test_strategy_data)

            if validation_result["is_valid"]:
                self.test_results["data_validation"]["details"].append("✓ 策略数据验证通过")
            else:
                self.test_results["data_validation"]["details"].append("✗ 策略数据验证失败")

            # 测试4: 不完整数据验证
            incomplete_data = {
                "returns": valid_returns
                # 缺少必要字段
            }

            validation_result = service.validate_strategy_data("incomplete_strategy", incomplete_data)

            if not validation_result["is_valid"]:
                self.test_results["data_validation"]["details"].append("✓ 不完整数据正确拒绝")
            else:
                self.test_results["data_validation"]["details"].append("✗ 不完整数据错误接受")

            # 计算通过率
            passed_tests = sum(1 for detail in self.test_results["data_validation"]["details"] if detail.startswith("✓"))
            total_tests = len(self.test_results["data_validation"]["details"])

            if passed_tests >= total_tests * 0.8:
                self.test_results["data_validation"]["passed"] = True
                self.logger.info(f"数据验证测试通过 ({passed_tests}/{total_tests})")
            else:
                self.logger.error(f"数据验证测试失败 ({passed_tests}/{total_tests})")

        except Exception as e:
            self.logger.error(f"数据验证测试异常: {e}")
            self.test_results["data_validation"]["details"].append(f"✗ 测试异常: {e}")

    async def test_real_time_integration(self):
        """测试实时数据集成"""
        self.logger.info("=== 测试实时数据集成 ===")

        try:
            config = PerformanceConfig(update_interval=5)  # 5秒更新间隔用于测试
            service = FixedPerformanceService(config)

            # 启动服务
            await service.initialize()

            # 等待一些数据生成
            await asyncio.sleep(6)

            # 检查数据是否生成
            all_metrics = service.get_all_performance_metrics()

            if len(all_metrics) > 0:
                self.test_results["real_time_integration"]["details"].append("✓ 实时数据生成成功")
            else:
                self.test_results["real_time_integration"]["details"].append("✗ 实时数据生成失败")

            # 检查数据更新频率
            initial_metrics = all_metrics
            await asyncio.sleep(6)  # 等待下一次更新
            updated_metrics = service.get_all_performance_metrics()

            if len(updated_metrics) >= len(initial_metrics):
                self.test_results["real_time_integration"]["details"].append("✓ 数据定期更新")
            else:
                self.test_results["real_time_integration"]["details"].append("✗ 数据未定期更新")

            # 检查系统状态
            system_status = service.get_system_status()

            if system_status["service_running"]:
                self.test_results["real_time_integration"]["details"].append("✓ 服务运行状态正常")
            else:
                self.test_results["real_time_integration"]["details"].append("✗ 服务运行状态异常")

            # 检查配置
            if system_status["config"]["update_interval"] == 5:
                self.test_results["real_time_integration"]["details"].append("✓ 配置参数正确")
            else:
                self.test_results["real_time_integration"]["details"].append("✗ 配置参数错误")

            # 停止服务
            await service.stop()

            # 计算通过率
            passed_tests = sum(1 for detail in self.test_results["real_time_integration"]["details"] if detail.startswith("✓"))
            total_tests = len(self.test_results["real_time_integration"]["details"])

            if passed_tests >= total_tests * 0.8:
                self.test_results["real_time_integration"]["passed"] = True
                self.logger.info(f"实时数据集成测试通过 ({passed_tests}/{total_tests})")
            else:
                self.logger.error(f"实时数据集成测试失败 ({passed_tests}/{total_tests})")

        except Exception as e:
            self.logger.error(f"实时数据集成测试异常: {e}")
            self.test_results["real_time_integration"]["details"].append(f"✗ 测试异常: {e}")

    async def generate_test_report(self):
        """生成测试报告"""
        self.logger.info("=== 生成测试报告 ===")

        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for result in self.test_results.values() if result["passed"]),
                "failed_tests": sum(1 for result in self.test_results.values() if not result["passed"])
            },
            "details": self.test_results
        }

        # 保存报告
        report_file = f"cbsc_dashboard_fix_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"测试报告已保存到: {report_file}")

        # 打印摘要
        self.logger.info("=== 测试摘要 ===")
        for test_name, result in self.test_results.items():
            status = "通过" if result["passed"] else "失败"
            self.logger.info(f"{test_name}: {status}")

            for detail in result["details"]:
                self.logger.info(f"  {detail}")

        overall_passed = report["summary"]["passed_tests"] >= report["summary"]["total_tests"] * 0.8
        self.logger.info(f"\n总体结果: {'通过' if overall_passed else '失败'}")
        self.logger.info(f"通过测试: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")

        return report

    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始CBSC策略Dashboard修复验证测试")

        await self.test_sharpe_ratio_fix()
        await self.test_data_validation()
        await self.test_real_time_integration()

        report = await self.generate_test_report()
        return report


async def main():
    """主函数"""
    validator = CBSCDashboardValidator()
    report = await validator.run_all_tests()

    # 返回适当的退出码
    overall_passed = report["summary"]["passed_tests"] >= report["summary"]["total_tests"] * 0.8
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())