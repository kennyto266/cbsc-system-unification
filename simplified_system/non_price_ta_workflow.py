#!/usr / bin / env python3
"""
非價格數據技術分析完整工作流程
Non - Price Data Technical Analysis Complete Workflow

邏輯鏈: 非價格數據 → 技術指標 → 買賣信號 → 回測
Logic Chain: Non - Price Data → Technical Indicators → Trading Signals → Backtesting
"""

import json
import logging
import multiprocessing as mp
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'api'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'indicators'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backtest'))

try:
    from api.government_data import GovernmentDataAPI
    from api.stock_api import get_hk_stock_data
    from indicators.core_indicators import CoreIndicators

    from backtest.vectorbt_engine import VectorBTEngine

    # 設置日誌
    logging.basicConfig(level = logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    class NonPriceTechnicalAnalyzer:
        """非價格技術分析器"""

        def __init__(self):
            self.gov_api = GovernmentDataAPI()
            self.indicators = CoreIndicators()
            self.available_sources = {}

        def collect_non_price_data(self) -> Dict[str, pd.Series]:
            """收集非價格數據"""
            print("📊 [步驟 1 / 4] 收集非價格數據...")

            non_price_data = {}

            try:
                # 1. HIBOR利率數據
                print("   🔍 收集HIBOR利率數據...")
                hibor_data = self._get_hibor_data()
                if hibor_data is not None:
                    non_price_data['hibor_rates'] = hibor_data
                    print(f"   ✅ HIBOR: {len(hibor_data)} 條記錄")

                # 2. 貨幣基礎數據
                print("   🔍 收集貨幣基礎數據...")
                monetary_data = self._get_monetary_base_data()
                if monetary_data is not None:
                    non_price_data['monetary_base'] = monetary_data
                    print(f"   ✅ 貨幣基礎: {len(monetary_data)} 條記錄")

                # 3. 匯率數據
                print("   🔍 收集匯率數據...")
                exchange_data = self._get_exchange_rate_data()
                if exchange_data is not None:
                    non_price_data['exchange_rates'] = exchange_data
                    print(f"   ✅ 匯率: {len(exchange_data)} 條記錄")

                # 4. 模擬其他經濟數據（基於真實數據生成）
                print("   🔍 生成擴展經濟數據...")
                extended_data = self._generate_extended_economic_data(non_price_data)
                non_price_data.update(extended_data)

                self.available_sources = non_price_data
                print(f"   📈 總共收集 {len(non_price_data)} 個非價格數據源")
                return non_price_data

            except Exception as e:
                logger.error(f"收集非價格數據失敗: {e}")
                return {}

        def _get_hibor_data(self) -> Optional[pd.Series]:
            """獲取HIBOR數據"""
            try:
                # 使用真實數據文件
                hibor_files = [
                    "data / government / hibor_rates_20251124_174050.json",
                    "../data / government / hibor_rates_20251124_174050.json",
                    "backup_mock_files / 真實DATA / hibor_5y.csv"
                ]

                for file_path in hibor_files:
                    if os.path.exists(file_path):
                        if file_path.endswith('.json'):
                            with open(file_path, 'r', encoding='utf - 8') as f:
                                data = json.load(f)
                                if isinstance(data, list) and len(data) > 0:
                                    # 轉換為pandas Series
                                    dates = []
                                    rates = []
                                    for item in data[:365]:  # 限制到最近一年
                                        if 'date' in item and 'rate' in item:
                                            dates.append(pd.to_datetime(item['date']))
                                            rates.append(float(item['rate']))

                                    if dates and rates:
                                        series = pd.Series(rates, index = dates)
                                        return series.sort_index()
                        elif file_path.endswith('.csv'):
                            df = pd.read_csv(file_path)
                            if 'date' in df.columns and 'rate' in df.columns:
                                df['date'] = pd.to_datetime(df['date'])
                                series = pd.Series(df['rate'].values, index = df['date'])
                                return series.sort_index()

                # 如果真實數據不可用，生成模擬數據
                print("   ⚠️ 真實HIBOR數據不可用，使用高質量模擬數據")
                dates = pd.date_range(end = datetime.now(), periods = 365, freq='D')
                np.random.seed(42)
                base_rate = 3.5
                rates = base_rate + np.cumsum(np.random.normal(0, 0.02, 365)) * 0.1
                rates = np.clip(rates, 1.0, 8.0)  # 合理範圍

                return pd.Series(rates, index = dates)

            except Exception as e:
                logger.warning(f"獲取HIBOR數據失敗: {e}")
                return None

        def _get_monetary_base_data(self) -> Optional[pd.Series]:
            """獲取貨幣基礎數據"""
            try:
                # 使用真實數據文件
                monetary_files = [
                    "data / final_real_indicators / hkma_real_data_with_indicators.csv",
                    "../data / final_real_indicators / hkma_real_data_with_indicators.csv"
                ]

                for file_path in monetary_files:
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                        if 'date' in df.columns and len(df.columns) > 1:
                            # 尋找貨幣基礎相關列
                            monetary_cols = [col for col in df.columns if
                                          'monetary' in col.lower() or 'base' in col.lower() or 'money' in col.lower()]

                            if monetary_cols:
                                col = monetary_cols[0]
                                df['date'] = pd.to_datetime(df['date'])
                                series = pd.Series(df[col].values, index = df['date'])
                                return series.sort_index()

                # 生成模擬貨幣基礎數據
                print("   ⚠️ 真實貨幣基礎數據不可用，使用高質量模擬數據")
                dates = pd.date_range(end = datetime.now(), periods = 365, freq='D')
                np.random.seed(123)
                base_value = 2000000  # 20億港幣
                growth_trend = np.linspace(0, 0.02, 365)  # 2%年增長
                random_fluctuation = np.random.normal(0, 0.005, 365)
                values = base_value * (1 + growth_trend + random_fluctuation)

                return pd.Series(values, index = dates)

            except Exception as e:
                logger.warning(f"獲取貨幣基礎數據失敗: {e}")
                return None

        def _get_exchange_rate_data(self) -> Optional[pd.Series]:
            """獲取匯率數據"""
            try:
                # 生成模擬美元兌港幣匯率數據
                print("   ⚠️ 使用模擬美元兌港幣匯率數據")
                dates = pd.date_range(end = datetime.now(), periods = 365, freq='D')
                np.random.seed(456)
                base_rate = 7.8
                rates = base_rate + np.cumsum(np.random.normal(0, 0.01, 365)) * 0.01
                rates = np.clip(rates, 7.5, 8.1)  # 合理範圍

                return pd.Series(rates, index = dates)

            except Exception as e:
                logger.warning(f"獲取匯率數據失敗: {e}")
                return None

        def _generate_extended_economic_data(self, base_data: Dict[str, pd.Series]) -> Dict[str, pd.Series]:
            """基於基礎數據生成擴展經濟指標"""
            extended_data = {}

            try:
                if not base_data:
                    return extended_data

                # 獲取共同的日期範圍
                common_dates = None
                for series in base_data.values():
                    if common_dates is None:
                        common_dates = series.index
                    else:
                        common_dates = common_dates.intersection(series.index)

                if len(common_dates) < 50:  # 數據不足
                    return extended_data

                # 1. 利率變化率
                if 'hibor_rates' in base_data:
                    hibor = base_data['hibor_rates'].loc[common_dates]
                    extended_data['hibor_rate_change'] = hibor.pct_change().fillna(0)

                # 2. 貨幣供給增長率
                if 'monetary_base' in base_data:
                    monetary = base_data['monetary_base'].loc[common_dates]
                    extended_data['monetary_growth'] = monetary.pct_change().fillna(0)

                # 3. 匯率波動率
                if 'exchange_rates' in base_data:
                    exchange = base_data['exchange_rates'].loc[common_dates]
                    extended_data['exchange_volatility'] = exchange.pct_change().rolling(20).std().fillna(0)

                # 4. 綜合流動性指標
                if 'hibor_rates' in base_data and 'monetary_base' in base_data:
                    hibor = base_data['hibor_rates'].loc[common_dates]
                    monetary = base_data['monetary_base'].loc[common_dates]

                    # 標準化兩個指標
                    hibor_norm = (hibor - hibor.mean()) / hibor.std()
                    monetary_norm = (monetary - monetary.mean()) / monetary.std()

                    # 流動性指標 = 貨幣供給正向 - 利率反向
                    liquidity = monetary_norm - hibor_norm
                    extended_data['liquidity_index'] = liquidity

                # 5. 經濟壓力指標
                if len(extended_data) > 0:
                    # 基於現有指標計算壓力指標
                    stress_factors = []
                    for name, series in extended_data.items():
                        if name not in ['liquidity_index']:  # 排除已經是綜合指標的
                            # Z - score標準化
                            z_score = (series - series.mean()) / series.std()
                            stress_factors.append(z_score.abs())

                    if stress_factors:
                        stress_index = sum(stress_factors) / len(stress_factors)
                        extended_data['economic_stress'] = stress_index

                print(f"   ✅ 生成 {len(extended_data)} 個擴展經濟指標")
                return extended_data

            except Exception as e:
                logger.warning(f"生成擴展經濟數據失敗: {e}")
                return {}

        def calculate_technical_indicators(self, data: Dict[str, pd.Series]) -> Dict[str, Dict[str, Any]]:
            """計算技術指標"""
            print("\n🔧 [步驟 2 / 4] 計算技術指標...")

            indicator_results = {}

            for source_name, series in data.items():
                try:
                    if len(series) < 20:  # 數據不足
                        continue

                    print(f"   📈 計算 {source_name} 技術指標...")

                    indicators = {}

                    # 1. RSI
                    try:
                        rsi_periods = [14, 21, 30]
                        for period in rsi_periods:
                            rsi = self.indicators.calculate_rsi(series, period)
                            if not rsi.empty:
                                indicators[f'rsi_{period}'] = {
                                    'current': rsi.iloc[-1],
                                    'series': rsi,
                                    'period': period,
                                    'signal': self._rsi_signal(rsi.iloc[-1])
                                }
                    except Exception as e:
                        logger.warning(f"{source_name} RSI計算失敗: {e}")

                    # 2. MACD
                    try:
                        macd_result = self.indicators.calculate_macd(series, 12, 26, 9)
                        if not macd_result.empty:
                            latest_macd = macd_result.iloc[-1]
                            indicators['macd'] = {
                                'current': latest_macd['macd'],
                                'signal': latest_macd['signal'],
                                'histogram': latest_macd['histogram'],
                                'series': macd_result,
                                'signal_type': self._macd_signal(latest_macd['macd'], latest_macd['signal'])
                            }
                    except Exception as e:
                        logger.warning(f"{source_name} MACD計算失敗: {e}")

                    # 3. 移動平均
                    try:
                        sma_periods = [10, 20, 50]
                        for period in sma_periods:
                            sma = self.indicators.calculate_sma(series, period)
                            if not sma.empty:
                                indicators[f'sma_{period}'] = {
                                    'current': sma.iloc[-1],
                                    'series': sma,
                                    'period': period
                                }
                    except Exception as e:
                        logger.warning(f"{source_name} SMA計算失敗: {e}")

                    # 4. 布林帶
                    try:
                        bb_result = self.indicators.calculate_bollinger_bands(series, 20, 2.0)
                        if not bb_result.empty:
                            latest_bb = bb_result.iloc[-1]
                            indicators['bollinger'] = {
                                'current': series.iloc[-1],
                                'upper': latest_bb['upper'],
                                'middle': latest_bb['middle'],
                                'lower': latest_bb['lower'],
                                'series': bb_result,
                                'position': self._bollinger_position(series.iloc[-1], latest_bb)
                            }
                    except Exception as e:
                        logger.warning(f"{source_name} 布林帶計算失敗: {e}")

                    # 5. 動量指標
                    try:
                        momentum = self.indicators.calculate_rate_of_change(series, 10)
                        if not momentum.empty:
                            indicators['momentum'] = {
                                'current': momentum.iloc[-1],
                                'series': momentum,
                                'signal': self._momentum_signal(momentum.iloc[-1])
                            }
                    except Exception as e:
                        logger.warning(f"{source_name} 動量指標計算失敗: {e}")

                    # 6. 綜合評分
                    indicators['composite_score'] = self._calculate_composite_score(indicators, series)

                    indicator_results[source_name] = indicators

                except Exception as e:
                    logger.warning(f"計算 {source_name} 技術指標失敗: {e}")
                    continue

            print(f"   ✅ 成功計算 {len(indicator_results)} 個數據源的技術指標")
            return indicator_results

        def _rsi_signal(self, rsi_value: float) -> str:
            """RSI信號判斷"""
            if rsi_value < 30:
                return "oversold"  # 超賣（買入信號）
            elif rsi_value > 70:
                return "overbought"  # 超買（賣出信號）
            else:
                return "neutral"

        def _macd_signal(self, macd: float, signal: float) -> str:
            """MACD信號判斷"""
            if macd > signal:
                return "bullish"  # 看漲
            elif macd < signal:
                return "bearish"  # 看跌
            else:
                return "neutral"

        def _bollinger_position(self, current: float, bb_line: pd.Series) -> str:
            """布林帶位置判斷"""
            upper = bb_line['upper']
            lower = bb_line['lower']
            middle = bb_line['middle']

            if current > upper:
                return "above_upper"  # 超買
            elif current < lower:
                return "below_lower"  # 超賣
            elif current > middle:
                return "upper_half"
            else:
                return "lower_half"

        def _momentum_signal(self, momentum: float) -> str:
            """動量信號判斷"""
            if momentum > 0.02:
                return "strong_bullish"
            elif momentum > 0:
                return "bullish"
            elif momentum < -0.02:
                return "strong_bearish"
            else:
                return "bearish"

        def _calculate_composite_score(self, indicators: Dict[str, Any], series: pd.Series) -> float:
            """計算綜合評分"""
            try:
                score = 0.5  # 基礎分
                weight_sum = 1.0

                # RSI權重 (30%)
                for key, rsi_data in indicators.items():
                    if key.startswith('rsi_'):
                        rsi_val = rsi_data['current']
                        if rsi_val < 30:
                            score += 0.3  # 超賣加分
                        elif rsi_val > 70:
                            score -= 0.3  # 超買減分
                        weight_sum += 0.3
                        break

                # MACD權重 (25%)
                if 'macd' in indicators:
                    macd_data = indicators['macd']
                    if macd_data['signal_type'] == 'bullish':
                        score += 0.25
                    elif macd_data['signal_type'] == 'bearish':
                        score -= 0.25
                    weight_sum += 0.25

                # 勢量權重 (20%)
                if 'momentum' in indicators:
                    momentum_data = indicators['momentum']
                    if 'bullish' in momentum_data['signal']:
                        score += 0.2
                    elif 'bearish' in momentum_data['signal']:
                        score -= 0.2
                    weight_sum += 0.2

                # 布林帶權重 (15%)
                if 'bollinger' in indicators:
                    bb_data = indicators['bollinger']
                    if bb_data['position'] == 'below_lower':
                        score += 0.15  # 超賣加分
                    elif bb_data['position'] == 'above_upper':
                        score -= 0.15  # 超買減分
                    weight_sum += 0.15

                # 標準化到0 - 1範圍
                final_score = max(0, min(1, score / weight_sum if weight_sum > 0 else 0.5))
                return final_score

            except Exception as e:
                logger.warning(f"計算綜合評分失敗: {e}")
                return 0.5

        def generate_trading_signals(self, indicator_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
            """生成買賣信號"""
            print("\n📡 [步驟 3 / 4] 生成買賣信號...")

            trading_signals = {}

            for source_name, indicators in indicator_results.items():
                try:
                    print(f"   🎯 生成 {source_name} 交易信號...")

                    signals = {
                        'primary_signal': 'HOLD',
                        'signal_strength': 0.5,
                        'confidence': 0.5,
                        'individual_signals': {},
                        'signal_rationale': []
                    }

                    # 收集個別指標信號
                    signal_votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                    total_weight = 0

                    # RSI信號 (權重: 0.3)
                    for key, rsi_data in indicators.items():
                        if key.startswith('rsi_'):
                            rsi_signal = rsi_data['signal']
                            if rsi_signal == 'oversold':
                                signal_votes['BUY'] += 3
                                signals['individual_signals']['rsi'] = 'BUY'
                                signals['signal_rationale'].append(f"RSI超賣 ({rsi_data['current']:.1f})")
                            elif rsi_signal == 'overbought':
                                signal_votes['SELL'] += 3
                                signals['individual_signals']['rsi'] = 'SELL'
                                signals['signal_rationale'].append(f"RSI超買 ({rsi_data['current']:.1f})")
                            else:
                                signal_votes['HOLD'] += 1
                                signals['individual_signals']['rsi'] = 'HOLD'
                            total_weight += 3
                            break

                    # MACD信號 (權重: 0.25)
                    if 'macd' in indicators:
                        macd_data = indicators['macd']
                        macd_signal = macd_data['signal_type']
                        if macd_signal == 'bullish':
                            signal_votes['BUY'] += 2.5
                            signals['individual_signals']['macd'] = 'BUY'
                            signals['signal_rationale'].append("MACD看漲交叉")
                        elif macd_signal == 'bearish':
                            signal_votes['SELL'] += 2.5
                            signals['individual_signals']['macd'] = 'SELL'
                            signals['signal_rationale'].append("MACD看跌交叉")
                        else:
                            signal_votes['HOLD'] += 1
                            signals['individual_signals']['macd'] = 'HOLD'
                        total_weight += 2.5

                    # 勢量信號 (權重: 0.2)
                    if 'momentum' in indicators:
                        momentum_data = indicators['momentum']
                        momentum_signal = momentum_data['signal']
                        if 'bullish' in momentum_signal:
                            signal_votes['BUY'] += 2
                            signals['individual_signals']['momentum'] = 'BUY'
                            signals['signal_rationale'].append("正向動量")
                        elif 'bearish' in momentum_signal:
                            signal_votes['SELL'] += 2
                            signals['individual_signals']['momentum'] = 'SELL'
                            signals['signal_rationale'].append("負向動量")
                        else:
                            signal_votes['HOLD'] += 1
                            signals['individual_signals']['momentum'] = 'HOLD'
                        total_weight += 2

                    # 布林帶信號 (權重: 0.15)
                    if 'bollinger' in indicators:
                        bb_data = indicators['bollinger']
                        bb_position = bb_data['position']
                        if bb_position == 'below_lower':
                            signal_votes['BUY'] += 1.5
                            signals['individual_signals']['bollinger'] = 'BUY'
                            signals['signal_rationale'].append("價格低於布林帶下軌")
                        elif bb_position == 'above_upper':
                            signal_votes['SELL'] += 1.5
                            signals['individual_signals']['bollinger'] = 'SELL'
                            signals['signal_rationale'].append("價格高於布林帶上軌")
                        else:
                            signal_votes['HOLD'] += 1
                            signals['individual_signals']['bollinger'] = 'HOLD'
                        total_weight += 1.5

                    # 綜合評分 (權重: 0.1)
                    if 'composite_score' in indicators:
                        comp_score = indicators['composite_score']
                        if comp_score > 0.7:
                            signal_votes['BUY'] += 1
                            signals['signal_rationale'].append(f"高綜合評分 ({comp_score:.2f})")
                        elif comp_score < 0.3:
                            signal_votes['SELL'] += 1
                            signals['signal_rationale'].append(f"低綜合評分 ({comp_score:.2f})")
                        else:
                            signal_votes['HOLD'] += 0.5
                        total_weight += 1

                    # 確定主要信號
                    if total_weight > 0:
                        buy_strength = signal_votes['BUY'] / total_weight
                        sell_strength = signal_votes['SELL'] / total_weight
                        hold_strength = signal_votes['HOLD'] / total_weight

                        if buy_strength > 0.6:
                            signals['primary_signal'] = 'BUY'
                            signals['signal_strength'] = buy_strength
                        elif sell_strength > 0.6:
                            signals['primary_signal'] = 'SELL'
                            signals['signal_strength'] = sell_strength
                        else:
                            signals['primary_signal'] = 'HOLD'
                            signals['signal_strength'] = hold_strength

                        # 信心度基於信號一致性
                        max_strength = max(buy_strength, sell_strength, hold_strength)
                        signals['confidence'] = min(max_strength * 1.2, 1.0)  # 放大但限制在1.0

                    trading_signals[source_name] = signals

                except Exception as e:
                    logger.warning(f"生成 {source_name} 交易信號失敗: {e}")
                    continue

            print(f"   ✅ 成功生成 {len(trading_signals)} 個交易信號")
            return trading_signals

        def run_comprehensive_backtest(self, non_price_data: Dict[str, pd.Series],
                                     trading_signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
            """運行綜合回測"""
            print("\n📊 [步驟 4 / 4] 運行綜合回測...")

            try:
                # 獲取股價數據進行回測
                print("   📈 獲取股價數據進行回測驗證...")
                stock_data = get_hk_stock_data('0700.HK', 365)

                if not stock_data or 'data' not in stock_data:
                    print("   ⚠️ 無法獲取股價數據，跳過回測")
                    return {'error': '無法獲取股價數據'}

                price_data = stock_data['data']['close']
                dates = list(price_data.keys())
                prices = list(price_data.values())

                if len(prices) < 50:
                    print("   ⚠️ 股價數據不足，跳過回測")
                    return {'error': '股價數據不足'}

                # 對齊非價格數據和股價數據
                aligned_data = self._align_data_sources(non_price_data, dates)

                if not aligned_data:
                    print("   ⚠️ 數據對齊失敗，跳過回測")
                    return {'error': '數據對齊失敗'}

                print(f"   📊 對齊數據點: {len(aligned_data)} 天")

                # 生成信號時間序列
                signal_series = self._generate_signal_time_series(aligned_data, trading_signals)

                if signal_series.empty:
                    print("   ⚠️ 信號生成失敗，跳過回測")
                    return {'error': '信號生成失敗'}

                # 運行回測
                backtest_results = self._execute_backtest(prices, signal_series)

                # 分析結果
                analysis = self._analyze_backtest_results(backtest_results, signal_series)

                print(f"   ✅ 回測完成，測試了 {len(backtest_results.get('trades', []))} 筆交易")

                return {
                    'backtest_results': backtest_results,
                    'signal_analysis': analysis,
                    'data_alignment': {
                        'price_data_points': len(prices),
                        'signal_data_points': len(signal_series),
                        'alignment_quality': 'good' if len(signal_series) > 100 else 'limited'
                    }
                }

            except Exception as e:
                logger.error(f"回測執行失敗: {e}")
                return {'error': str(e)}

        def _align_data_sources(self, non_price_data: Dict[str, pd.Series], price_dates: List[str]) -> Dict[str, pd.Series]:
            """對齊數據源"""
            try:
                # 轉換價格日期為datetime
                price_datetime = pd.to_datetime(price_dates)

                aligned_data = {}

                for source_name, series in non_price_data.items():
                    try:
                        # 對齊日期索引
                        common_dates = series.index.intersection(price_datetime)

                        if len(common_dates) > 30:  # 至少30天數據
                            aligned_series = series.loc[common_dates].sort_index()
                            aligned_data[source_name] = aligned_series

                    except Exception as e:
                        logger.warning(f"對齊 {source_name} 失敗: {e}")
                        continue

                return aligned_data

            except Exception as e:
                logger.error(f"數據對齊失敗: {e}")
                return {}

        def _generate_signal_time_series(self, aligned_data: Dict[str, pd.Series],
                                       trading_signals: Dict[str, Dict[str, Any]]) -> pd.Series:
            """生成信號時間序列"""
            try:
                if not aligned_data:
                    return pd.Series()

                # 獲取共同的日期範圍
                common_dates = None
                for series in aligned_data.values():
                    if common_dates is None:
                        common_dates = series.index
                    else:
                        common_dates = common_dates.intersection(series.index)

                if len(common_dates) < 30:
                    return pd.Series()

                # 為每個日期生成綜合信號
                daily_signals = []
                signal_dates = []

                for date in common_dates:
                    date_signals = []
                    signal_weights = []

                    for source_name, series in aligned_data.items():
                        if date in series.index:
                            # 模擬在該日期的技術分析
                            # 這裡簡化處理，實際應該基於歷史數據計算
                            if source_name in trading_signals:
                                signal_data = trading_signals[source_name]
                                signal_strength = signal_data.get('signal_strength', 0.5)
                                confidence = signal_data.get('confidence', 0.5)

                                # 根據信號強度決定信號
                                primary_signal = signal_data.get('primary_signal', 'HOLD')

                                # 轉換為數值 (-1 = SELL, 0 = HOLD, 1 = BUY)
                                if primary_signal == 'BUY':
                                    signal_value = 1.0
                                elif primary_signal == 'SELL':
                                    signal_value = -1.0
                                else:
                                    signal_value = 0.0

                                date_signals.append(signal_value * confidence)
                                signal_weights.append(confidence)

                    # 計算加權平均信號
                    if date_signals and signal_weights:
                        weighted_signal = sum(s * w for s, w in zip(date_signals, signal_weights)) / sum(signal_weights)
                        daily_signals.append(weighted_signal)
                        signal_dates.append(date)

                if not daily_signals:
                    return pd.Series()

                return pd.Series(daily_signals, index = signal_dates)

            except Exception as e:
                logger.error(f"生成信號時間序列失敗: {e}")
                return pd.Series()

        def _execute_backtest(self, prices: List[float], signals: pd.Series) -> Dict[str, Any]:
            """執行回測"""
            try:
                # 簡化回測邏輯
                initial_capital = 100000
                capital = initial_capital
                position = 0  # 0 = 空倉, 1 = 滿倉
                trades = []
                portfolio_values = []

                # 對齊信號和價格數據
                min_length = min(len(prices), len(signals))

                for i in range(min_length):
                    current_price = prices[i]
                    signal = signals.iloc[i] if i < len(signals) else 0

                    # 執行交易邏輯
                    if signal > 0.3 and position == 0:  # 買入信號且當前空倉
                        position = 1
                        shares = capital / current_price
                        trades.append({
                            'date': signals.index[i] if i < len(signals) else f'Day {i}',
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'signal_strength': signal
                        })

                    elif signal < -0.3 and position == 1:  # 賣出信號且當前滿倉
                        position = 0
                        portfolio_value = shares * current_price if 'shares' in locals() else capital
                        capital = portfolio_value
                        trades.append({
                            'date': signals.index[i] if i < len(signals) else f'Day {i}',
                            'action': 'SELL',
                            'price': current_price,
                            'portfolio_value': capital,
                            'signal_strength': signal
                        })

                    # 計算投資組合價值
                    if position == 1 and 'shares' in locals():
                        portfolio_value = shares * current_price
                    else:
                        portfolio_value = capital

                    portfolio_values.append(portfolio_value)

                # 計算最終結果
                final_value = portfolio_values[-1] if portfolio_values else initial_capital
                total_return = (final_value - initial_capital) / initial_capital

                # 計算日常回報用於Sharpe比率
                daily_returns = []
                for i in range(1, len(portfolio_values)):
                    daily_return = (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1]
                    daily_returns.append(daily_return)

                # Sharpe比率 (無風險利率3%)
                if daily_returns and np.std(daily_returns) > 0:
                    excess_returns = np.array(daily_returns) - 0.03 / 252
                    sharpe_ratio = np.mean(excess_returns) / np.std(daily_returns) * np.sqrt(252)
                else:
                    sharpe_ratio = 0

                # 最大回撤
                peak = portfolio_values[0] if portfolio_values else initial_capital
                max_drawdown = 0
                for value in portfolio_values:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)

                # 勝率計算
                winning_trades = 0
                losing_trades = 0

                for i in range(0, len(trades)-1, 2):
                    if i + 1 < len(trades):
                        buy_trade = trades[i]
                        sell_trade = trades[i + 1]
                        if buy_trade['action'] == 'BUY' and sell_trade['action'] == 'SELL':
                            if sell_trade['portfolio_value'] > buy_trade['price'] * buy_trade.get('shares', 0):
                                winning_trades += 1
                            else:
                                losing_trades += 1

                total_trades = winning_trades + losing_trades
                win_rate = winning_trades / total_trades if total_trades > 0 else 0

                return {
                    'initial_capital': initial_capital,
                    'final_value': final_value,
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'total_trades': len(trades),
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'portfolio_values': portfolio_values,
                    'trades': trades,
                    'daily_returns': daily_returns
                }

            except Exception as e:
                logger.error(f"回測執行失敗: {e}")
                return {'error': str(e)}

        def _analyze_backtest_results(self, results: Dict[str, Any], signals: pd.Series) -> Dict[str, Any]:
            """分析回測結果"""
            try:
                if 'error' in results:
                    return {'analysis_status': 'failed', 'error': results['error']}

                analysis = {
                    'analysis_status': 'success',
                    'performance_metrics': {
                        'total_return': results['total_return'],
                        'sharpe_ratio': results['sharpe_ratio'],
                        'max_drawdown': results['max_drawdown'],
                        'win_rate': results['win_rate'],
                        'trade_count': results['total_trades']
                    },
                    'signal_analysis': {
                        'signal_count': len(signals),
                        'buy_signals': sum(1 for s in signals if s > 0.3),
                        'sell_signals': sum(1 for s in signals if s < -0.3),
                        'hold_signals': sum(1 for s in signals if abs(s) <= 0.3),
                        'avg_signal_strength': np.mean(np.abs(signals)) if len(signals) > 0 else 0
                    },
                    'quality_assessment': {}
                }

                # 質量評估
                total_return = results['total_return']
                sharpe = results['sharpe_ratio']
                max_dd = results['max_drawdown']
                win_rate = results['win_rate']

                # 評分標準
                score = 0
                max_score = 100

                # 回報率評分 (30%)
                if total_return > 0.5:  # 50%以上
                    score += 30
                elif total_return > 0.2:  # 20%以上
                    score += 20
                elif total_return > 0.1:  # 10%以上
                    score += 10
                elif total_return > 0:
                    score += 5

                # Sharpe比率評分 (30%)
                if sharpe > 2.0:
                    score += 30
                elif sharpe > 1.5:
                    score += 25
                elif sharpe > 1.0:
                    score += 20
                elif sharpe > 0.5:
                    score += 15
                elif sharpe > 0:
                    score += 10

                # 最大回撤評分 (20%)
                if max_dd < 0.05:  # 5%以下
                    score += 20
                elif max_dd < 0.1:  # 10%以下
                    score += 15
                elif max_dd < 0.15:  # 15%以下
                    score += 10
                elif max_dd < 0.2:  # 20%以下
                    score += 5

                # 勝率評分 (20%)
                if win_rate > 0.6:  # 60%以上
                    score += 20
                elif win_rate > 0.5:  # 50%以上
                    score += 15
                elif win_rate > 0.4:  # 40%以上
                    score += 10
                elif win_rate > 0.3:  # 30%以上
                    score += 5

                analysis['quality_assessment'] = {
                    'overall_score': score,
                    'grade': self._get_grade(score),
                    'return_score': min(30, max(0, (total_return - 0.1) * 60)) if total_return > 0 else 0,
                    'sharpe_score': min(30, max(0, sharpe * 15)) if sharpe > 0 else 0,
                    'risk_score': max(0, 20 - max_dd * 100),
                    'win_rate_score': win_rate * 20
                }

                return analysis

            except Exception as e:
                logger.error(f"回測結果分析失敗: {e}")
                return {'analysis_status': 'failed', 'error': str(e)}

        def _get_grade(self, score: float) -> str:
            """獲取等級"""
            if score >= 85:
                return 'A+'
            elif score >= 75:
                return 'A'
            elif score >= 65:
                return 'B+'
            elif score >= 55:
                return 'B'
            elif score >= 45:
                return 'C+'
            elif score >= 35:
                return 'C'
            elif score >= 25:
                return 'D'
            else:
                return 'F'

        def run_complete_workflow(self) -> Dict[str, Any]:
            """運行完整工作流程"""
            print("=" * 80)
            print("🔄 非價格數據技術分析完整工作流程")
            print("邏輯鏈: 非價格數據 → 技術指標 → 買賣信號 → 回測")
            print("=" * 80)

            start_time = time.time()

            try:
                # 步驟1: 收集非價格數據
                non_price_data = self.collect_non_price_data()

                if not non_price_data:
                    return {'error': '無法收集非價格數據'}

                # 步驟2: 計算技術指標
                indicator_results = self.calculate_technical_indicators(non_price_data)

                if not indicator_results:
                    return {'error': '無法計算技術指標'}

                # 步驟3: 生成交易信號
                trading_signals = self.generate_trading_signals(indicator_results)

                if not trading_signals:
                    return {'error': '無法生成交易信號'}

                # 步驟4: 運行回測
                backtest_results = self.run_comprehensive_backtest(non_price_data, trading_signals)

                # 生成最終報告
                total_time = time.time() - start_time

                final_report = {
                    'workflow_info': {
                        'execution_time': total_time,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    },
                    'data_collection': {
                        'sources_count': len(non_price_data),
                        'data_points': {name: len(series) for name, series in non_price_data.items()},
                        'data_quality': 'good' if len(non_price_data) >= 3 else 'limited'
                    },
                    'technical_analysis': {
                        'indicators_calculated': len(indicator_results),
                        'indicator_types': ['RSI', 'MACD', 'SMA', 'Bollinger', 'Momentum'],
                        'composite_scores': {name: data.get('composite_score', 0)
                                           for name, data in indicator_results.items()}
                    },
                    'trading_signals': {
                        'signals_generated': len(trading_signals),
                        'signal_distribution': self._analyze_signal_distribution(trading_signals),
                        'avg_confidence': np.mean([s.get('confidence', 0) for s in trading_signals.values()])
                    },
                    'backtest_results': backtest_results,
                    'summary': self._generate_workflow_summary(
                        non_price_data, indicator_results, trading_signals, backtest_results
                    )
                }

                # 保存結果
                self._save_workflow_results(final_report)

                # 顯示結果摘要
                self._display_workflow_results(final_report)

                return final_report

            except Exception as e:
                logger.error(f"工作流程執行失敗: {e}")
                return {
                    'error': str(e),
                    'workflow_info': {
                        'execution_time': time.time() - start_time,
                        'status': 'failed'
                    }
                }

        def _analyze_signal_distribution(self, trading_signals: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
            """分析信號分佈"""
            distribution = {'BUY': 0, 'SELL': 0, 'HOLD': 0}

            for signal_data in trading_signals.values():
                primary_signal = signal_data.get('primary_signal', 'HOLD')
                if primary_signal in distribution:
                    distribution[primary_signal] += 1

            return distribution

        def _generate_workflow_summary(self, data: Dict, indicators: Dict,
                                     signals: Dict, backtest: Dict) -> Dict[str, Any]:
            """生成工作流程摘要"""
            try:
                summary = {
                    'data_quality': f"{len(data)} 數據源",
                    'analysis_coverage': f"{len(indicators)} 源完成技術分析",
                    'signal_generation': f"{len(signals)} 個信號源",
                }

                if 'error' not in backtest:
                    analysis = backtest.get('signal_analysis', {})
                    quality = analysis.get('quality_assessment', {})

                    summary.update({
                        'backtest_status': '成功',
                        'performance_grade': quality.get('grade', 'N / A'),
                        'total_score': quality.get('overall_score', 0),
                        'sharpe_ratio': backtest['backtest_results'].get('sharpe_ratio', 0),
                        'total_return': f"{backtest['backtest_results'].get('total_return', 0):.1%}",
                        'max_drawdown': f"{backtest['backtest_results'].get('max_drawdown', 0):.1%}",
                        'win_rate': f"{backtest['backtest_results'].get('win_rate', 0):.1%}",
                        'trade_count': backtest['backtest_results'].get('total_trades', 0)
                    })
                else:
                    summary['backtest_status'] = '失敗'
                    summary['backtest_error'] = backtest.get('error', '未知錯誤')

                return summary

            except Exception as e:
                logger.warning(f"生成摘要失敗: {e}")
                return {'error': str(e)}

        def _save_workflow_results(self, results: Dict[str, Any]):
            """保存工作流程結果"""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"non_price_ta_workflow_results_{timestamp}.json"
                filepath = os.path.join(os.getcwd(), filename)

                with open(filepath, 'w', encoding='utf - 8') as f:
                    json.dump(results, f, ensure_ascii = False, indent = 2, default = str)

                print(f"\n📁 結果已保存至: {filepath}")

            except Exception as e:
                logger.warning(f"保存結果失敗: {e}")

        def _display_workflow_results(self, results: Dict[str, Any]):
            """顯示工作流程結果"""
            print("\n" + "=" * 80)
            print("📊 非價格數據技術分析工作流程結果摘要")
            print("=" * 80)

            # 基本信息
            workflow_info = results.get('workflow_info', {})
            print(f"⏱️ 執行時間: {workflow_info.get('execution_time', 0):.2f} 秒")
            print(f"📅 執行時間: {workflow_info.get('timestamp', 'N / A')}")
            print(f"🎯 執行狀態: {workflow_info.get('status', 'unknown')}")

            # 數據收集
            data_collection = results.get('data_collection', {})
            print(f"\n📊 數據收集:")
            print(f"   數據源數量: {data_collection.get('sources_count', 0)}")
            print(f"   數據質量: {data_collection.get('data_quality', 'unknown')}")

            # 技術分析
            tech_analysis = results.get('technical_analysis', {})
            print(f"\n🔧 技術分析:")
            print(f"   分析完成數量: {tech_analysis.get('indicators_calculated', 0)}")
            print(f"   指標類型: {', '.join(tech_analysis.get('indicator_types', []))}")

            # 交易信號
            trading_signals = results.get('trading_signals', {})
            signal_dist = trading_signals.get('signal_distribution', {})
            print(f"\n📡 交易信號:")
            print(f"   生成信號數量: {trading_signals.get('signals_generated', 0)}")
            print(f"   信號分佈: BUY({signal_dist.get('BUY', 0)}) SELL({signal_dist.get('SELL', 0)}) HOLD({signal_dist.get('HOLD', 0)})")
            print(f"   平均信心度: {trading_signals.get('avg_confidence', 0):.2%}")

            # 回測結果
            summary = results.get('summary', {})
            print(f"\n📈 回測結果:")
            print(f"   回測狀態: {summary.get('backtest_status', 'unknown')}")

            if summary.get('backtest_status') == '成功':
                print(f"   績效等級: {summary.get('performance_grade', 'N / A')}")
                print(f"   綜合評分: {summary.get('total_score', 0):.1f}/100")
                print(f"   Sharpe比率: {summary.get('sharpe_ratio', 0):.3f}")
                print(f"   總回報: {summary.get('total_return', 'N / A')}")
                print(f"   最大回撤: {summary.get('max_drawdown', 'N / A')}")
                print(f"   勝率: {summary.get('win_rate', 'N / A')}")
                print(f"   交易次數: {summary.get('trade_count', 0)}")

            print("\n" + "=" * 80)


def main():
    """主函數"""
    print("🚀 啟動非價格數據技術分析完整工作流程")
    print("=" * 80)

    # 創建分析器
    analyzer = NonPriceTechnicalAnalyzer()

    # 運行完整工作流程
    results = analyzer.run_complete_workflow()

    # 檢查結果
    if 'error' in results:
        print(f"\n❌ 工作流程失敗: {results['error']}")
        return False
    else:
        print(f"\n✅ 工作流程成功完成!")
        return True


if __name__ == "__main__":
    main()