"""
Mixed Data Strategy Example
混合數據策略示例

展示如何同時使用價格數據和非價格（經濟）數據進行量化交易
"""

import asyncio
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 添加項目路徑
sys.path.append('..')

from src.strategies.quant_strategy_framework import (
    create_strategy_config, StrategyType, StrategyManager
)
from src.strategies.examples.example_strategies import (
    MovingAverageCrossoverStrategy,
    RSIMeanReversionStrategy
)
from src.strategies.examples.fundamental_strategies_v2 import (
    HIBORStrategyV2,
    GDPGrowthStrategyV2,
    PMIStrategyV2,
    CompositeFundamentalStrategy
)
from src.strategies.strategy_backtester import (
    BacktestEngine, BacktestConfig, BacktestAnalyzer
)
from src.strategies.data_provider import get_data_provider

async def main():
    """主函數 - 混合數據策略演示"""

    print("="*60)
    print("CBS-C 混合數據策略開發示例")
    print("="*60)

    # 1. 創建價格數據策略
    print("\n1. 創建價格數據策略...")

    ma_config = create_strategy_config(
        name="MA交叉策略",
        strategy_type=StrategyType.MOMENTUM,
        symbols=["HSI"],  # 恆生指數
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.3,
        risk_limit=0.02,
        fast_period=10,
        slow_period=30
    )

    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    print("✅ MA交叉策略創建完成")

    # 2. 創建經濟數據策略
    print("\n2. 創建經濟數據策略...")

    hibor_config = create_strategy_config(
        name="HIBOR策略",
        strategy_type=StrategyType.STATISTICAL,
        symbols=["HSI"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.2,
        risk_limit=0.02,
        lookback_period=30,
        rate_threshold_high=5.0,
        rate_threshold_low=2.0
    )

    hibor_strategy = HIBORStrategyV2(hibor_config)
    print("✅ HIBOR策略創建完成")

    # 3. 創建綜合基本面策略
    print("\n3. 創建綜合基本面策略...")

    composite_config = create_strategy_config(
        name="綜合基本面策略",
        strategy_type=StrategyType.STATISTICAL,
        symbols=["HSI"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.4,
        risk_limit=0.02,
        indicator_weights={
            'hibor': 0.4,
            'gdp': 0.3,
            'pmi': 0.3
        },
        hibor_lookback=30,
        gdp_high=0.05,
        pmi_expansion=55
    )

    composite_strategy = CompositeFundamentalStrategy(composite_config)
    print("✅ 綜合基本面策略創建完成")

    # 4. 準備混合數據
    print("\n4. 準備混合數據...")

    # 獲取價格數據
    data_provider = get_data_provider()
    price_data = await data_provider.get_market_data(
        symbols=["HSI"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        timeframe="1d",
        fields=['open', 'high', 'low', 'close', 'volume']
    )

    print(f"✅ 獲取價格數據: {len(price_data)} 天")

    # 5. 初始化策略
    print("\n5. 初始化策略...")

    strategies = [ma_strategy, hibor_strategy, composite_strategy]
    initialized = []

    for strategy in strategies:
        if strategy.initialize():
            initialized.append(strategy)
            print(f"  ✅ {strategy.config.name} 初始化成功")
        else:
            print(f"  ❌ {strategy.config.name} 初始化失敗")

    # 6. 運行模擬交易
    print("\n6. 運行模擬交易...")

    # 確保數據格式正確
    if not price_data.empty:
        # 為每個策略準備數據
        prepared_data = price_data.copy()

        # 運行每個策略
        results = {}
        for strategy in initialized:
            print(f"\n  運行策略: {strategy.config.name}")

            # 生成信號
            signals = strategy.generate_signals(prepared_data)

            # 模擬交易執行
            trades = []
            capital = strategy.config.initial_capital
            positions = {}

            for signal in signals:
                # 計算倉位大小
                position_size = strategy.calculate_position_size(signal, capital)

                # 模擬執行
                if signal.signal_type.value in ['buy', 'sell']:
                    trades.append({
                        'timestamp': signal.timestamp,
                        'symbol': signal.symbol,
                        'action': signal.signal_type.value,
                        'quantity': position_size,
                        'price': signal.price,
                        'strength': signal.strength,
                        'confidence': signal.confidence,
                        'metadata': signal.metadata
                    })

            results[strategy.config.name] = {
                'signals_count': len(signals),
                'trades_count': len(trades),
                'trades': trades[:10]  # 只顯示前10個交易
            }

            print(f"    生成信號: {len(signals)} 個")
            print(f"    模擬交易: {len(trades)} 筆")

    # 7. 分析結果
    print("\n7. 分析結果...")

    print("\n策略比較:")
    print("-" * 60)
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  信號數量: {result['signals_count']}")
        print(f"  交易數量: {result['trades_count']}")

        if result['trades']:
            print(f"  平均信號強度: {np.mean([t['strength'] for t in result['trades']]):.3f}")
            print(f"  平均置信度: {np.mean([t['confidence'] for t in result['trades']]):.3f}")

    # 8. 展示混合策略優勢
    print("\n8. 混合數據策略優勢:")
    print("""
    🔍 多維度分析:
    - 價格數據: 捕捉市場趨勢和技術信號
    - 經濟數據: 提供宏觀經濟背景和周期判斷
    - 綜合判斷: 減少單一數據源的噪音

    📊 策略組合建議:
    1. 趨勢策略 + 經濟週期判斷
       - 在經濟擴張期增加趨勢跟隨倉位
       - 在經濟收縮期減少倉位或反向操作

    2. 均值回歸 + 利率環境
       - 低利率環境下均值回歸效果更好
       - 高利率環境下謹慎使用均值回歸

    3. 突破策略 + PMI數據
       - PMI擴張期，突破策略成功率更高
       - PMI收縮期，注意假突破風險

    💡 實施建議:
    - 給予經濟數據更高的權重（經濟決定大趨勢）
    - 使用經濟數據調整策略倉位大小
    - 在經濟轉折點附近謹慎交易
    """)

    # 9. 創建混合策略示例
    print("\n9. 創建智能混合策略...")

    class SmartMixedStrategy(QuantStrategyBase):
        """智能混合策略 - 根據市場環境動態調整"""

        def __init__(self, config):
            super().__init__(config)
            self.ma_strategy = MovingAverageCrossoverStrategy(config)
            self.fundamental_strategy = CompositeFundamentalStrategy(config)
            self.market_mode = 'normal'  # 'bull', 'bear', 'normal'

        def initialize(self):
            # 初始化子策略
            self.ma_strategy.initialize()
            self.fundamental_strategy.initialize()
            return True

        def generate_signals(self, data):
            # 獲取兩種策略的信號
            price_signals = self.ma_strategy.generate_signals(data)
            fundamental_signals = self.fundamental_strategy.generate_signals(data)

            # 根據經濟環境調整權重
            if fundamental_signals:
                # 檢查最近的經濟信號
                recent_fundamental = fundamental_signals[-5:] if len(fundamental_signals) >= 5 else fundamental_signals
                bull_weight = sum(1 for s in recent_fundamental if s.signal_type.value == 'buy') / len(recent_fundamental)

                if bull_weight > 0.6:
                    self.market_mode = 'bull'
                    weight_factor = 1.5  # 牛市中加大價格策略權重
                elif bull_weight < 0.4:
                    self.market_mode = 'bear'
                    weight_factor = 0.5  # 熊市中減少價格策略權重
                else:
                    self.market_mode = 'normal'
                    weight_factor = 1.0

            # 合併信號
            all_signals = []

            # 調整價格信號強度
            for signal in price_signals:
                if hasattr(signal, 'strength'):
                    signal.strength *= weight_factor
                all_signals.append(signal)

            # 添加基本面信號（保持原權重）
            all_signals.extend(fundamental_signals)

            # 去重和優化
            filtered_signals = []
            signal_dict = {}

            for signal in all_signals:
                key = (signal.timestamp, signal.symbol)
                if key not in signal_dict or signal.strength > signal_dict[key].strength:
                    signal_dict[key] = signal

            filtered_signals = list(signal_dict.values())
            return filtered_signals

        def calculate_position_size(self, signal, portfolio_value):
            # 根據市場模式調整倉位
            base_size = portfolio_value * self.config.max_position_size

            if self.market_mode == 'bull':
                multiplier = 1.2
            elif self.market_mode == 'bear':
                multiplier = 0.6
            else:
                multiplier = 1.0

            return base_size * signal.strength * multiplier / signal.price

    # 創建並測試智能混合策略
    mixed_config = create_strategy_config(
        name="智能混合策略",
        strategy_type=StrategyType.STATISTICAL,
        symbols=["HSI"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.3,
        risk_limit=0.02,
        fast_period=10,
        slow_period=30,
        indicator_weights={'hibor': 0.5, 'gdp': 0.5}
    )

    mixed_strategy = SmartMixedStrategy(mixed_config)
    if mixed_strategy.initialize():
        mixed_signals = mixed_strategy.generate_signals(prepared_data)
        print(f"\n✅ 智能混合策略生成 {len(mixed_signals)} 個信號")
        print(f"   市場模式: {mixed_strategy.market_mode}")

    # 10. 最佳實踐總結
    print("\n10. 最佳實踐總結:")
    print("""
    📌 數據整合原則:
    1. 數據質量 > 數據數量
    2. 理解各數據源的特性和局限性
    3. 注意不同頻率數據的對齊問題
    4. 避免未來函數（lookahead bias）

    📌 策略設計建議:
    1. 經濟數據決定大方向，價格數據決定時機
    2. 使用經濟數據調整策略風險暴露
    3. 建立經濟狀況的過濾器
    4. 定期重新評估和調整權重

    📌 實施注意事項:
    1. 經濟數據發布延遲（注意及時性）
    2. 數據修訂問題（可能影響回測結果）
    3. 相關性分析（避免多重共線性）
    4. 樣本外測試（確保策略穩健性）
    """)

    print("\n" + "="*60)
    print("混合數據策略示例完成！")
    print("="*60)

if __name__ == "__main__":
    # 設置日誌
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 運行示例
    asyncio.run(main())