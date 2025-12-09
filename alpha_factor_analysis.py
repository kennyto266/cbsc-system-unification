#!/usr/bin/env python3
"""
Simplified System - Alpha Factor Analysis Engine
專業級Alpha因子分析和可視化工具

功能特性:
1. 全面Alpha因子計算和評估
2. 因子相關性分析和去相關
3. 因子組合優化
4. 因子有效性回測
5. 多因子模型構建

Author: Claude Code Assistant
Date: 2025-11-27
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import warnings

# 統計和機器學習
from scipy import stats
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score

# 可視化
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# 技術指標
import talib

warnings.filterwarnings('ignore')

@dataclass
class FactorConfig:
    """因子配置"""
    # 數據配置
    lookback_period: int = 252  # 1年
    min_periods: int = 60  # 最小數據期數
    forward_period: int = 5  # 預測未來期數

    # 因子類型
    include_technical: bool = True
    include_fundamental: bool = False
    include_macro: bool = True
    include_sentiment: bool = False

    # 因子篩選
    min_ic: float = 0.02  # 最小信息係數
    max_correlation: float = 0.7  # 最大因子間相關性
    top_n_factors: int = 20  # 選取前N個因子

    # 模型配置
    test_size: float = 0.2
    cv_folds: int = 5
    random_state: int = 42

@dataclass
class FactorPerformance:
    """因子性能指標"""
    name: str
    ic_mean: float
    ic_std: float
    ic_ir: float  # 信息比率 = IC_mean / IC_std
    rank_ic_mean: float
    rank_ic_std: float
    turnover: float  # 換手率
    coverage: float  # 覆蓋率
    hit_rate: float  # 勝率

    # 分組表現
    long_short_return: float
    long_short_sharpe: float
    top_decile_return: float
    bottom_decile_return: float

    # 統計檢驗
    t_stat: float
    p_value: float
    is_significant: bool

class AlphaFactorAnalyzer:
    """
    Alpha因子分析引擎

    提供專業級的因子計算、評估、優化和組合功能
    """

    def __init__(self, config: Optional[FactorConfig] = None):
        self.config = config or FactorConfig()
        self.factor_data = {}
        self.factor_performance = {}
        self.factor_returns = {}
        self.scaler = StandardScaler()
        self.robust_scaler = RobustScaler()

        print(f"Alpha Factor Analyzer initialized with lookback period: {self.config.lookback_period} days")

    def calculate_technical_factors(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算技術類因子

        Args:
            data: 股票數據DataFrame (OHLCV)

        Returns:
            技術因子字典
        """
        factors = {}

        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data['volume'].values

            # 動量因子
            for period in [5, 10, 20, 60, 120]:
                factors[f'momentum_{period}'] = data['close'].pct_change(period)

            # 反轉因子
            for period in [5, 10, 20]:
                factors[f'reversal_{period}'] = -data['close'].pct_change(period)

            # 波動率因子
            for period in [10, 20, 60]:
                factors[f'volatility_{period}'] = data['close'].pct_change().rolling(period).std()

            # 趨勢因子
            for period in [10, 20, 60]:
                factors[f'trend_{period}'] = (data['close'] / data['close'].rolling(period).mean() - 1)

            # RSI因子
            factors['rsi_14'] = talib.RSI(close, timeperiod=14) / 100.0
            factors['rsi_30'] = talib.RSI(close, timeperiod=30) / 100.0

            # MACD因子
            macd, macd_signal, macd_hist = talib.MACD(close)
            factors['macd_signal'] = macd_signal
            factors['macd_hist'] = macd_hist

            # 布林帶因子
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            factors['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            factors['bb_width'] = (bb_upper - bb_lower) / bb_middle

            # 隨機指標因子
            slowk, slowd = talib.STOCH(high, low, close)
            factors['stoch_k'] = slowk / 100.0
            factors['stoch_d'] = slowd / 100.0

            # 威廉指标因子
            factors['williams_r'] = talib.WILLR(high, low, close) / -100.0

            # CCI因子
            factors['cci'] = talib.CCI(high, low, close) / 100.0

            # 均線因子
            for period in [5, 10, 20, 60]:
                ma = talib.MA(close, timeperiod=period)
                factors[f'ma_ratio_{period}'] = close / ma

            # 價格位置因子
            for period in [20, 60, 120]:
                factors[f'price_position_{period}'] = (close - data['close'].rolling(period).min()) / (data['close'].rolling(period).max() - data['close'].rolling(period).min())

            # 成交量因子
            volume_ma = talib.MA(volume, timeperiod=20)
            factors['volume_ratio'] = volume / volume_ma
            factors['volume_price_trend'] = talib.AD(high, low, close, volume)

            # 價量結合因子
            factors['vwap'] = (data['close'] * volume).rolling(20).sum() / volume.rolling(20).sum()
            factors[f'price_to_vwap'] = close / factors['vwap']

            # ATR因子
            atr = talib.ATR(high, low, close, timeperiod=14)
            factors[f'atr_ratio'] = atr / close

            # ADX因子
            factors['adx'] = talib.ADX(high, low, close) / 100.0

            print(f"Calculated {len(factors)} technical factors")
            return factors

        except Exception as e:
            print(f"Error calculating technical factors: {e}")
            return {}

    def calculate_macro_factors(self, data: pd.DataFrame, macro_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """
        計算宏觀經濟因子

        Args:
            data: 股票數據
            macro_data: 宏觀數據字典

        Returns:
            宏觀因子字典
        """
        factors = {}

        try:
            # HIBOR利率因子
            if 'hibor' in macro_data:
                hibor_data = macro_data['hibor']
                # 重新採樣到股票數據頻率
                hibor_aligned = hibor_data.reindex(data.index, method='ffill')
                factors['hibor_effect'] = -hibor_aligned['overnight']  # 負相關假設

            # 貨幣基礎因子
            if 'monetary_base' in macro_data:
                mb_data = macro_data['monetary_base']
                mb_aligned = mb_data.reindex(data.index, method='ffill')
                factors['monetary_base_effect'] = mb_aligned['total'].pct_change(20)

            # 匯率因子
            if 'exchange_rates' in macro_data:
                fx_data = macro_data['exchange_rates']
                fx_aligned = fx_data.reindex(data.index, method='ffill')
                factors['usd_hkd_effect'] = fx_data['usd_hkd'].pct_change(5)

            print(f"Calculated {len(factors)} macro factors")
            return factors

        except Exception as e:
            print(f"Error calculating macro factors: {e}")
            return {}

    def calculate_all_factors(self, stock_data: Dict[str, pd.DataFrame],
                            macro_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Dict[str, pd.Series]]:
        """
        計算所有股票的所有因子

        Args:
            stock_data: 股票數據字典 {symbol: DataFrame}
            macro_data: 宏觀數據字典

        Returns:
            因子數據字典 {symbol: {factor_name: Series}}
        """
        all_factors = {}

        for symbol, data in stock_data.items():
            print(f"Calculating factors for {symbol}...")
            symbol_factors = {}

            # 技術因子
            if self.config.include_technical:
                tech_factors = self.calculate_technical_factors(data)
                symbol_factors.update(tech_factors)

            # 宏觀因子
            if self.config.include_macro and macro_data:
                macro_factors = self.calculate_macro_factors(data, macro_data)
                symbol_factors.update(macro_factors)

            # 清理無效值
            for name, factor in symbol_factors.items():
                symbol_factors[name] = factor.replace([np.inf, -np.inf], np.nan)

            all_factors[symbol] = symbol_factors
            print(f"Generated {len(symbol_factors)} factors for {symbol}")

        self.factor_data = all_factors
        return all_factors

    def evaluate_factor_performance(self, factor_data: Dict[str, pd.Series],
                                  returns: pd.Series) -> FactorPerformance:
        """
        評估單個因子的性能

        Args:
            factor_data: 因子數據
            returns: 未來收益率

        Returns:
            因子性能指標
        """
        try:
            # 對齊數據
            aligned_data = pd.concat([factor_data, returns], axis=1, join='inner')
            aligned_data.columns = ['factor', 'returns']
            aligned_data = aligned_data.dropna()

            if len(aligned_data) < self.config.min_periods:
                return None

            factor_values = aligned_data['factor']
            future_returns = aligned_data['returns']

            # 計算信息係數 (IC)
            ic = factor_values.corr(future_returns, method='pearson')
            rank_ic = factor_values.corr(future_returns, method='spearman')

            # 時序滾動IC
            rolling_ic = factor_values.rolling(60).corr(future_returns)
            ic_mean = rolling_ic.mean()
            ic_std = rolling_ic.std()
            ic_ir = ic_mean / ic_std if ic_std > 0 else 0

            # 分組回測
            factor_quantiles = pd.qcut(factor_values, 10, labels=False, duplicates='drop')
            group_returns = future_returns.groupby(factor_quantiles).mean()

            # 多空組合表現
            long_short_return = group_returns.iloc[-1] - group_returns.iloc[0]
            long_short_sharpe = long_short_return / (group_returns.std() * np.sqrt(252))

            # 勝率
            hit_rate = (long_short_return > 0).mean() if hasattr(long_short_return, '__iter__') else (long_short_return > 0) * 1.0

            # 換手率
            factor_quantiles_shifted = factor_quantiles.shift(1)
            turnover = (factor_quantiles != factor_quantiles_shifted).mean()

            # 覆蓋率
            coverage = len(aligned_data) / len(factor_values)

            # 統計檢驗
            t_stat, p_value = stats.ttest_1samp(rolling_ic.dropna(), 0)

            performance = FactorPerformance(
                name=factor_data.name or 'Unknown',
                ic_mean=ic_mean,
                ic_std=ic_std,
                ic_ir=ic_ir,
                rank_ic_mean=rank_ic,
                rank_ic_std=rank_ic.rolling(60).std().mean(),
                turnover=turnover,
                coverage=coverage,
                hit_rate=hit_rate if isinstance(hit_rate, float) else hit_rate.mean(),
                long_short_return=long_short_return,
                long_short_sharpe=long_short_sharpe,
                top_decile_return=group_returns.iloc[-1] if len(group_returns) > 0 else 0,
                bottom_decile_return=group_returns.iloc[0] if len(group_returns) > 0 else 0,
                t_stat=t_stat,
                p_value=p_value,
                is_significant=p_value < 0.05
            )

            return performance

        except Exception as e:
            print(f"Error evaluating factor performance: {e}")
            return None

    def evaluate_all_factors(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, FactorPerformance]:
        """
        評估所有因子的性能

        Args:
            stock_data: 股票數據字典

        Returns:
            因子性能字典
        """
        all_performance = {}

        for symbol, data in stock_data.items():
            if symbol not in self.factor_data:
                continue

            # 計算未來收益率
            future_returns = data['close'].pct_change(self.config.forward_period).shift(-self.config.forward_period)

            symbol_performance = {}
            for factor_name, factor_values in self.factor_data[symbol].items():
                factor_values.name = factor_name
                performance = self.evaluate_factor_performance(factor_values, future_returns)
                if performance:
                    symbol_performance[factor_name] = performance

            all_performance[symbol] = symbol_performance
            print(f"Evaluated {len(symbol_performance)} factors for {symbol}")

        self.factor_performance = all_performance
        return all_performance

    def get_top_factors(self, symbol: Optional[str] = None, top_n: Optional[int] = None) -> List[Tuple[str, FactorPerformance]]:
        """
        獲取頂級因子

        Args:
            symbol: 股票代碼 (None表示所有股票)
            top_n: 返回前N個因子

        Returns:
            排序後的因子列表 [(symbol_factor_name, performance), ...]
        """
        if top_n is None:
            top_n = self.config.top_n_factors

        all_factors = []

        if symbol and symbol in self.factor_performance:
            # 單個股票的因子
            for factor_name, performance in self.factor_performance[symbol].items():
                if performance.ic_mean >= self.config.min_ic:
                    all_factors.append((f"{symbol}_{factor_name}", performance))
        else:
            # 所有股票的因子
            for sym, factors in self.factor_performance.items():
                for factor_name, performance in factors.items():
                    if performance.ic_mean >= self.config.min_ic:
                        all_factors.append((f"{sym}_{factor_name}", performance))

        # 按信息比率排序
        all_factors.sort(key=lambda x: x[1].ic_ir, reverse=True)

        return all_factors[:top_n]

    def analyze_factor_correlation(self, symbol: str) -> pd.DataFrame:
        """
        分析因子相關性

        Args:
            symbol: 股票代碼

        Returns:
            因子相關性矩陣
        """
        if symbol not in self.factor_data:
            raise ValueError(f"No factor data for {symbol}")

        factor_df = pd.DataFrame(self.factor_data[symbol])
        correlation_matrix = factor_df.corr()

        return correlation_matrix

    def select_uncorrelated_factors(self, symbol: str, top_factors: List[str], max_correlation: float = None) -> List[str]:
        """
        選擇低相關性因子

        Args:
            symbol: 股票代碼
            top_factors: 頂級因子列表
            max_correlation: 最大相關性閾值

        Returns:
            選中的因子列表
        """
        if max_correlation is None:
            max_correlation = self.config.max_correlation

        if symbol not in self.factor_data:
            return []

        selected_factors = []
        factor_df = pd.DataFrame(self.factor_data[symbol])

        for factor in top_factors:
            if factor not in factor_df.columns:
                continue

            # 檢查與已選因子的相關性
            add_factor = True
            for selected in selected_factors:
                if selected in factor_df.columns:
                    correlation = abs(factor_df[factor].corr(factor_df[selected]))
                    if correlation > max_correlation:
                        add_factor = False
                        break

            if add_factor:
                selected_factors.append(factor)

        return selected_factors

    def build_multifactor_model(self, symbol: str, selected_factors: List[str]) -> Dict[str, Any]:
        """
        構建多因子模型

        Args:
            symbol: 股票代碼
            selected_factors: 選中的因子列表

        Returns:
            模型結果字典
        """
        if symbol not in self.factor_data or symbol not in stock_data:
            raise ValueError(f"No data for {symbol}")

        # 準備數據
        factor_df = pd.DataFrame({f: self.factor_data[symbol][f] for f in selected_factors})
        returns = stock_data[symbol]['close'].pct_change(self.config.forward_period).shift(-self.config.forward_period)

        # 對齊數據
        model_data = pd.concat([factor_df, returns], axis=1, join='inner').dropna()
        X = model_data.iloc[:, :-1]
        y = model_data.iloc[:, -1]

        if len(X) < self.config.min_periods:
            return {}

        # 標準化因子
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            index=X.index,
            columns=X.columns
        )

        # 時間序列交叉驗證
        tscv = TimeSeriesSplit(n_splits=self.config.cv_folds)
        cv_scores = []

        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled.iloc[train_idx], X_scaled.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            # 訓練隨機森林模型
            rf = RandomForestRegressor(n_estimators=100, random_state=self.config.random_state)
            rf.fit(X_train, y_train)
            y_pred = rf.predict(X_val)

            score = r2_score(y_val, y_pred)
            cv_scores.append(score)

        # 訓練最終模型
        final_model = RandomForestRegressor(n_estimators=100, random_state=self.config.random_state)
        final_model.fit(X_scaled, y)

        # 因子重要性
        feature_importance = pd.Series(final_model.feature_importances_, index=selected_factors)
        feature_importance = feature_importance.sort_values(ascending=False)

        # 預測結果
        y_pred_all = final_model.predict(X_scaled)

        return {
            'model': final_model,
            'cv_scores': cv_scores,
            'cv_mean': np.mean(cv_scores),
            'cv_std': np.std(cv_scores),
            'feature_importance': feature_importance,
            'predictions': y_pred_all,
            'actual': y.values,
            'r2_score': r2_score(y, y_pred_all),
            'mse': mean_squared_error(y, y_pred_all)
        }

    def create_factor_analysis_report(self, symbol: str) -> Dict[str, Any]:
        """
        創建完整的因子分析報告

        Args:
            symbol: 股票代碼

        Returns:
            分析報告字典
        """
        if symbol not in self.factor_performance:
            return {}

        report = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'total_factors': len(self.factor_performance[symbol]),
            'significant_factors': sum(1 for p in self.factor_performance[symbol].values() if p.is_significant)
        }

        # 頂級因子
        top_factors = self.get_top_factors(symbol)
        report['top_factors'] = [
            {
                'name': name,
                'ic_mean': perf.ic_mean,
                'ic_ir': perf.ic_ir,
                'hit_rate': perf.hit_rate,
                'sharpe_ratio': perf.long_short_sharpe
            }
            for name, perf in top_factors[:10]
        ]

        # 因子相關性分析
        correlation_matrix = self.analyze_factor_correlation(symbol)
        high_correlation_pairs = []

        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_val = correlation_matrix.iloc[i, j]
                if abs(corr_val) > self.config.max_correlation:
                    high_correlation_pairs.append({
                        'factor1': correlation_matrix.columns[i],
                        'factor2': correlation_matrix.columns[j],
                        'correlation': corr_val
                    })

        report['high_correlation_pairs'] = high_correlation_pairs

        # 選擇低相關性因子
        factor_names = [f.split('_', 1)[-1] for f, _ in top_factors[:20]]
        selected_factors = self.select_uncorrelated_factors(symbol, factor_names)
        report['selected_factors'] = selected_factors

        # 多因子模型 (如果有足夠的因子)
        if len(selected_factors) >= 3:
            try:
                model_results = self.build_multifactor_model(symbol, selected_factors)
                report['multifactor_model'] = {
                    'cv_score_mean': model_results['cv_mean'],
                    'cv_score_std': model_results['cv_std'],
                    'r2_score': model_results['r2_score'],
                    'top_features': model_results['feature_importance'].head(5).to_dict()
                }
            except Exception as e:
                report['multifactor_model'] = {'error': str(e)}

        return report

    def visualize_factor_performance(self, symbol: str, factor_name: str, save_path: Optional[str] = None):
        """
        可視化因子性能

        Args:
            symbol: 股票代碼
            factor_name: 因子名稱
            save_path: 保存路徑
        """
        if symbol not in self.factor_data or factor_name not in self.factor_data[symbol]:
            print(f"Factor {factor_name} not found for {symbol}")
            return

        factor_values = self.factor_data[symbol][factor_name]
        returns = stock_data[symbol]['close'].pct_change(self.config.forward_period).shift(-self.config.forward_period)

        # 對齊數據
        aligned_data = pd.concat([factor_values, returns], axis=1, join='inner').dropna()
        aligned_data.columns = ['factor', 'returns']

        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Factor Values Over Time',
                'IC Rolling Correlation',
                'Factor Decile Returns',
                'Factor Distribution'
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        # 因子值時間序列
        fig.add_trace(
            go.Scatter(x=aligned_data.index, y=aligned_data['factor'], name='Factor Value'),
            row=1, col=1
        )

        # 滾動IC
        rolling_ic = aligned_data['factor'].rolling(60).corr(aligned_data['returns'])
        fig.add_trace(
            go.Scatter(x=rolling_ic.index, y=rolling_ic, name='Rolling IC'),
            row=1, col=2
        )

        # 分組回報
        factor_quantiles = pd.qcut(aligned_data['factor'], 10, labels=False, duplicates='drop')
        decile_returns = aligned_data['returns'].groupby(factor_quantiles).mean()
        fig.add_trace(
            go.Bar(x=decile_returns.index, y=decile_returns, name='Decile Returns'),
            row=2, col=1
        )

        # 因子分佈
        fig.add_trace(
            go.Histogram(x=aligned_data['factor'], name='Factor Distribution', nbinsx=50),
            row=2, col=2
        )

        fig.update_layout(
            title=f'Factor Analysis: {symbol} - {factor_name}',
            showlegend=False,
            height=800
        )

        if save_path:
            fig.write_html(save_path)

        fig.show()

    def export_factor_data(self, symbols: List[str], output_path: str):
        """
        導出因子數據

        Args:
            symbols: 股票代碼列表
            output_path: 輸出路徑
        """
        export_data = {}

        for symbol in symbols:
            if symbol in self.factor_data:
                symbol_data = {}
                for factor_name, factor_series in self.factor_data[symbol].items():
                    symbol_data[factor_name] = factor_series.to_dict()

                export_data[symbol] = symbol_data

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        print(f"Factor data exported to {output_path}")

# 示例使用
if __name__ == "__main__":
    # 創建分析器
    analyzer = AlphaFactorAnalyzer()

    # 模擬數據 (在實際使用中，這裡應該是真實數據)
    dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # 模擬股票數據
    symbol_data = {}
    symbols = ['0700.HK', '0941.HK', '1398.HK']

    global stock_data
    stock_data = {}

    for symbol in symbols:
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.02)
        volumes = np.random.randint(1000000, 5000000, len(dates))

        df = pd.DataFrame({
            'close': prices,
            'high': prices * (1 + np.random.rand(len(dates)) * 0.02),
            'low': prices * (1 - np.random.rand(len(dates)) * 0.02),
            'open': prices * (1 + (np.random.rand(len(dates)) - 0.5) * 0.01),
            'volume': volumes
        }, index=dates)

        stock_data[symbol] = df

    # 計算因子
    all_factors = analyzer.calculate_all_factors(stock_data)
    print(f"Calculated factors for {len(all_factors)} symbols")

    # 評估因子性能
    all_performance = analyzer.evaluate_all_factors(stock_data)
    print(f"Evaluated factors for {len(all_performance)} symbols")

    # 獲取頂級因子
    top_factors = analyzer.get_top_factors(top_n=10)
    print("\nTop 10 Factors:")
    for i, (name, perf) in enumerate(top_factors, 1):
        print(f"{i}. {name}: IC={perf.ic_mean:.3f}, IR={perf.ic_ir:.3f}, Sharpe={perf.long_short_sharpe:.3f}")

    # 生成報告
    for symbol in symbols:
        report = analyzer.create_factor_analysis_report(symbol)
        print(f"\n{symbol} Analysis Report:")
        print(f"Total factors: {report['total_factors']}")
        print(f"Significant factors: {report['significant_factors']}")

        if 'multifactor_model' in report:
            model_info = report['multifactor_model']
            if 'r2_score' in model_info:
                print(f"Multifactor model R²: {model_info['r2_score']:.3f}")
                print(f"CV score: {model_info['cv_score_mean']:.3f} ± {model_info['cv_score_std']:.3f}")

    print("\nAlpha factor analysis completed!")