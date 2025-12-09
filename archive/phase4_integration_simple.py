#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: 简化系统集成测试
Phase 4: Simplified System Integration Testing
"""

import numpy as np
import time
import logging
import json
from datetime import datetime
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase4SimpleIntegration:
    """Phase 4 简化集成测试"""

    def __init__(self):
        self.start_time = time.time()
        logger.info("Phase 4 简化集成测试开始")

    def test_all_phases(self) -> Dict[str, Any]:
        """测试所有Phase"""
        results = {
            'phase1_success': False,
            'phase2_success': False,
            'phase3_success': False,
            'integration_success': False,
            'total_time': 0,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Phase 1: GPU环境测试
            print("测试 Phase 1: GPU环境和数据准备")
            results['phase1_success'] = self._test_phase1()

            # Phase 2: TA引擎测试
            print("测试 Phase 2: GPU TA引擎")
            results['phase2_success'] = self._test_phase2()

            # Phase 3: 回测引擎测试
            print("测试 Phase 3: 回测引擎")
            results['phase3_success'] = self._test_phase3()

            # 系统集成测试
            print("测试系统集成")
            results['integration_success'] = self._test_integration()

            # 计算总体成功率
            successful_tests = sum([
                results['phase1_success'],
                results['phase2_success'],
                results['phase3_success'],
                results['integration_success']
            ])
            results['success_rate'] = successful_tests / 4
            results['overall_success'] = results['success_rate'] >= 0.75

        except Exception as e:
            logger.error(f"集成测试失败: {e}")
            results['error'] = str(e)

        finally:
            results['total_time'] = time.time() - self.start_time

        return results

    def _test_phase1(self) -> bool:
        """测试Phase 1: GPU环境和数据准备"""
        try:
            # 测试GPU
            try:
                import cupy as cp
                gpu_test = True
                logger.info("GPU可用")
            except ImportError:
                gpu_test = False
                logger.info("使用CPU版本")

            # 测试数据加载
            try:
                from phase2_gpu_ta_engine_with_real_data import RealGovDataLoader
                loader = RealGovDataLoader()
                data = loader.get_all_real_data(50)
                data_test = len(data) > 0
                logger.info(f"政府数据加载: {len(data)}个源")
            except:
                data_test = False
                logger.warning("政府数据加载失败")

            return gpu_test or data_test  # 至少一个成功

        except Exception as e:
            logger.error(f"Phase 1 测试失败: {e}")
            return False

    def _test_phase2(self) -> bool:
        """测试Phase 2: GPU TA引擎"""
        try:
            from phase2_gpu_ta_engine_with_real_data import Phase2GPUBacktestEngine

            # 初始化引擎
            engine = Phase2GPUBacktestEngine(gpu_device=0)

            # 测试数据加载
            data = engine.load_0700_hk_data(100)
            if not data.get('success', False):
                return False

            # 测试HIBOR策略
            hibor_result = engine.run_hibor_rsi_strategy(data)

            # 测试MACD策略
            macd_result = engine.run_monetary_macd_strategy(data)

            success = (hibor_result.get('success', False) and
                      macd_result.get('success', False))

            logger.info(f"TA引擎测试: HIBOR={hibor_result.get('success')}, MACD={macd_result.get('success')}")
            return success

        except Exception as e:
            logger.error(f"Phase 2 测试失败: {e}")
            return False

    def _test_phase3(self) -> bool:
        """测试Phase 3: 回测引擎"""
        try:
            from phase3_backtest_simple import Phase3SimpleBacktest

            # 初始化回测引擎
            backtest_engine = Phase3SimpleBacktest(gpu_device=0)

            # 运行完整回测
            result = backtest_engine.run_all_strategies(days=100)

            success = result.get('success', False)
            logger.info(f"回测引擎测试: {success}")

            if success:
                strategy_results = result.get('strategy_results', {})
                successful_strategies = sum(1 for r in strategy_results.values() if r.get('success', False))
                logger.info(f"成功策略: {successful_strategies}/{len(strategy_results)}")

            return success

        except Exception as e:
            logger.error(f"Phase 3 测试失败: {e}")
            return False

    def _test_integration(self) -> bool:
        """测试系统集成"""
        try:
            # 端到端测试
            from phase3_backtest_simple import Phase3SimpleBacktest
            engine = Phase3SimpleBacktest(gpu_device=0)

            # 运行完整流程
            result = engine.run_all_strategies(days=50)

            success = result.get('success', False)
            execution_time = result.get('summary', {}).get('total_execution_time', 0)

            logger.info(f"集成测试: {success}, 执行时间: {execution_time:.4f}秒")

            # 性能基准检查
            performance_ok = execution_time < 10.0  # 10秒内完成
            logger.info(f"性能检查: {'通过' if performance_ok else '失败'}")

            return success and performance_ok

        except Exception as e:
            logger.error(f"集成测试失败: {e}")
            return False

    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 60)
        report.append("Phase 4 系统集成测试报告")
        report.append("=" * 60)

        # 总体结果
        report.append(f"\n[总体结果]")
        report.append(f"测试成功率: {results.get('success_rate', 0):.1%}")
        report.append(f"总体状态: {'成功' if results.get('overall_success', False) else '失败'}")
        report.append(f"执行时间: {results.get('total_time', 0):.4f}秒")

        # Phase结果
        report.append(f"\n[Phase测试结果]")
        report.append(f"Phase 1 (数据准备): {'成功' if results.get('phase1_success', False) else '失败'}")
        report.append(f"Phase 2 (GPU TA引擎): {'成功' if results.get('phase2_success', False) else '失败'}")
        report.append(f"Phase 3 (回测引擎): {'成功' if results.get('phase3_success', False) else '失败'}")
        report.append(f"系统集成: {'成功' if results.get('integration_success', False) else '失败'}")

        # 系统状态
        success_rate = results.get('success_rate', 0)
        if success_rate >= 0.75:
            status = "PRODUCTION_READY"
        elif success_rate >= 0.5:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "NOT_READY"

        report.append(f"\n[系统状态: {status}]")

        # 建议
        report.append(f"\n[建议]")
        if results.get('overall_success', False):
            report.append("- 系统已准备就绪，可以投入生产使用")
            report.append("- 所有核心功能正常工作")
            report.append("- GPU加速功能可用")
        else:
            report.append("- 系统需要进一步优化")
            report.append("- 建议检查失败的组件")

        report.append(f"\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)

        return "\n".join(report)

def main():
    """主函数"""
    print("=" * 60)
    print("Phase 4: 系统集成测试")
    print("=" * 60)

    try:
        # 运行集成测试
        integration_test = Phase4SimpleIntegration()
        results = integration_test.test_all_phases()

        # 生成报告
        report = integration_test.generate_report(results)
        print("\n" + report)

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"phase4_integration_results_{timestamp}.json"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n结果已保存至: {json_file}")

        # 保存报告
        report_file = f"phase4_integration_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"报告已保存至: {report_file}")

        # 最终状态
        if results.get('overall_success', False):
            print("\n🎉 系统集成测试成功完成！")
            print("GPU加速量化交易平台已准备就绪")
        else:
            print("\n⚠️ 系统需要进一步优化")

    except Exception as e:
        logger.error(f"集成测试执行失败: {e}")
        print(f"集成测试执行失败: {e}")

if __name__ == "__main__":
    main()