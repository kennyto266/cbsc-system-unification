#!/usr/bin/env python3
"""
阿程Sharpe Ratio计算器
基于USD/CNH预测HSI期货的实时交易信号和统计计算

策略逻辑:
1. USD/CNH连续4天都是正(负)回报
2. 4天累积回报大于(小于)0.4%(-0.4%)
3. 生成买入/卖出信号
4. 实时计算Sharpe Ratio和相关统计指标

特性:
- 无持仓延迟的即时信号
- 实时Sharpe Ratio计算
- 完整的风险指标
- 交易成本考虑
- 高性能计算优化

作者: 基于"阿程"策略优化
日期: 2025-11-30
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AchengSharpeCalculator:
    """
    阿程Sharpe比率计算器

    实现USD/CNH预测HSI期货的策略逻辑，
    提供无持仓延迟的实时交易信号和统计计算
    """

    def __init__(self,
                 lookback_days: int = 4,
                 cumulative_threshold: float = 0.004,
                 risk_free_rate: float = 0.02,
                 trading_days_per_year: int = 252,
                 transaction_cost: float = 0.0002):
        """
        初始化计算器

        Args:
            lookback_days: 回看天数 (默认4天)
            cumulative_threshold: 累积回报阈值 (默认0.4%)
            risk_free_rate: 无风险利率 (默认2%)
            trading_days_per_year: 每年交易日数 (默认252)
            transaction_cost: 交易成本 (默认0.02%)
        """
        self.lookback_days = lookback_days
        self.cumulative_threshold = cumulative_threshold
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
        self.transaction_cost = transaction_cost

        # 初始化统计存储
        self.signals_history = []
        self.current_position = 0  # 0=无仓位, 1=多头, -1=空头
        self.position_entry_price = None
        self.position_entry_date = None

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: 包含HSIF_close和USDCNH_close的数据框

        Returns:
            添加了技术指标的数据框
        """
        # 计算日回报
        df['HSIF_return'] = df['HSIF_close'].pct_change()
        df['USDCNH_return'] = df['USDCNH_close'].pct_change()

        # 计算历史回报列
        for i in range(self.lookback_days):
            df[f'T-{i}_USDCNH_return'] = df['USDCNH_return'].shift(i)

        # 计算累积回报
        df[f'{self.lookback_days}_days_USDCNH_return'] = (
            df['USDCNH_close'] / df['USDCNH_close'].shift(self.lookback_days) - 1
        )

        # 计算HSIF的T+1回报 (用于计算策略表现)
        df['T+1_HSIF_return'] = df['HSIF_return'].shift(-1)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            df: 包含技术指标的数据框

        Returns:
            添加了信号的数据框
        """
        df['signal'] = 0  # 0=无信号, 1=买入, -1=卖出

        # 生成买入信号 (USD/CNH连续4天负回报且累积<-0.4%)
        buy_conditions = []
        for i in range(self.lookback_days):
            buy_conditions.append(df[f'T-{i}_USDCNH_return'] < 0)

        buy_mask = (
            np.all(buy_conditions, axis=0) &
            (df[f'{self.lookback_days}_days_USDCNH_return'] < -self.cumulative_threshold)
        )

        df.loc[buy_mask, 'signal'] = 1

        # 生成卖出信号 (USD/CNH连续4天正回报且累积>0.4%)
        sell_conditions = []
        for i in range(self.lookback_days):
            sell_conditions.append(df[f'T-{i}_USDCNH_return'] > 0)

        sell_mask = (
            np.all(sell_conditions, axis=0) &
            (df[f'{self.lookback_days}_days_USDCNH_return'] > self.cumulative_threshold)
        )

        df.loc[sell_mask, 'signal'] = -1

        return df

    def calculate_real_time_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算实时回报 (无持仓延迟)

        Args:
            df: 包含信号的数据框

        Returns:
            添加了策略回报的数据框
        """
        # 初始化回报列
        df['strategy_return'] = 0.0
        df['position'] = 0  # 当前持仓状态

        # 逐日计算策略回报
        for i in range(len(df)):
            current_signal = df.iloc[i]['signal']

            # 如果有信号，更新持仓状态
            if current_signal != 0:
                self.current_position = current_signal
                self.position_entry_price = df.iloc[i]['HSIF_close']
                self.position_entry_date = df.iloc[i]['Date']

                # 记录信号历史
                self.signals_history.append({
                    'date': self.position_entry_date,
                    'signal': current_signal,
                    'entry_price': self.position_entry_price
                })

            # 记录当前持仓状态
            df.loc[df.index[i], 'position'] = self.current_position

            # 计算当日策略回报 (基于信号预测的T+1回报)
            if i < len(df) - 1:  # 确保有T+1数据
                strategy_return = df.iloc[i]['signal'] * df.iloc[i]['T+1_HSIF_return']

                # 扣除交易成本 (只在有信号时扣除)
                if df.iloc[i]['signal'] != 0:
                    strategy_return -= self.transaction_cost

                df.loc[df.index[i], 'strategy_return'] = strategy_return

        return df

    def calculate_sharpe_statistics(self, df: pd.DataFrame) -> Dict:
        """
        计算完整的Sharpe Ratio和统计指标

        Args:
            df: 包含策略回报的数据框

        Returns:
            统计指标字典
        """
        # 过滤有效交易数据
        valid_returns = df[df['strategy_return'] != 0]['strategy_return']

        if len(valid_returns) == 0:
            return self._empty_statistics()

        # 基础统计
        total_return = (1 + valid_returns).prod() - 1
        mean_return = valid_returns.mean()
        std_return = valid_returns.std()

        # 年化统计
        annual_return = mean_return * self.trading_days_per_year
        annual_volatility = std_return * np.sqrt(self.trading_days_per_year)

        # Sharpe Ratio
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

        # 时间相关统计
        start_date = df['Date'].min()
        end_date = df['Date'].max()
        year_diff = (end_date - start_date).days / 365.25

        # CAGR (复合年增长率)
        cagr = (total_return + 1) ** (1 / year_diff) - 1 if year_diff > 0 else 0

        # 交易统计
        total_trading_days = len(df)
        trading_days_with_signals = len(valid_returns)
        exposure_ratio = trading_days_with_signals / total_trading_days if total_trading_days > 0 else 0

        # 曝露调整回报
        exposed_adjusted_returns = cagr / exposure_ratio if exposure_ratio > 0 else 0

        # 最大回撤计算
        cumulative_returns = (1 + df['strategy_return']).cumprod()
        cumulative_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns / cumulative_max - 1)
        max_drawdown = drawdown.min()

        # 信号统计
        buy_signals = len(df[df['signal'] == 1])
        sell_signals = len(df[df['signal'] == -1])

        return {
            "Start Date": start_date,
            "End Date": end_date,
            "Total Trading Days": total_trading_days,
            "Trading Days with Signals": trading_days_with_signals,
            "Buy Signals": buy_signals,
            "Sell Signals": sell_signals,
            "Total Return": total_return,
            "Annual Return": annual_return,
            "Sharpe Ratio": sharpe_ratio,
            "CAGR": cagr,
            "Annual Volatility": annual_volatility,
            "Max Drawdown": max_drawdown,
            "Exposure Ratio": exposure_ratio,
            "Exposed Adjusted Returns": exposed_adjusted_returns
        }

    def _empty_statistics(self) -> Dict:
        """返回空统计指标"""
        return {
            "Start Date": None,
            "End Date": None,
            "Total Trading Days": 0,
            "Trading Days with Signals": 0,
            "Buy Signals": 0,
            "Sell Signals": 0,
            "Total Return": 0.0,
            "Annual Return": 0.0,
            "Sharpe Ratio": 0.0,
            "CAGR": 0.0,
            "Annual Volatility": 0.0,
            "Max Drawdown": 0.0,
            "Exposure Ratio": 0.0,
            "Exposed Adjusted Returns": 0.0
        }

    def process_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        处理数据的主函数

        Args:
            df: 原始数据 (包含Date, HSIF_close, USDCNH_close)

        Returns:
            处理后的数据框和统计指标
        """
        # 确保日期格式正确
        df['Date'] = pd.to_datetime(df['Date'])

        # 计算技术指标
        df = self.calculate_technical_indicators(df)

        # 生成交易信号
        df = self.generate_signals(df)

        # 计算实时回报
        df = self.calculate_real_time_returns(df)

        # 计算统计指标
        statistics = self.calculate_sharpe_statistics(df)

        return df, statistics

    def get_latest_signal(self, df: pd.DataFrame) -> Dict:
        """
        获取最新的交易信号

        Args:
            df: 处理后的数据框

        Returns:
            最新信号信息
        """
        latest = df.iloc[-1]

        return {
            "date": latest['Date'],
            "hsif_close": latest['HSIF_close'],
            "usdcnh_close": latest['USDCNH_close'],
            "signal": latest['signal'],
            "usdcnh_return": latest['USDCNH_return'],
            "cumulative_usdcnh_return": latest[f'{self.lookback_days}_days_USDCNH_return'],
            "position": latest['position'],
            "strategy_return": latest['strategy_return']
        }

    def export_results(self, df: pd.DataFrame, statistics: Dict,
                      output_file: str = "acheng_sharpe_results.csv"):
        """
        导出结果到CSV文件

        Args:
            df: 处理后的数据框
            statistics: 统计指标
            output_file: 输出文件名
        """
        df.to_csv(output_file, index=False)

        # 保存统计指标到JSON
        import json
        stats_file = output_file.replace('.csv', '_statistics.json')

        # 转换datetime对象为字符串
        serializable_stats = {}
        for key, value in statistics.items():
            if hasattr(value, 'strftime'):
                serializable_stats[key] = value.strftime('%Y-%m-%d')
            else:
                serializable_stats[key] = value

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_stats, f, indent=2, ensure_ascii=False)


def main():
    """
    主函数 - 演示阿程Sharpe计算器的使用
    """
    print("=== 阿程Sharpe Ratio计算器启动 ===")
    print("基于USD/CNH预测HSI期货的实时交易策略")
    print()

    # 创建计算器实例
    calculator = AchengSharpeCalculator(
        lookback_days=4,
        cumulative_threshold=0.004,
        transaction_cost=0.0002
    )

    # 读取数据 (使用阿程的数据格式)
    try:
        df = pd.read_csv("HSIF_USDCNH_201009_202412.csv")
        print(f"✓ 成功加载数据: {len(df)} 行")
        print(f"  时间范围: {df.iloc[0]['Date']} 至 {df.iloc[-1]['Date']}")
        print()
    except FileNotFoundError:
        print("❌ 未找到数据文件，生成模拟数据...")
        # 生成模拟数据
        np.random.seed(42)
        dates = pd.date_range('2010-09-01', periods=1000, freq='D')

        # 生成USD/CNH价格 (基础价格 + 趋势 + 噪声)
        usdcnh_base = 6.8
        trend = np.sin(np.linspace(0, 4*np.pi, 1000)) * 0.3
        noise = np.random.normal(0, 0.01, 1000)
        usdcnh_prices = usdcnh_base + trend + noise

        # 生成HSI期货价格 (与USD/CNH有一定的负相关性)
        hsi_base = 20000
        hsi_trend = -np.sin(np.linspace(0, 4*np.pi, 1000)) * 1000  # 负相关
        hsi_noise = np.random.normal(0, 200, 1000)
        hsi_prices = hsi_base + hsi_trend + hsi_noise

        df = pd.DataFrame({
            'Date': dates,
            'HSIF_close': hsi_prices,
            'USDCNH_close': usdcnh_prices
        })
        print(f"✓ 生成模拟数据: {len(df)} 行")
        print()

    # 处理数据
    print("处理数据并计算指标...")
    processed_df, statistics = calculator.process_data(df)

    # 显示统计结果
    print("=== 策略统计结果 ===")
    print(f"总交易日数: {statistics['Total Trading Days']:,}")
    print(f"有信号的交易日: {statistics['Trading Days with Signals']:,}")
    print(f"买入信号数: {statistics['Buy Signals']:,}")
    print(f"卖出信号数: {statistics['Sell Signals']:,}")
    print(f"暴露比例: {statistics['Exposure Ratio']:.2%}")
    print()
    print("=== 收益表现 ===")
    print(f"总回报率: {statistics['Total Return']:+.2%}")
    print(f"年化回报率: {statistics['Annual Return']:+.2%}")
    print(f"CAGR: {statistics['CAGR']:+.2%}")
    print(f"年化波动率: {statistics['Annual Volatility']:.2%}")
    print(f"夏普比率: {statistics['Sharpe Ratio']:.3f}")
    print(f"最大回撤: {statistics['Max Drawdown']:+.2%}")
    print()

    # 获取最新信号
    latest_signal = calculator.get_latest_signal(processed_df)
    print("=== 最新交易信号 ===")
    print(f"日期: {latest_signal['date'].strftime('%Y-%m-%d')}")
    print(f"HSI期货收盘价: {latest_signal['hsif_close']:,.2f}")
    print(f"USD/CNH收盘价: {latest_signal['usdcnh_close']:.4f}")
    print(f"USD/CNH日回报: {latest_signal['usdcnh_return']:+.4f}")
    print(f"4天累积回报: {latest_signal['cumulative_usdcnh_return']:+.4f}")
    print(f"交易信号: {latest_signal['signal']} ({'买入' if latest_signal['signal']==1 else '卖出' if latest_signal['signal']==-1 else '无信号'})")
    print(f"当前持仓: {latest_signal['position']} ({'多头' if latest_signal['position']==1 else '空头' if latest_signal['position']==-1 else '无持仓'})")
    print()

    # 显示最近的信号历史
    if len(calculator.signals_history) > 0:
        print("=== 最近信号历史 ===")
        recent_signals = calculator.signals_history[-5:]
        for signal in recent_signals:
            signal_type = "买入" if signal['signal'] == 1 else "卖出"
            print(f"{signal['date'].strftime('%Y-%m-%d')}: {signal_type} @ {signal['entry_price']:,.2f}")
        print()

    # 性能评估
    print("=== 性能评估 ===")
    if statistics['Sharpe Ratio'] > 1.0:
        print("🌟 优秀策略! Sharpe比率 > 1.0")
    elif statistics['Sharpe Ratio'] > 0.5:
        print("✅ 良好策略! Sharpe比率 > 0.5")
    elif statistics['Sharpe Ratio'] > 0:
        print("⚠️  可接受策略! Sharpe比率 > 0")
    else:
        print("❌ 需要改进策略! Sharpe比率 < 0")

    if statistics['Max Drawdown'] > -0.20:
        print("✅ 风险控制良好! 最大回撤 < 20%")
    else:
        print("⚠️  风险较高! 最大回撤 > 20%")

    print()

    # 导出结果
    output_file = "acheng_sharpe_results.csv"
    calculator.export_results(processed_df, statistics, output_file)
    print(f"✓ 结果已导出到: {output_file}")

    return processed_df, statistics


if __name__ == "__main__":
    # 运行主函数
    df, stats = main()