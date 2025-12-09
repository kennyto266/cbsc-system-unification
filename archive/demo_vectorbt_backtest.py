#!/usr/bin/env python3
"""
VectorBT回测演示
展示CODEX--系统中VectorBT集成功能
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.data.vectorbt_adapter import VectorBTDataAdapter
    from src.strategy.hybrid_signals import HybridSignalFramework, SignalConfig
    from src.performance.vectorbt_engine import VectorBTComputeEngine, BacktestConfig
    from src.performance.parallel_optimizer import ParallelOptimizer, OptimizationConfig
    from src.indicators.vectorbt_indicators import VectorBTTechnicalIndicators
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在CODEX--项目根目录运行此脚本")
    sys.exit(1)


class VectorBTBacktestDemo:
    """VectorBT回测演示类"""
    
    def __init__(self):
        print("=" * 60)
        print("🚀 VectorBT深度集成演示")
        print("CODEX--量化交易系统")
        print("=" * 60)
        
        # 初始化组件
        self.vbt_adapter = VectorBTDataAdapter()
        self.hybrid_framework = HybridSignalFramework()
        self.vbt_engine = VectorBTComputeEngine()
        self.technical_indicators = VectorBTTechnicalIndicators()
        
        # 演示参数
        self.symbols = ["0700.HK", "0005.HK", "1398.HK"]
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2024, 1, 1)
        
    def generate_sample_data(self):
        """生成示例数据用于演示"""
        print("\n📊 生成示例数据...")
        
        # 生成示例价格数据
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        
        price_data = {}
        for symbol in self.symbols:
            np.random.seed(hash(symbol) % (2**32))  # 确保可重现性
            
            # 模拟价格走势
            initial_price = 100.0
            returns = np.random.normal(0.0005, 0.02, len(date_range))
            prices = [initial_price]
            
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            
            # 创建OHLCV数据
            df = pd.DataFrame({
                'open': prices[1:] + [prices[-1]],
                'high': [p * 1.02 for p in prices],
                'low': [p * 0.98 for p in prices],
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, len(date_range))
            }, index=date_range)
            
            price_data[symbol] = df
        
        # 生成示例经济数据
        economic_data = {
            'hibor': self._generate_hibor_data(date_range),
            'gdp': self._generate_gdp_data(date_range),
            'trade': self._generate_trade_data(date_range)
        }
        
        print(f"✅ 生成了 {len(price_data)} 个标的价格数据")
        print(f"✅ 生成了 {len(economic_data)} 个经济数据源")
        
        return price_data, economic_data
    
    def _generate_hibor_data(self, date_range):
        """生成HIBOR数据"""
        hibor_rates = np.random.normal(0.05, 0.01, len(date_range))
        hibor_rates = np.clip(hibor_rates, 0.01, 0.15)  # 限制在合理范围内
        
        df = pd.DataFrame({
            'date': date_range,
            'rate': hibor_rates
        })
        df.set_index('date', inplace=True)
        return df
    
    def _generate_gdp_data(self, date_range):
        """生成GDP数据"""
        # 生成季度GDP数据
        gdp_values = []
        base_gdp = 100.0
        for i in range(0, len(date_range), 90):  # 每季度
            growth = np.random.normal(0.02, 0.01)  # 2% ± 1% 增长
            base_gdp *= (1 + growth)
            gdp_values.append(base_gdp)
        
        # 扩展到每日数据
        daily_gdp = []
        for value in gdp_values:
            daily_gdp.extend([value] * min(90, len(date_range) - len(daily_gdp)))
        
        # 确保长度匹配
        daily_gdp = daily_gdp[:len(date_range)]
        
        df = pd.DataFrame({
            'date': date_range,
            'value': daily_gdp
        })
        df.set_index('date', inplace=True)
        return df
    
    def _generate_trade_data(self, date_range):
        """生成贸易数据"""
        export_values = np.random.normal(50, 10, len(date_range))
        import_values = np.random.normal(45, 8, len(date_range))
        
        export_values = np.clip(export_values, 20, 80)
        import_values = np.clip(import_values, 15, 70)
        
        df = pd.DataFrame({
            'date': date_range,
            'export_value': export_values,
            'import_value': import_values
        })
        df.set_index('date', inplace=True)
        return df
    
    async def demo_signal_generation(self, price_data, economic_data):
        """演示信号生成"""
        print("\n🎯 演示混合信号生成...")
        
        # 选择一个股票进行演示
        symbol = self.symbols[0]
        print(f"标的: {symbol}")
        print(f"时间范围: {self.start_date.date()} 到 {self.end_date.date()}")
        
        # 配置信号参数
        signal_config = SignalConfig(
            price_weight=0.6,
            economic_weight=0.4,
            adaptive_weights=True,
            regime_aware=True
        )
        
        self.hybrid_framework.config = signal_config
        
        try:
            # 生成混合信号
            signal_result = await self.hybrid_framework.generate_hybrid_signals(
                symbol,
                price_data[symbol],
                economic_data,
                self.start_date,
                self.end_date
            )
            
            print(f"✅ 信号质量评分: {signal_result.quality_score:.2f}/100")
            print(f"✅ 市场状态: {signal_result.regime.value}")
            print(f"✅ 信号权重: {signal_result.weights}")
            
            # 信号解读
            interpretation = self.hybrid_framework.get_signal_interpretation(signal_result.signals)
            print(f"✅ 当前信号: {interpretation.get('action', 'N/A')}")
            print(f"✅ 信号强度: {interpretation.get('signal_strength', 'N/A')}")
            print(f"✅ 信号质量: {interpretation.get('signal_consensus', 'N/A')}")
            
            # 显示信号统计
            signals_df = signal_result.signals
            if not signals_df.empty:
                print(f"\n📈 信号统计:")
                print(f"  总信号数: {len(signals_df.columns)}")
                print(f"  时间点数: {len(signals_df)}")
                
                if 'hybrid_signal' in signals_df.columns:
                    hybrid_signal = signals_df['hybrid_signal']
                    print(f"  混合信号均值: {hybrid_signal.mean():.4f}")
                    print(f"  混合信号标准差: {hybrid_signal.std():.4f}")
                    print(f"  最强看涨信号: {hybrid_signal.max():.4f}")
                    print(f"  最强看跌信号: {hybrid_signal.min():.4f}")
            
            return signal_result.signals
            
        except Exception as e:
            print(f"❌ 信号生成失败: {e}")
            return pd.DataFrame()
    
    def demo_technical_indicators(self, price_data):
        """演示技术指标计算"""
        print("\n📊 演示技术指标计算...")
        
        symbol = self.symbols[0]
        df = price_data[symbol]
        
        try:
            # 计算所有技术指标
            indicators_df = self.technical_indicators.calculate_all_indicators(df)
            
            print(f"✅ 计算了 {len(indicators_df.columns)} 个技术指标")
            print(f"✅ 数据时间范围: {len(indicators_df)} 个交易日")
            
            # 显示指标类别统计
            rsi_cols = [col for col in indicators_df.columns if 'rsi' in col]
            macd_cols = [col for col in indicators_df.columns if 'macd' in col]
            bb_cols = [col for col in indicators_df.columns if 'bb_' in col]
            adx_cols = [col for col in indicators_df.columns if 'adx' in col]
            
            print(f"\n📈 指标类别统计:")
            print(f"  RSI指标: {len(rsi_cols)} 个")
            print(f"  MACD指标: {len(macd_cols)} 个")
            print(f"  布林带指标: {len(bb_cols)} 个")
            print(f"  ADX指标: {len(adx_cols)} 个")
            
            return indicators_df
            
        except Exception as e:
            print(f"❌ 技术指标计算失败: {e}")
            return pd.DataFrame()
    
    def demo_backtest(self, price_data, signals):
        """演示回测功能"""
        print("\n⚡ 演示VectorBT回测...")
        
        try:
            # 配置回测参数
            backtest_config = BacktestConfig(
                start_date=self.start_date,
                end_date=self.end_date,
                initial_cash=100000,
                fees=0.001,
                slippage=0.001
            )
            
            # 准备回测数据
            backtest_signals = {}
            for symbol in self.symbols:
                # 为每个股票创建简单信号
                if symbol in price_data and not price_data[symbol].empty:
                    df = price_data[symbol]
                    # 使用20日移动平均线作为简单信号
                    ma_20 = df['close'].rolling(20).mean()
                    signal = pd.DataFrame(index=df.index)
                    signal['hybrid_signal'] = (df['close'] > ma_20).astype(float) * 2 - 1  # -1, 1信号
                    backtest_signals[symbol] = signal
            
            if not backtest_signals:
                print("❌ 没有有效的回测信号")
                return
            
            print(f"🎯 回测配置:")
            print(f"  初始资金: ${backtest_config.initial_cash:,.0f}")
            print(f"  手续费率: {backtest_config.fees:.3%}")
            print(f"  滑点: {backtest_config.slippage:.3%}")
            print(f"  回测标的: {len(backtest_signals)} 个")
            
            # 运行回测
            results = self.vbt_engine.vectorized_backtest(
                list(backtest_signals.keys()),
                price_data,
                backtest_signals,
                backtest_config
            )
            
            print(f"\n📊 回测结果:")
            for symbol, result in results.items():
                metrics = result.metrics
                print(f"\n📈 {symbol}:")
                print(f"  总收益率: {metrics.get('total_return', 0):.2%}")
                print(f"  Sharpe比率: {metrics.get('sharpe_ratio', 0):.2f}")
                print(f"  最大回撤: {metrics.get('max_drawdown', 0):.2%}")
                print(f"  年化收益率: {metrics.get('annual_return', 0):.2%}")
                print(f"  交易次数: {metrics.get('total_trades', 0)}")
                print(f"  胜率: {metrics.get('win_rate', 0):.2%}")
                print(f"  执行时间: {result.execution_time:.2f}秒")
            
            return results
            
        except Exception as e:
            print(f"❌ 回测执行失败: {e}")
            return {}
    
    async def demo_optimization(self, price_data, economic_data):
        """演示参数优化"""
        print("\n🔧 演示参数优化...")
        
        try:
            # 配置优化参数
            param_grid = {
                "price_weight": [0.4, 0.6, 0.8],
                "economic_weight": [0.2, 0.4, 0.6],
                "lookback_period": [10, 20, 30]
            }
            
            optimization_config = OptimizationConfig(
                max_processes=2,  # 限制进程数以避免资源问题
                use_threading=False,
                cache_enabled=True,
                timeout_per_task=60  # 1分钟超时
            )
            
            backtest_config = BacktestConfig(
                start_date=self.start_date,
                end_date=self.end_date,
                initial_cash=100000
            )
            
            total_combinations = 1
            for values in param_grid.values():
                total_combinations *= len(values)
            
            print(f"🎯 优化配置:")
            print(f"  参数组合数: {total_combinations}")
            print(f"  优化进程数: {optimization_config.max_processes}")
            print(f"  超时时间: {optimization_config.timeout_per_task}秒")
            
            # 创建并行优化器
            optimizer = ParallelOptimizer(optimization_config)
            
            # 运行优化（只使用前2个股票以加快演示）
            symbols_subset = self.symbols[:2]
            
            # 生成简化的经济数据用于优化
            simple_economic_data = {}
            for source, df in economic_data.items():
                if not df.empty:
                    # 取第一个指标的值作为简化数据
                    if 'rate' in df.columns:
                        simple_economic_data[source] = df['rate']
                    elif 'value' in df.columns:
                        simple_economic_data[source] = df['value']
                    elif 'export_value' in df.columns:
                        simple_economic_data[source] = df['export_value']
            
            print(f"\n⚡ 开始参数优化...")
            
            results = optimizer.optimize_parameters_parallel(
                symbols_subset,
                price_data,
                simple_economic_data,
                param_grid,
                backtest_config
            )
            
            print(f"\n🏆 优化结果:")
            if results:
                print(f"  有效结果数: {len(results)}")
                
                # 显示前5个最佳结果
                top_results = results[:5]
                for i, result in enumerate(top_results, 1):
                    print(f"\n  #{i} 参数组合:")
                    print(f"    参数: {result.parameters}")
                    print(f"    质量评分: {result.quality_score:.2f}")
                    print(f"    Sharpe比率: {result.sharpe_ratio:.2f}")
                    print(f"    总收益率: {result.total_return:.2%}")
                    print(f"    最大回撤: {result.max_drawdown:.2%}")
                    print(f"    执行时间: {result.execution_time:.2f}秒")
            else:
                print("  ⚠️ 没有找到有效的优化结果")
            
            # 获取性能统计
            perf_stats = optimizer.get_performance_stats()
            print(f"\n📊 性能统计:")
            print(f"  内存使用: {perf_stats['memory_usage']:.1%}")
            print(f"  执行器类型: {perf_stats['executor_type']}")
            print(f"  最大工作进程: {perf_stats['max_workers']}")
            
            # 清理资源
            optimizer.cleanup()
            
            return results
            
        except Exception as e:
            print(f"❌ 参数优化失败: {e}")
            return []
    
    def demo_performance_stats(self):
        """演示性能统计"""
        print("\n📊 演示性能统计...")
        
        try:
            # 获取VectorBT引擎性能信息
            perf_stats = self.vbt_engine.get_performance_stats()
            
            print(f"🖥️ 系统信息:")
            print(f"  GPU加速: {'启用' if perf_stats['gpu_acceleration'] else '禁用'}")
            print(f"  缓存启用: {'启用' if perf_stats['cache_enabled'] else '禁用'}")
            print(f"  最大进程数: {perf_stats['max_processes']}")
            
            # 显示可用内存
            try:
                import psutil
                memory = psutil.virtual_memory()
                print(f"  系统内存: {memory.total / (1024**3):.1f}GB")
                print(f"  可用内存: {memory.available / (1024**3):.1f}GB ({memory.percent:.1f}%已使用)")
            except ImportError:
                print("  需要安装psutil来查看内存信息")
            
        except Exception as e:
            print(f"❌ 获取性能统计失败: {e}")
    
    async def run_demo(self):
        """运行完整演示"""
        start_time = datetime.now()
        
        try:
            # 1. 生成示例数据
            price_data, economic_data = self.generate_sample_data()
            
            # 2. 演示技术指标计算
            indicators_df = self.demo_technical_indicators(price_data)
            
            # 3. 演示信号生成
            signals = await self.demo_signal_generation(price_data, economic_data)
            
            # 4. 演示回测
            backtest_results = self.demo_backtest(price_data, signals)
            
            # 5. 演示参数优化
            optimization_results = await self.demo_optimization(price_data, economic_data)
            
            # 6. 演示性能统计
            self.demo_performance_stats()
            
            # 总结
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 60)
            print("🎉 VectorBT集成演示完成!")
            print("=" * 60)
            print(f"⏱️ 总执行时间: {execution_time:.2f}秒")
            print(f"📈 处理股票数: {len(self.symbols)}")
            print(f"📊 数据时间范围: {(self.end_date - self.start_date).days}天")
            
            print(f"\n✅ 完成的功能演示:")
            print(f"  🎯 混合信号生成: {'✅' if not signals.empty else '❌'}")
            print(f"  📊 技术指标计算: {'✅' if not indicators_df.empty else '❌'}")
            print(f"  ⚡ VectorBT回测: {'✅' if backtest_results else '❌'}")
            print(f"  🔧 参数优化: {'✅' if optimization_results else '❌'}")
            
            print(f"\n🚀 VectorBT深度集成已准备就绪!")
            print(f"   可以开始使用完整的量化交易功能")
            
        except Exception as e:
            print(f"\n❌ 演示执行失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    print("启动VectorBT回测演示...")
    
    demo = VectorBTBacktestDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())