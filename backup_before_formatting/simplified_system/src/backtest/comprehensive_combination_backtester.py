#!/usr/bin/env python3
"""
全組合回測引擎 - 支持255種數據組合
Comprehensive Combination Backtest Engine - Support 255 Data Combinations

實現您要求的功能：
- 回測庭全部組合 (255種)
- 不要HOLD信號，只要買賣
- 搵高Sharpe Ratio
"""

import pandas as pd
import numpy as np
import itertools
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveCombinationBacktester:
    """全組合回測引擎"""

    def __init__(self):
        self.risk_free_rate = 0.03  # 3%無風險利率
        self.combinations_cache = {}
        self.results_cache = {}

        # 數據源定義
        self.data_sources = [
            'stock_price',      # 股價數據 (必需)
            'hibor_rates',      # HIBOR利率
            'monetary_base',   # 貨幣基礎
            'exchange_rates',   # 匯率數據
            'efbn_yield',       # 外匯基金收益率
            'discount_window',  # 貼現窗利率
            'market_operation', # 市場操作
            'institutional_bond', # 機構債券
            'forward_exchange'  # 遠期匯率
        ]

        logger.info(f"初始化全組合回測引擎，支持 {len(self.data_sources)} 個數據源")

    def generate_all_combinations(self) -> List[Set[str]]:
        """生成所有可能的數據組合 (2^9 - 1 = 511種組合)"""
        try:
            # 必須包含股價數據
            essential_sources = ['stock_price']
            optional_sources = [src for src in self.data_sources if src != 'stock_price']

            combinations = []

            # 生成所有可能的組合
            for r in range(1, len(optional_sources) + 1):
                for combo in itertools.combinations(optional_sources, r):
                    # 每個組合必須包含股價數據
                    full_combination = set(['stock_price']) | set(combo)
                    combinations.append(full_combination)

            logger.info(f"生成 {len(combinations)} 種數據組合")
            return combinations

        except Exception as e:
            logger.error(f"生成組合失敗: {e}")
            return []

    def calculate_portfolio_signals(self, combination: Set[str],
                                     stock_data: pd.DataFrame,
                                     gov_indicators: Dict[str, Dict[str, float]]) -> pd.Series:
        """計算組合的信號 (純買賣，無HOLD)"""
        try:
            signals = pd.Series(0, index=stock_data.index)
            current_positions = 0
            scores = []

            # 股價基礎信號 (使用技術指標)
            stock_signals = self.calculate_stock_signals(stock_data)

            # 政府數據信號加權
            gov_weight = 0.4  # 政府數據權重
            stock_weight = 0.6  # 股價數據權重

            for i, (date, idx) in enumerate(zip(stock_data.index, range(len(stock_data)))):
                stock_score = stock_signals[idx]  # -1, 0, 1

                # 政府數據綜合評分
                gov_score = self.calculate_government_combination_score(
                    combination, gov_indicators, date
                )

                # 加權綜合評分
                combined_score = (stock_weight * stock_score + gov_weight * gov_score)
                scores.append(combined_score)

                # 生成買賣信號 (強制決策，無HOLD)
                if combined_score > 0.2:  # 買進閾值
                    signal = 1  # 買入
                elif combined_score < -0.2:  # 賣出閾值
                    signal = -1  # 賣出
                else:
                    # 中性區間強制決策
                    signal = 1 if combined_score >= 0 else -1

                signals.iloc[idx] = signal

            return signals, scores

        except Exception as e:
            logger.error(f"計算組合信號失敗: {e}")
            return pd.Series(0, index=stock_data.index), []

    def calculate_stock_signals(self, stock_data: pd.DataFrame) -> pd.Series:
        """計算基礎股價技術指標信號"""
        try:
            if stock_data.empty:
                return pd.Series(0)

            prices = stock_data['close']

            # RSI信號
            rsi = self.calculate_rsi(prices, 14)
            rsi_signal = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))

            # MACD信號
            macd_data = self.calculate_macd(prices, 12, 26, 9)
            if macd_data and 'macd' in macd_data and 'signal' in macd_data:
                macd_signal = np.where(
                    macd_data['macd'] > macd_data['signal'], 1,
                    np.where(macd_data['macd'] < macd_data['signal'], -1, 0)
                )
            else:
                macd_signal = np.zeros(len(prices))

            # 均線信號
            ma_short = prices.rolling(window=20).mean()
            ma_long = prices.rolling(window=50).mean()
            ma_signal = np.where(ma_short > ma_long, 1, -1)

            # 綜合信號
            combined_signal = rsi_signal + macd_signal + ma_signal
            return pd.Series(combined_signal, index=stock_data.index)

        except Exception as e:
            logger.error(f"計算股價信號失敗: {e}")
            return pd.Series(0, index=stock_data.index)

    def calculate_government_combination_score(self, combination: Set[str],
                                                  gov_indicators: Dict[str, Dict[str, float]],
                                                  date: datetime) -> float:
        """計算政府數據組合的綜合評分"""
        try:
            score = 0.0
            active_indicators = 0

            # HIBOR信號
            if 'hibor_rates' in combination and 'hibor' in gov_indicators:
                hibor_ind = gov_indicators['hibor']

                # 低利率看好股市
                if 'hibor_rsi' in hibor_ind:
                    if hibor_ind['hibor_rsi'] < 30:  # 利率超賣
                        score += 2
                    elif hibor_ind['hibor_rsi'] > 70:  # 利率超買
                        score -= 2

                if 'hibor_trend' in hibor_ind:
                    if hibor_ind['hibor_trend'] < 0:  # 利率下降
                        score += 1
                    else:  # 利率上升
                        score -= 1

                active_indicators += 1

            # 貨幣供應信號
            if 'monetary_base' in combination and 'monetary' in gov_indicators:
                monetary_ind = gov_indicators['monetary']

                # 貨幣增長利好股市
                if 'monetary_growth' in monetary_ind:
                    score += monetary_ind['monetary_growth'] * 0.5

                active_indicators += 1

            # 匯率信號
            if 'exchange_rates' in combination and 'exchange' in gov_indicators:
                exchange_ind = gov_indicators['exchange']

                # 港元貶值利好港股
                if 'exchange_trend' in exchange_ind:
                    if exchange_ind['exchange_trend'] < 0:  # 港元貶值
                        score += 1
                    else:  # 港元升值
                        score -= 1

                active_indicators += 1

            # EFBN收益率信號
            if 'efbn_yield' in combination and 'efbn' in gov_indicators:
                efbn_ind = gov_indicators['efbn']

                # 收益率下降利好股市
                if 'efbn_yield_trend' in efbn_ind:
                    if efbn_ind['efbn_yield_trend'] < 0:
                        score += 1
                    else:
                        score -= 1

                active_indicators += 1

            # 正規化評分
            if active_indicators > 0:
                score = score / active_indicators

            return score

        except Exception as e:
            logger.error(f"計算政府數據評分失敗: {e}")
            return 0.0

    def backtest_combination(self, combination: Set[str],
                           stock_data: pd.DataFrame,
                           gov_indicators: Dict[str, Dict[str, float]],
                           combination_id: str) -> Dict[str, Any]:
        """回測單個組合"""
        try:
            # 計算信號
            signals, scores = self.calculate_portfolio_signals(combination, stock_data, gov_indicators)

            # 計算回報
            returns = stock_data['close'].pct_change().shift(-1)  # 次日回報
            strategy_returns = signals.shift(1) * returns

            # 移除最後一個NaN
            strategy_returns = strategy_returns.dropna()

            if len(strategy_returns) == 0:
                return {
                    'combination_id': combination_id,
                    'combination': list(combination),
                    'error': 'No valid returns calculated',
                    'total_return': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'win_rate': 0,
                    'total_trades': 0
                }

            # 計算性能指標
            total_return = (1 + strategy_returns).cumprod().iloc[-1] - 1

            # Sharpe Ratio (年化)
            excess_returns = strategy_returns - self.risk_free_rate / 252
            if excess_returns.std() > 0:
                sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative = (1 + strategy_returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 勝率和交易次數
            win_rate = (strategy_returns > 0).mean()
            total_trades = (signals.diff() != 0).sum()

            # 計算平均評分
            avg_score = np.mean(scores) if scores else 0

            result = {
                'combination_id': combination_id,
                'combination': list(combination),
                'total_return': total_return,
                'annual_return': total_return * 252 / len(strategy_returns),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': int(total_trades),
                'avg_signal_score': avg_score,
                'signal_volatility': np.std(scores) if scores else 0,
                'returns_volatility': strategy_returns.std(),
                'data_points': len(strategy_returns)
            }

            return result

        except Exception as e:
            logger.error(f"回測組合 {combination_id} 失敗: {e}")
            return {
                'combination_id': combination_id,
                'combination': list(combination),
                'error': str(e),
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'total_trades': 0
            }

    def run_comprehensive_backtest(self, stock_data: pd.DataFrame,
                                    gov_indicators: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """運行全組合回測"""
        try:
            logger.info("開始全組合回測...")
            start_time = time.time()

            # 生成所有組合
            combinations = self.generate_all_combinations()

            # 限制組合數量以避免性能問題
            max_combinations = min(255, len(combinations))
            combinations = combinations[:max_combinations]

            logger.info(f"將測試 {len(combinations)} 種組合")

            # 並行回測
            results = []
            with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
                futures = []

                for i, combination in enumerate(combinations):
                    combination_id = f"combo_{i+1:03d}"
                    future = executor.submit(
                        self.backtest_combination,
                        combination,
                        stock_data,
                        gov_indicators,
                        combination_id
                    )
                    futures.append(future)

                # 收集結果
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"回測任務失敗: {e}")

            # 分析結果
            analysis = self.analyze_results(results)

            # 排序並選擇最佳策略
            valid_results = [r for r in results if 'error' not in r]

            if valid_results:
                # 按Sharpe Ratio排序
                best_by_sharpe = sorted(valid_results, key=lambda x: x['sharpe_ratio'], reverse=True)
                best_by_return = sorted(valid_results, key=lambda x: x['total_return'], reverse=True)

                analysis['best_by_sharpe'] = best_by_sharpe[0]
                analysis['best_by_return'] = best_by_return[0]
                analysis['top_10_strategies'] = best_by_sharpe[:10]

            execution_time = time.time() - start_time

            final_result = {
                'execution_time': execution_time,
                'total_combinations': len(combinations),
                'successful_combinations': len(valid_results),
                'results': results,
                'analysis': analysis
            }

            logger.info(f"回測完成! 總耗時: {execution_time:.2f}秒")
            logger.info(f"成功率: {len(valid_results)}/{len(combinations)} = {len(valid_results)/len(combinations)*100:.1f}%")

            return final_result

        except Exception as e:
            logger.error(f"全組合回測失敗: {e}")
            return {'error': str(e), 'execution_time': 0}

    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析回測結果"""
        try:
            if not results:
                return {'error': 'No results to analyze'}

            # 基礎統計
            valid_results = [r for r in results if 'error' not in r]

            if not valid_results:
                return {'error': 'No valid results'}

            sharpe_ratios = [r['sharpe_ratio'] for r in valid_results]
            total_returns = [r['total_return'] for r in valid_results]
            max_drawdowns = [r['max_drawdown'] for r in valid_results]

            analysis = {
                'sharpe_ratio_stats': {
                    'mean': np.mean(sharpe_ratios),
                    'std': np.std(sharpe_ratios),
                    'min': np.min(sharpe_ratios),
                    'max': np.max(sharpe_ratios),
                    'median': np.median(sharpe_ratios)
                },
                'total_return_stats': {
                    'mean': np.mean(total_returns),
                    'std': np.std(total_returns),
                    'min': np.min(total_returns),
                    'max': np.max(total_returns),
                    'median': np.median(total_returns)
                },
                'risk_stats': {
                    'max_drawdown_mean': np.mean(np.abs(max_drawdowns)),
                    'max_drawdown_max': np.max(np.abs(max_drawdowns)),
                    'max_drawdown_median': np.median(np.abs(max_drawdowns))
                },
                'high_sharpe_strategies': [r for r in valid_results if r['sharpe_ratio'] > 1.0],
                'profitable_strategies': [r for r in valid_results if r['total_return'] > 0],
                'low_drawdown_strategies': [r for r in valid_results if np.abs(r['max_drawdown']) < 0.1]
            }

            # 計算高質量策略指標
            analysis['quality_metrics'] = {
                'sharpe_above_1': len(analysis['high_sharpe_strategies']),
                'sharpe_above_2': len([r for r in valid_results if r['sharpe_ratio'] > 2.0]),
                'return_above_10pct': len([r for r in valid_results if r['total_return'] > 0.10]),
                'drawdown_below_5pct': len([r for r in valid_results if np.abs(r['max_drawdown']) < 0.05]),
                'win_rate_above_60pct': len([r for r in valid_results if r['win_rate'] > 0.60])
            }

            return analysis

        except Exception as e:
            logger.error(f"結果分析失敗: {e}")
            return {'error': str(e)}

    # ============ 輔助方法 ============

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, pd.Series]]:
        """計算MACD"""
        try:
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal).mean()

            return {
                'macd': macd,
                'signal': signal_line,
                'histogram': macd - signal_line
            }
        except:
            return None

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存回測結果"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"comprehensive_backtest_results_{timestamp}.json"

            filepath = f"optimization_results/{filename}"

            # 確保目錄存在
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"結果已保存至: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存結果失敗: {e}")
            return ""

if __name__ == "__main__":
    # 測試代碼
    backtester = ComprehensiveCombinationBacktester()

    print("全組合回測引擎初始化完成")
    print(f"支持數據源: {len(backtester.data_sources)}")

    # 生成組合示例
    combinations = backtester.generate_all_combinations()
    print(f"可生成組合數量: {len(combinations)}")

    # 顯示前5個組合
    print("\n前5個組合示例:")
    for i, combo in enumerate(combinations[:5]):
        print(f"{i+1}. {sorted(combo)}")