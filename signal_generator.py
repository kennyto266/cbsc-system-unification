"""
Signal Generator for CBSC Backtesting System
CBSC回測系統信號生成器

Generate sentiment-based trading signals optimized for VectorBT backtesting.
為VectorBT回測優化的基於情緒的交易信號生成。

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from enum import Enum

class SignalType(Enum):
    """信號類型枚舉"""
    BUY_BULL = 1      # 買入牛證
    SELL_BEAR = -1    # 買入熊證
    HOLD = 0          # 持有

class CBSCSignalGenerator:
    """CBSC信號生成器 - 專為VectorBT回測設計"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信號生成器

        Args:
            config: 配置參數
        """
        self.config = config or self._default_config()

    def _default_config(self) -> Dict:
        """默認配置參數"""
        return {
            'sentiment_threshold': 0.3,      # 情緒閾值
            'extreme_sentiment_boost': 1.5,  # 極端情緒加權
            'rsi_overbought': 70,           # RSI超買閾值
            'rsi_oversold': 30,             # RSI超賣閾值
            'volume_multiplier': 1.2,        # 成交量放大倍數
            'signal_smoothing': 3,           # 信號平滑天數
            'min_turnover_threshold': 1000000  # 最小成交額閾值
        }

    def generate_sentiment_signals(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        生成基於情緒的交易信號

        Args:
            features_df: 特徵數據DataFrame

        Returns:
            包含信號的DataFrame
        """
        df = features_df.copy()

        # 1. 基礎情緒信號
        df['Sentiment_Signal'] = np.where(
            df['Sentiment_Strength'] > self.config['sentiment_threshold'],
            SignalType.BUY_BULL.value,
            np.where(
                df['Sentiment_Strength'] < -self.config['sentiment_threshold'],
                SignalType.SELL_BEAR.value,
                SignalType.HOLD.value
            )
        )

        # 2. 極端情緒加權
        extreme_mask = df['Sentiment_Level'].isin(['EXTREME BULL', 'EXTREME BEAR'])
        df.loc[extreme_mask, 'Sentiment_Signal'] *= self.config['extreme_sentiment_boost']

        # 3. 成交量確認
        volume_valid = df['Total_Turnover'] >= self.config['min_turnover_threshold']
        df.loc[~volume_valid, 'Sentiment_Signal'] = SignalType.HOLD.value

        # 4. 信號平滑（減少噪音）
        df['Sentiment_Signal_Smoothed'] = (
            df['Sentiment_Signal']
            .rolling(window=self.config['signal_smoothing'], center=True)
            .mean()
            .fillna(df['Sentiment_Signal'])
        )

        # 5. 最終信號（離散化）
        df['Final_Sentiment_Signal'] = np.where(
            df['Sentiment_Signal_Smoothed'] > 0.5,
            SignalType.BUY_BULL.value,
            np.where(
                df['Sentiment_Signal_Smoothed'] < -0.5,
                SignalType.SELL_BEAR.value,
                SignalType.HOLD.value
            )
        )

        return df

    def generate_technical_signals(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        生成技術指標信號

        Args:
            features_df: 特徵數據DataFrame

        Returns:
            包含技術信號的DataFrame
        """
        df = features_df.copy()

        # RSI信號
        df['RSI_Signal'] = np.where(
            df['RSI'] < self.config['rsi_oversold'],
            SignalType.BUY_BULL.value,
            np.where(
                df['RSI'] > self.config['rsi_overbought'],
                SignalType.SELL_BEAR.value,
                SignalType.HOLD.value
            )
        )

        # 移動平均線信號
        df['MA_Signal'] = np.where(
            (df['MA5'] > df['MA20']) & (df['close'] > df['MA5']),
            SignalType.BUY_BULL.value,
            np.where(
                (df['MA5'] < df['MA20']) & (df['close'] < df['MA5']),
                SignalType.SELL_BEAR.value,
                SignalType.HOLD.value
            )
        )

        # 價格動量信號
        df['Momentum_Signal'] = np.where(
            df['Returns'] > 0.02,  # 2%以上漲幅
            SignalType.BUY_BULL.value,
            np.where(
                df['Returns'] < -0.02,  # 2%以上跌幅
                SignalType.SELL_BEAR.value,
                SignalType.HOLD.value
            )
        )

        return df

    def generate_cbsc_aware_signals(self, features_df: pd.DataFrame,
                                  call_price_buffer: float = 0.05) -> pd.DataFrame:
        """
        生成CBSC感知信號（考慮收回價風險）

        Args:
            features_df: 特徵數據DataFrame
            call_price_buffer: 收回價緩衝區

        Returns:
            包含CBSC感知信號的DataFrame
        """
        df = features_df.copy()

        # 模擬收回價（假設為當前價格的80%作為牛證收回價，120%作為熊證收回價）
        df['Bull_Call_Price'] = df['close'] * 0.8
        df['Bear_Call_Price'] = df['close'] * 1.2

        # 計算距離收回價的距離
        df['Bull_Call_Distance'] = (df['close'] - df['Bull_Call_Price']) / df['close']
        df['Bear_Call_Distance'] = (df['Bear_Call_Price'] - df['close']) / df['close']

        # 收回價風險調整
        bull_risk_adjustment = np.clip(df['Bull_Call_Distance'] / call_price_buffer, 0, 1)
        bear_risk_adjustment = np.clip(df['Bear_Call_Distance'] / call_price_buffer, 0, 1)

        # 生成基礎信號
        df = self.generate_sentiment_signals(df)
        df = self.generate_technical_signals(df)

        # CBSC風險調整信號
        df['CBSC_Bull_Signal'] = df['Final_Sentiment_Signal'] * bull_risk_adjustment
        df['CBSC_Bear_Signal'] = -df['Final_Sentiment_Signal'] * bear_risk_adjustment

        # 選擇較安全的信號
        df['CBSC_Adjusted_Signal'] = np.where(
            df['CBSC_Bull_Signal'] > abs(df['CBSC_Bear_Signal']),
            np.where(df['CBSC_Bull_Signal'] > 0.3, SignalType.BUY_BULL.value, SignalType.HOLD.value),
            np.where(abs(df['CBSC_Bear_Signal']) > 0.3, SignalType.SELL_BEAR.value, SignalType.HOLD.value)
        )

        return df

    def generate_vectorbt_signals(self, features_df: pd.DataFrame,
                                 signal_type: str = 'cbsc_aware') -> Tuple[pd.Series, pd.Series]:
        """
        為VectorBT生成進入和退出信號

        Args:
            features_df: 特徵數據DataFrame
            signal_type: 信號類型 ('sentiment', 'technical', 'cbsc_aware')

        Returns:
            (進入信號Series, 退出信號Series)
        """
        # 生成信號
        if signal_type == 'sentiment':
            df = self.generate_sentiment_signals(features_df)
            signal_col = 'Final_Sentiment_Signal'
        elif signal_type == 'technical':
            df = self.generate_technical_signals(features_df)
            # 綜合技術信號
            df['Combined_Technical'] = (
                df['RSI_Signal'] + df['MA_Signal'] + df['Momentum_Signal']
            ) / 3
            signal_col = 'Combined_Technical'
        else:  # cbsc_aware
            df = self.generate_cbsc_aware_signals(features_df)
            signal_col = 'CBSC_Adjusted_Signal'

        # 生成VectorBT格式的信號
        entries = df[signal_col] == SignalType.BUY_BULL.value
        exits = df[signal_col] == SignalType.SELL_BEAR.value

        # 轉換為boolean類型
        entries = entries.astype(bool)
        exits = exits.astype(bool)

        print(f"生成 {signal_type} 信號: {entries.sum()} 個進入信號, {exits.sum()} 個退出信號")

        return entries, exits

    def generate_multiple_strategies(self, features_df: pd.DataFrame) -> Dict[str, Tuple[pd.Series, pd.Series]]:
        """
        生成多種策略的信號

        Args:
            features_df: 特徵數據DataFrame

        Returns:
            策略名稱到信號的映射
        """
        strategies = {}

        # 1. 純情緒策略
        strategies['sentiment_only'] = self.generate_vectorbt_signals(
            features_df, 'sentiment'
        )

        # 2. 純技術策略
        strategies['technical_only'] = self.generate_vectorbt_signals(
            features_df, 'technical'
        )

        # 3. CBSC感知策略
        strategies['cbsc_aware'] = self.generate_vectorbt_signals(
            features_df, 'cbsc_aware'
        )

        # 4. 保守策略（僅在極端情緒時交易）
        df_conservative = features_df.copy()
        extreme_mask = df_conservative['Sentiment_Level'].isin(['EXTREME BULL', 'EXTREME BEAR'])
        df_conservative.loc[~extreme_mask, 'Final_Sentiment_Signal'] = SignalType.HOLD.value

        entries = (df_conservative['Final_Sentiment_Signal'] == SignalType.BUY_BULL.value) & extreme_mask
        exits = (df_conservative['Final_Sentiment_Signal'] == SignalType.SELL_BEAR.value) & extreme_mask

        strategies['conservative'] = (entries.astype(bool), exits.astype(bool))

        # 5. 積極策略（低閾值）
        aggressive_config = self.config.copy()
        aggressive_config['sentiment_threshold'] = 0.1
        aggressive_generator = CBSCSignalGenerator(aggressive_config)

        df_aggressive = features_df.copy()
        df_aggressive = aggressive_generator.generate_sentiment_signals(df_aggressive)

        entries = df_aggressive['Final_Sentiment_Signal'] == SignalType.BUY_BULL.value
        exits = df_aggressive['Final_Sentiment_Signal'] == SignalType.SELL_BEAR.value

        strategies['aggressive'] = (entries.astype(bool), exits.astype(bool))

        print(f"生成 {len(strategies)} 種策略信號")
        for strategy_name, (entries, exits) in strategies.items():
            print(f"  {strategy_name}: {entries.sum()} 進入, {exits.sum()} 退出")

        return strategies

    def analyze_signal_quality(self, features_df: pd.DataFrame,
                             entries: pd.Series, exits: pd.Series) -> Dict:
        """
        分析信號質量

        Args:
            features_df: 特徵數據
            entries: 進入信號
            exits: 退出信號

        Returns:
            信號質量分析結果
        """
        analysis = {}

        # 信號數量
        analysis['total_entries'] = int(entries.sum())
        analysis['total_exits'] = int(exits.sum())
        analysis['signal_ratio'] = analysis['total_entries'] / max(1, len(features_df))

        # 信號分布
        signal_days = (entries | exits).sum()
        analysis['signal_frequency'] = float(signal_days / len(features_df))

        # 情緒信號質量
        valid_sentiment_days = features_df['Total_Turnover'] >= self.config['min_turnover_threshold']
        analysis['sentiment_data_quality'] = float(valid_sentiment_days.sum() / len(features_df))

        # 極端情緒比例
        extreme_days = features_df['Sentiment_Level'].isin(['EXTREME BULL', 'EXTREME BEAR']).sum()
        analysis['extreme_sentiment_ratio'] = float(extreme_days / len(features_df))

        # 信號與回報相關性
        if entries.sum() > 0:
            entry_returns = features_df.loc[entries, 'Returns'].dropna()
            analysis['avg_entry_return'] = float(entry_returns.mean()) if len(entry_returns) > 0 else 0.0
            analysis['entry_return_std'] = float(entry_returns.std()) if len(entry_returns) > 0 else 0.0

        return analysis

def main():
    """測試信號生成器"""
    print("=== CBSC Signal Generator 測試 ===")

    # 模擬數據
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    mock_data = pd.DataFrame({
        'Date': dates,
        'close': 100 + np.cumsum(np.random.randn(100) * 0.02),
        'Sentiment_Strength': np.random.randn(100) * 0.3,
        'Total_Turnover': np.random.randint(1000000, 10000000, 100),
        'Sentiment_Level': np.random.choice(
            ['EXTREME BULL', 'MOD BULL', 'NEUTRAL', 'MOD BEAR', 'EXTREME BEAR'],
            100
        ),
        'RSI': 50 + np.random.randn(100) * 10,
        'Returns': np.random.randn(100) * 0.02
    })

    # 計算移動平均線
    mock_data['MA5'] = mock_data['close'].rolling(5).mean()
    mock_data['MA20'] = mock_data['close'].rolling(20).mean()
    mock_data = mock_data.dropna().reset_index(drop=True)

    print(f"創建模擬數據: {len(mock_data)} 條記錄")

    # 初始化信號生成器
    generator = CBSCSignalGenerator()

    # 生成多種策略信號
    print("\n1. 生成策略信號...")
    strategies = generator.generate_multiple_strategies(mock_data)

    # 分析信號質量
    print("\n2. 分析信號質量...")
    for strategy_name, (entries, exits) in strategies.items():
        quality = generator.analyze_signal_quality(mock_data, entries, exits)
        print(f"\n{strategy_name} 策略:")
        for key, value in quality.items():
            print(f"  {key}: {value:.3f}")

    print("\n✅ CBSC Signal Generator 測試完成！")

if __name__ == "__main__":
    main()