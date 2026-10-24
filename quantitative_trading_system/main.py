#!/usr/bin/env python3
"""
量化交易系统 - 简化版主入口
Quantitative Trading System - Simplified Main Entry

基于YAGNI和KISS原则的简化量化交易系统
专注于核心功能：数据获取、技术指标、回测、优化

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quantitative_trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class QuantitativeTradingSystem:
    """
    量化交易系统主类
    简化版本，专注于核心功能
    """

    def __init__(self):
        """初始化量化交易系统"""
        self.data_manager = None
        self.indicators = None
        self.backtest_engine = None
        self.optimizer = None
        self.initialized = False

        logger.info("量化交易系统初始化开始")

    def initialize(self):
        """初始化所有模块"""
        try:
            # 动态导入核心模块
            from data.data_manager import DataManager
            from indicators.core_indicators import CoreIndicators
            from backtest.vectorbt_engine import VectorBTEngine
            from optimization.optimizer import ParameterOptimizer

            # 初始化数据管理器
            self.data_manager = DataManager()
            logger.info("✅ 数据管理器初始化完成")

            # 初始化技术指标引擎
            self.indicators = CoreIndicators()
            logger.info("✅ 技术指标引擎初始化完成")

            # 初始化回测引擎
            self.backtest_engine = VectorBTEngine()
            logger.info("✅ 回测引擎初始化完成")

            # 初始化参数优化器
            self.optimizer = ParameterOptimizer()
            logger.info("✅ 参数优化器初始化完成")

            self.initialized = True
            logger.info("🚀 量化交易系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            return False

    def quick_test(self):
        """快速系统测试"""
        if not self.initialized:
            logger.error("系统未初始化，请先调用 initialize()")
            return False

        try:
            logger.info("🧪 开始快速系统测试...")

            # 测试数据获取
            data = self.data_manager.get_stock_data("0700.HK", 252)
            if data is not None and len(data) > 0:
                logger.info(f"✅ 数据获取测试通过: {len(data)} 条记录")
            else:
                logger.error("❌ 数据获取测试失败")
                return False

            # 测试技术指标计算
            if 'close' in data.columns:
                rsi = self.indicators.calculate_rsi(data['close'], 14)
                if rsi is not None and len(rsi) > 0:
                    logger.info(f"✅ 技术指标测试通过: RSI最新值 {rsi.iloc[-1]:.2f}")
                else:
                    logger.error("❌ 技术指标测试失败")
                    return False

            # 测试回测引擎
            result = self.backtest_engine.backtest_strategy(
                data, "RSI_MEAN_REVERSION",
                {'period': 14, 'oversold': 30, 'overbought': 70}
            )
            if result:
                logger.info(f"✅ 回测引擎测试通过: 回报 {result.total_return:.2%}, Sharpe {result.sharpe_ratio:.3f}")
            else:
                logger.error("❌ 回测引擎测试失败")
                return False

            logger.info("🎉 所有测试通过！系统运行正常")
            return True

        except Exception as e:
            logger.error(f"❌ 系统测试失败: {e}")
            return False

    def run_demo(self):
        """运行演示"""
        if not self.initialized:
            logger.error("系统未初始化，请先调用 initialize()")
            return

        try:
            logger.info("🚀 运行量化交易系统演示...")

            # 获取腾讯数据
            data = self.data_manager.get_stock_data("0700.HK", 365)

            # 计算多种技术指标
            indicators = {}
            if 'close' in data.columns:
                indicators['rsi'] = self.indicators.calculate_rsi(data['close'], 14)
                indicators['sma_20'] = self.indicators.calculate_sma(data['close'], 20)
                indicators['sma_50'] = self.indicators.calculate_sma(data['close'], 50)
                indicators['macd'] = self.indicators.calculate_macd(data['close'])

            # 运行多策略回测
            strategies = [
                ("RSI均值回归", {'period': 14, 'oversold': 30, 'overbought': 70}),
                ("双移动平均", {'short_period': 20, 'long_period': 50}),
                ("MACD交叉", {'fast': 12, 'slow': 26, 'signal': 9})
            ]

            results = []
            for strategy_name, params in strategies:
                result = self.backtest_engine.backtest_strategy(data, "RSI_MEAN_REVERSION", params)
                if result:
                    results.append((strategy_name, result.total_return, result.sharpe_ratio))
                    logger.info(f"策略 {strategy_name}: 回报 {result.total_return:.2%}, Sharpe {result.sharpe_ratio:.3f}")

            # 找到最佳策略
            if results:
                best_strategy = max(results, key=lambda x: x[2])
                logger.info(f"🏆 最佳策略: {best_strategy[0]} (Sharpe: {best_strategy[2]:.3f})")

            logger.info("✅ 演示完成")

        except Exception as e:
            logger.error(f"❌ 演示运行失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 量化交易系统 - 简化版 v1.0.0")
    print("Quantitative Trading System - Simplified Edition")
    print("=" * 60)
    print()

    # 创建系统实例
    system = QuantitativeTradingSystem()

    # 初始化系统
    if not system.initialize():
        print("❌ 系统初始化失败，退出...")
        return 1

    print()
    print("🎯 选择运行模式:")
    print("1. 快速系统测试")
    print("2. 运行演示")
    print("3. 交互式模式")
    print()

    try:
        choice = input("请输入选择 (1-3): ").strip()

        if choice == "1":
            success = system.quick_test()
            return 0 if success else 1

        elif choice == "2":
            system.run_demo()
            return 0

        elif choice == "3":
            print("🚀 进入交互式模式...")
            print("可用命令:")
            print("  get_data <symbol> <days>  - 获取股票数据")
            print("  calculate_rsi <period>    - 计算RSI指标")
            print("  backtest <strategy>       - 运行回测")
            print("  quit                      - 退出")
            print()

            while True:
                try:
                    cmd = input(">>> ").strip().lower()
                    if cmd == "quit":
                        break
                    elif cmd.startswith("get_data"):
                        parts = cmd.split()
                        if len(parts) >= 3:
                            symbol = parts[1]
                            days = int(parts[2])
                            data = system.data_manager.get_stock_data(symbol, days)
                            if data is not None:
                                print(f"✅ 获取到 {len(data)} 条数据")
                            else:
                                print("❌ 数据获取失败")
                        else:
                            print("用法: get_data <symbol> <days>")
                    else:
                        print("未知命令，输入 quit 退出")
                except KeyboardInterrupt:
                    break

            print("👋 再见！")
            return 0

        else:
            print("❌ 无效选择")
            return 1

    except KeyboardInterrupt:
        print("\n👋 用户中断，退出...")
        return 0
    except Exception as e:
        logger.error(f"❌ 运行出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())