#!/usr/bin/env python3
"""
S&P 500基準對比分析
驗證修正後的夏普比率計算與市場基準的一致性
"""

import sys
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

from professional_sharpe_calculator import ProfessionalSharpeCalculator

def get_sp500_benchmark_data():
    """
    獲取S&P 500歷史基準數據

    Returns:
        dict: S&P 500基準性能指標
    """
    # S&P 500 長期歷史平均數據 (1928-2023)
    # 來源：多個金融研究機構的綜合數據

    return {
        'annual_return': 0.101,    # 10.1% 年化回報
        'annual_volatility': 0.156,  # 15.6% 年化波動率
        'sharpe_ratio': 0.45,      # 基於3%無風險利率
        'max_drawdown': -0.508,     # -50.8% 最大回撤
        'time_period': '1928-2023 (95年)',
        'description': 'S&P 500歷史長期基準'
    }

def generate_market_scenarios():
    """
    生成不同市場情景的模擬數據
    """
    scenarios = {}

    # 情景1: 標準S&P 500類型策略
    np.random.seed(42)
    sp500_like_returns = np.random.normal(0.000382, 0.0098, 252)  # 10.1%年化，15.6%年化波動
    scenarios['sp500_like'] = {
        'returns': sp500_like_returns,
        'description': 'S&P 500 標準表現 (10.1%年化回報)',
        'expected_sharpe': 0.45
    }

    # 情景2: 超額收益策略 (如MB_KDJ_[10,2])
    np.random.seed(123)
    excess_returns = np.random.normal(0.0018, 0.018, 252)  # 更高回報，中等波動
    scenarios['excess_alpha'] = {
        'returns': excess_returns,
        'description': '超額收益策略 (高Alpha)',
        'expected_sharpe': '1.0-2.0'
    }

    # 情景3: 高波動率策略
    np.random.seed(456)
    high_vol_returns = np.random.normal(0.0012, 0.025, 252)  # 高波動率
    scenarios['high_volatility'] = {
        'returns': high_vol_returns,
        'description': '高波動率策略',
        'expected_sharpe': '0.3-0.8'
    }

    # 情景4: 低波動率策略
    np.random.seed(789)
    low_vol_returns = np.random.normal(0.0006, 0.008, 252)  # 低波動率
    scenarios['low_volatility'] = {
        'returns': low_vol_returns,
        'description': '低波動率穩健策略',
        'expected_sharpe': '0.8-1.5'
    }

    return scenarios

def calculate_comprehensive_metrics(returns):
    """
    計算綜合性能指標
    """
    calculator = ProfessionalSharpeCalculator()

    # 計算基本指標
    annual_return = (1 + np.mean(returns))**252 - 1
    annual_volatility = np.std(returns, ddof=1) * np.sqrt(252)
    sharpe = calculator.get_recommended_sharpe(returns)

    # 計算最大回撤
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

    # 計算其他指標
    # Sortino比率 (只考慮下行波動)
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 0:
        downside_vol = np.std(downside_returns, ddof=1) * np.sqrt(252)
        sortino = (annual_return - 0.03) / downside_vol
    else:
        sortino = 0

    # Calmar比率
    if max_drawdown != 0:
        calmar = annual_return / abs(max_drawdown)
    else:
        calmar = 0

    return {
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'sortino_ratio': sortino,
        'calmar_ratio': calmar,
        'win_rate': len(returns[returns > 0]) / len(returns),
        'data_points': len(returns)
    }

def validate_against_standards(metrics, category):
    """
    對照行業標準驗證性能指標
    """
    validations = {}

    # 行業標準參考值
    standards = {
        'sp500_like': {
            'sharpe_range': (0.3, 0.6),
            'volatility_range': (0.12, 0.20),
            'max_dd_range': (-0.6, -0.3),
            'excellent_sharpe': 0.8
        },
        'excess_alpha': {
            'sharpe_range': (1.0, 3.0),
            'volatility_range': (0.12, 0.25),
            'max_dd_range': (-0.3, -0.1),
            'excellent_sharpe': 2.0
        },
        'low_volatility': {
            'sharpe_range': (0.8, 2.0),
            'volatility_range': (0.06, 0.12),
            'max_dd_range': (-0.2, -0.05),
            'excellent_sharpe': 1.5
        },
        'high_volatility': {
            'sharpe_range': (0.2, 0.8),
            'volatility_range': (0.18, 0.35),
            'max_dd_range': (-0.6, -0.3),
            'excellent_sharpe': 1.0
        }
    }

    if category in standards:
        stds = standards[category]
        sharpe = metrics['sharpe_ratio']
        vol = metrics['annual_volatility']
        dd = metrics['max_drawdown']

        # 驗證各項指標
        validations['sharpe_in_range'] = stds['sharpe_range'][0] <= sharpe <= stds['sharpe_range'][1]
        validations['volatility_in_range'] = stds['volatility_range'][0] <= vol <= stds['volatility_range'][1]
        validations['max_drawdown_in_range'] = stds['max_dd_range'][0] <= dd <= stds['max_dd_range'][1]

        # 評估整體表現
        validations['is_excellent'] = sharpe >= stds['excellent_sharpe']
        validations['overall_assessment'] = (
            validations['sharpe_in_range'] and
            validations['volatility_in_range'] and
            validations['max_drawdown_in_range']
        )

    return validations

def main():
    print("S&P 500 基準對比分析")
    print("=" * 60)

    # 獲取S&P 500基準數據
    sp500_benchmark = get_sp500_benchmark_data()

    print(f"\n📊 S&P 500 歷史基準 ({sp500_benchmark['time_period']}):")
    print(f"年化回報率: {sp500_benchmark['annual_return']:.3f}")
    print(f"年化波動率: {sp500_benchmark['annual_volatility']:.3f}")
    print(f"夏普比率: {sp500_benchmark['sharpe_ratio']:.3f}")
    print(f"最大回撤: {sp500_benchmark['max_drawdown']:.3f}")
    print()

    # 生成市場情景
    scenarios = generate_market_scenarios()

    print("🔍 策略性能分析 (基於修正後的夏普比率計算):")
    print("-" * 80)

    for name, scenario in scenarios.items():
        returns = scenario['returns']
        metrics = calculate_comprehensive_metrics(returns)

        print(f"\n{name.upper().replace('_', ' ')}:")
        print(f"描述: {scenario['description']}")
        print(f"預期夏普: {scenario['expected_sharpe']}")
        print()
        print(f"計算結果:")
        print(f"  年化回報率: {metrics['annual_return']:.3f}")
        print(f"  年化波動率: {metrics['annual_volatility']:.3f}")
        print(f"  夏普比率:   {metrics['sharpe_ratio']:.3f}")
        print(f"  最大回撤:   {metrics['max_drawdown']:.3f}")
        print(f"  Sortino比率: {metrics['sortino_ratio']:.3f}")
        print(f"  Calmar比率:  {metrics['calmar_ratio']:.3f}")
        print(f"  勝率:       {metrics['win_rate']:.3f}")

        # 與S&P 500比較
        sharpe_vs_sp500 = metrics['sharpe_ratio'] / sp500_benchmark['sharpe_ratio']
        return_vs_sp500 = metrics['annual_return'] / sp500_benchmark['annual_return']
        volatility_vs_sp500 = metrics['annual_volatility'] / sp500_benchmark['annual_volatility']

        print(f"\n與S&P 500比較:")
        print(f"  夏普比率倍數: {sharpe_vs_sp500:.2f}x")
        print(f"  回報率倍數:   {return_vs_sp500:.2f}x")
        print(f"  波動率倍數:   {volatility_vs_sp500:.2f}x")

        # 分類驗證
        category = 'sp500_like' if name == 'sp500_like' else (
            'excess_alpha' if name == 'excess_alpha' else (
            'low_volatility' if name == 'low_volatility' else 'high_volatility'
            )
        )

        validations = validate_against_standards(metrics, category)

        print(f"\n行業標準驗證 ({category}):")
        print(f"  夏普比率正常範圍: {'✅' if validations['sharpe_in_range'] else '❌'}")
        print(f"  波動率正常範圍:   {'✅' if validations['volatility_in_range'] else '❌'}")
        print(f"  最大回撤正常範圍: {'✅' if validations['max_drawdown_in_range'] else '❌'}")
        print(f"  整體評估:         {'優秀' if validations['is_excellent'] else '正常' if validations['overall_assessment'] else '異常'}")

        # 基於S&P 500的排名
        if sharpe_vs_sp500 > 1.5:
            sp500_rank = "遠超S&P 500"
        elif sharpe_vs_sp500 > 1.0:
            sp500_rank = "優於S&P 500"
        elif sharpe_vs_sp500 > 0.7:
            sp500_rank = "接近S&P 500"
        else:
            sp500_rank = "不如S&P 500"

        print(f"  相對S&P 500表現: {sp500_rank}")

    print(f"\n" + "=" * 60)
    print("📈 基於S&P 500的投資等級:")
    print("-" * 30)
    print("Sharpe > 3.0     : 世級策略")
    print("Sharpe > 2.0     : 優秀策略")
    print("Sharpe > 1.5     : 良好策略")
    print("Sharpe > 1.0     : 可接受")
    print("Sharpe 0.5-1.0   : 一般")
    print("Sharpe < 0.5     : 不可接受")
    print()
    print("S&P 500 基準:   Sharpe 0.45")
    print("建議閾值:      Sharpe > 1.0 (超過S&P 500)")

if __name__ == "__main__":
    main()