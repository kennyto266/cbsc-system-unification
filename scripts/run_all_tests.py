#!/usr/bin/env python3
"""
港股量化交易AI Agent系统 - 运行所有测试脚本

本脚本统一运行所有测试和验证脚本，包括：
- 最终集成测试
- 系统验证
- 生产环境模拟测试
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试脚本
from final_integration_test import FinalIntegrationTest
from system_validation import SystemValidator
from production_simulation import ProductionSimulator


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.test_results = {}
        self.start_time = datetime.now()
        
        # 测试脚本配置
        self.test_scripts = [
            {
                "name": "final_integration_test",
                "description": "最终集成测试和系统验证",
                "class": FinalIntegrationTest,
                "enabled": True
            },
            {
                "name": "system_validation",
                "description": "系统验证",
                "class": SystemValidator,
                "enabled": True
            },
            {
                "name": "production_simulation",
                "description": "生产环境模拟测试",
                "class": ProductionSimulator,
                "enabled": True
            }
        ]
        
        self.logger.info("测试运行器初始化完成")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("test_runner")
        logger.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        log_file = project_root / "logs" / "test_runner.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始运行所有测试")
        
        try:
            # 运行每个测试脚本
            for test_script in self.test_scripts:
                if not test_script["enabled"]:
                    self.logger.info(f"跳过测试: {test_script['name']}")
                    continue
                
                await self._run_single_test(test_script)
            
            # 生成综合报告
            comprehensive_report = self._generate_comprehensive_report()
            
            self.logger.info("所有测试运行完成")
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"测试运行失败: {e}", exc_info=True)
            raise
    
    async def _run_single_test(self, test_script: Dict[str, Any]):
        """运行单个测试"""
        test_name = test_script["name"]
        test_description = test_script["description"]
        test_class = test_script["class"]
        
        self.logger.info(f"开始运行测试: {test_description}")
        
        try:
            # 创建测试实例
            test_instance = test_class()
            
            # 运行测试
            start_time = time.time()
            
            if test_name == "final_integration_test":
                result = await test_instance.run_complete_test_suite()
            elif test_name == "system_validation":
                result = await test_instance.run_validation()
            elif test_name == "production_simulation":
                result = await test_instance.run_simulation()
            else:
                raise ValueError(f"未知的测试类型: {test_name}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 保存测试结果
            self.test_results[test_name] = {
                "status": "COMPLETED",
                "description": test_description,
                "duration": duration,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"测试完成: {test_description} (耗时: {duration:.2f}秒)")
            
        except Exception as e:
            self.logger.error(f"测试失败: {test_description} - {e}", exc_info=True)
            
            self.test_results[test_name] = {
                "status": "FAILED",
                "description": test_description,
                "duration": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # 统计测试结果
        total_tests = len(self.test_results)
        completed_tests = sum(1 for result in self.test_results.values() if result["status"] == "COMPLETED")
        failed_tests = sum(1 for result in self.test_results.values() if result["status"] == "FAILED")
        
        # 计算总体成功率
        overall_success_rate = 0
        if completed_tests > 0:
            # 从各个测试的结果中提取成功率
            success_rates = []
            for test_name, test_result in self.test_results.items():
                if test_result["status"] == "COMPLETED" and "result" in test_result:
                    result = test_result["result"]
                    if "test_summary" in result:
                        success_rates.append(result["test_summary"]["success_rate"])
                    elif "validation_summary" in result:
                        success_rates.append(result["validation_summary"]["success_rate"])
                    elif "simulation_summary" in result:
                        success_rates.append(result["simulation_summary"]["success_rate"])
            
            if success_rates:
                overall_success_rate = sum(success_rates) / len(success_rates)
        
        # 生成综合报告
        comprehensive_report = {
            "comprehensive_summary": {
                "total_tests": total_tests,
                "completed_tests": completed_tests,
                "failed_tests": failed_tests,
                "overall_success_rate": overall_success_rate,
                "total_duration": total_duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "test_results": self.test_results,
            "recommendations": self._generate_comprehensive_recommendations(),
            "metadata": {
                "test_runner_version": "1.0.0",
                "system_version": "1.0.0",
                "python_version": sys.version,
                "platform": os.name
            }
        }
        
        # 保存综合报告到文件
        report_file = project_root / "logs" / "comprehensive_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"综合报告已保存到: {report_file}")
        
        return comprehensive_report
    
    def _generate_comprehensive_recommendations(self) -> List[str]:
        """生成综合改进建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        for test_name, test_result in self.test_results.items():
            if test_result["status"] == "FAILED":
                recommendations.append(f"修复 {test_name} 测试失败的问题")
            elif test_result["status"] == "COMPLETED" and "result" in test_result:
                result = test_result["result"]
                if "recommendations" in result:
                    recommendations.extend(result["recommendations"])
        
        # 通用建议
        recommendations.extend([
            "定期运行完整的测试套件以确保系统质量",
            "建立持续集成和持续部署流程",
            "监控系统性能指标并及时优化",
            "建立完善的日志记录和监控体系",
            "定期更新系统依赖和安全补丁",
            "建立完善的故障恢复和灾难恢复机制"
        ])
        
        # 去重
        recommendations = list(set(recommendations))
        
        return recommendations


async def main():
    """主函数"""
    print("港股量化交易AI Agent系统 - 运行所有测试")
    print("=" * 60)
    
    try:
        # 创建测试运行器
        test_runner = TestRunner()
        
        # 运行所有测试
        comprehensive_report = await test_runner.run_all_tests()
        
        # 显示综合结果
        print("\n综合测试结果:")
        print("-" * 40)
        summary = comprehensive_report["comprehensive_summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"完成测试: {summary['completed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"总体成功率: {summary['overall_success_rate']:.2%}")
        print(f"总耗时: {summary['total_duration']:.2f}秒")
        
        print("\n详细测试结果:")
        print("-" * 40)
        for test_name, test_result in comprehensive_report["test_results"].items():
            status = "✓" if test_result["status"] == "COMPLETED" else "✗"
            duration = test_result.get("duration", 0)
            print(f"{status} {test_name}: {test_result['description']} (耗时: {duration:.2f}秒)")
        
        print("\n综合改进建议:")
        print("-" * 40)
        for i, recommendation in enumerate(comprehensive_report["recommendations"], 1):
            print(f"{i}. {recommendation}")
        
        # 判断整体测试是否成功
        if summary["overall_success_rate"] >= 0.8 and summary["failed_tests"] == 0:
            print(f"\n🎉 所有测试成功完成！总体成功率: {summary['overall_success_rate']:.2%}")
            return 0
        else:
            print(f"\n❌ 部分测试失败！总体成功率: {summary['overall_success_rate']:.2%}")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试运行过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    # 运行所有测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
