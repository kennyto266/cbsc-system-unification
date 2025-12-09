#!/usr/bin/env python3
"""
Multi-Asset Portfolio Engine
多資產投資組合引擎

Professional portfolio optimization and backtesting for multiple assets
專業多資產投資組合優化和回測
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")

logger = logging.getLogger(__name__)

@dataclass
class PortfolioConfig:
    """投資組合配置"""
    # 基本配置
    initial_cash: float = 1000000.0  # 100萬初始資金
    fees: float = 0.001  # 0.1%手續費
    slippage: float = 0.0005  # 0.05%滑點
    freq: str = '1D'  # 日頻率

    # 資產配置
    max_positions: int = 10  # 最大持倉數量
    min_position_weight: float = 0.05  # 最小倉位權重 (5%)
    max_position_weight: float = 0.30  # 最大倉位權重 (30%)
    rebalance_freq: Optional[str] = None  # 重平衡頻率

    # 風險管理
    stop_loss: Optional[float] = None  # 止損百分比
    take_profit: Optional[float] = None  # 止盈百分比
    max_portfolio_risk: float = 0.20  # 最大投資組合風險

    # 優化配置
    enable_parallel: bool = True
    max_workers: int = 4
    optimization_metric: str = 'sharpe_ratio'

@dataclass
class PortfolioResult:
    """投資組合結果"""
    assets: List[str]
    weights: Dict[str, float]
    strategy: str

    # 投資組合級別指標
    portfolio_return: float
    portfolio_sharpe: float
    portfolio_volatility: float
    portfolio_max_drawdown: float
    portfolio_calmar: float
    portfolio_sortino: float

    # 個別資產指標
    individual_returns: Dict[str, float]
    individual_sharpes: Dict[str, float]
    individual_volatilities: Dict[str, float]

    # 風險指標
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    expected_shortfall: float
    beta: float
    alpha: float
    information_ratio: float

    # 交易統計
    total_trades: int
    win_rate: float
    profit_factor: float

    # 元數據
    start_date: str
    end_date: str
    execution_time: float

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'portfolio_info': {
                'assets': self.assets,
                'weights': self.weights,
                'strategy': self.strategy
            },
            'performance': {
                'portfolio_return': round(self.portfolio_return * 100, 2),
                'sharpe_ratio': round(self.portfolio_sharpe, 3),
                'volatility': round(self.portfolio_volatility * 100, 2),
                'max_drawdown': round(self.portfolio_max_drawdown * 100, 2),
                'calmar_ratio': round(self.portfolio_calmar, 3),
                'sortino_ratio': round(self.portfolio_sortino, 3),
                'var_95': round(self.var_95 * 100, 2),
                'var_99': round(self.var_99 * 100, 2),
                'expected_shortfall': round(self.expected_shortfall * 100, 2),
                'beta': round(self.beta, 3),
                'alpha': round(self.alpha * 100, 2),
                'information_ratio': round(self.information_ratio, 3),
                'total_trades': self.total_trades,
                'win_rate': round(self.win_rate * 100, 2),
                'profit_factor': round(self.profit_factor, 2)
            },
            'individual_performance': {
                asset: {
                    'return': round(self.individual_returns[asset] * 100, 2),
                    'sharpe': round(self.individual_sharpes[asset], 3),
                    'volatility': round(self.individual_volatilities[asset] * 100, 2)
                }
                for asset in self.assets
            },
            'metadata': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'execution_time': round(self.execution_time, 3)
            }
        }

class PortfolioEngine:
    """
    多資產投資組合引擎

    Features:
    - 多資產組合回測
    - 現代投資組合理論 (MPT)
    - 風險平價和等權重配置
    - 動態權重優化
    - 進階風險指標計算
    - 並行優化支持
    """

    def __init__(self, config: Optional[PortfolioConfig] = None):
        """初始化投資組合引擎"""
        self.config = config or PortfolioConfig()

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for Portfolio Engine")

        logger.info("Portfolio Engine initialized")

    def backtest_portfolio(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy: str = "EQUAL_WEIGHT",
        weights: Optional[Dict[str, float]] = None,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> PortfolioResult:
        """
        執行多資產投資組合回測

        Args:
            data_dict: 資產數據字典 {symbol: DataFrame}
            strategy: 投資組合策略
            weights: 自定義權重
            strategy_params: 策略參數

        Returns:
            PortfolioResult: 投資組合回測結果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting portfolio backtest for {len(data_dict)} assets")

            # 驗證輸入數據
            self._validate_data(data_dict)

            # 獲取資產列表
            assets = list(data_dict.keys())

            # 準備價格數據
            price_matrix = self._prepare_price_matrix(data_dict)

            # 生成信號
            signals_dict = self._generate_portfolio_signals(data_dict, strategy, strategy_params or {})

            # 應用權重
            final_weights = self._apply_weights(assets, strategy, weights, signals_dict)

            # 執行回測
            portfolio_metrics = self._execute_portfolio_backtest(price_matrix, signals_dict, final_weights)

            # 計算個別資產表現
            individual_metrics = self._calculate_individual_metrics(data_dict, signals_dict)

            # 計算進階風險指標
            risk_metrics = self._calculate_risk_metrics(portfolio_metrics['returns'])

            # 創建結果
            result = PortfolioResult(
                assets=assets,
                weights=final_weights,
                strategy=strategy,
                portfolio_return=portfolio_metrics['total_return'],
                portfolio_sharpe=portfolio_metrics['sharpe_ratio'],
                portfolio_volatility=portfolio_metrics['volatility'],
                portfolio_max_drawdown=portfolio_metrics['max_drawdown'],
                portfolio_calmar=portfolio_metrics['calmar_ratio'],
                portfolio_sortino=portfolio_metrics['sortino_ratio'],
                individual_returns=individual_metrics['returns'],
                individual_sharpes=individual_metrics['sharpes'],
                individual_volatilities=individual_metrics['volatilities'],
                var_95=risk_metrics['var_95'],
                var_99=risk_metrics['var_99'],
                expected_shortfall=risk_metrics['expected_shortfall'],
                beta=risk_metrics['beta'],
                alpha=risk_metrics['alpha'],
                information_ratio=risk_metrics['information_ratio'],
                total_trades=portfolio_metrics['total_trades'],
                win_rate=portfolio_metrics['win_rate'],
                profit_factor=portfolio_metrics['profit_factor'],
                start_date=price_matrix.index[0].strftime('%Y-%m-%d'),
                end_date=price_matrix.index[-1].strftime('%Y-%m-%d'),
                execution_time=time.time() - start_time
            )

            logger.info(f"Portfolio backtest completed in {result.execution_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Portfolio backtest failed: {e}")
            raise

    def optimize_portfolio(
        self,
        data_dict: Dict[str, pd.DataFrame],
        optimization_method: str = "MAX_SHARPE",
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioResult:
        """
        優化投資組合權重

        Args:
            data_dict: 資產數據字典
            optimization_method: 優化方法
            constraints: 優化約束條件

        Returns:
            PortfolioResult: 優化後的投資組合結果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting portfolio optimization for {len(data_dict)} assets")

            assets = list(data_dict.keys())
            price_matrix = self._prepare_price_matrix(data_dict)

            # 計算收益率和協方差矩陣
            returns = price_matrix.pct_change().dropna()
            mean_returns = returns.mean() * 252  # 年化
            cov_matrix = returns.cov() * 252  # 年化協方差

            # 根據優化方法計算最優權重
            if optimization_method == "MAX_SHARPE":
                optimal_weights = self._maximize_sharpe_ratio(mean_returns, cov_matrix)
            elif optimization_method == "MIN_VOLATILITY":
                optimal_weights = self._minimize_volatility(cov_matrix)
            elif optimization_method == "EQUAL_WEIGHT":
                optimal_weights = self._equal_weights(len(assets))
            elif optimization_method == "RISK_PARITY":
                optimal_weights = self._risk_parity_weights(cov_matrix)
            else:
                raise ValueError(f"Unknown optimization method: {optimization_method}")

            # 應用約束條件
            if constraints:
                optimal_weights = self._apply_constraints(optimal_weights, constraints)

            # 構建權重字典
            weights_dict = {asset: weight for asset, weight in zip(assets, optimal_weights)}

            # 執行優化後的回測
            result = self.backtest_portfolio(
                data_dict=data_dict,
                strategy="OPTIMIZED_WEIGHTS",
                weights=weights_dict
            )

            logger.info(f"Portfolio optimization completed in {time.time() - start_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            raise

    def _validate_data(self, data_dict: Dict[str, pd.DataFrame]) -> None:
        """驗證輸入數據"""
        if len(data_dict) == 0:
            raise ValueError("No assets provided")

        if len(data_dict) > self.config.max_positions:
            raise ValueError(f"Too many assets: {len(data_dict)} > {self.config.max_positions}")

        # 檢查數據格式
        for symbol, data in data_dict.items():
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Asset {symbol} missing columns: {missing_columns}")

            if len(data) < 20:
                raise ValueError(f"Asset {symbol} has insufficient data: {len(data)}")

    def _prepare_price_matrix(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """準備價格矩陣"""
        price_matrix = pd.DataFrame()

        for symbol, data in data_dict.items():
            price_matrix[symbol] = data['close']

        # 確保所有資產有相同的日期範圍
        price_matrix = price_matrix.dropna()

        if len(price_matrix) < 20:
            raise ValueError("Insufficient overlapping data between assets")

        return price_matrix

    def _generate_portfolio_signals(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy: str,
        params: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """生成投資組合信號"""
        signals_dict = {}

        for symbol, data in data_dict.items():
            # 使用簡單的買入持有信號
            entries = pd.Series(False, index=data.index)
            exits = pd.Series(False, index=data.index)

            # 根據策略生成信號
            if strategy == "BUY_AND_HOLD":
                entries.iloc[0] = True
                exits.iloc[-1] = True
            elif strategy == "RSI_MEAN_REVERSION":
                import vectorbt as vbt
                rsi = vbt.RSI.run(data['close'], window=14)
                entries = (rsi.rsi < 30) & (~(rsi.rsi.shift(1) < 30))
                exits = (rsi.rsi > 70) & (~(rsi.rsi.shift(1) > 70))
            elif strategy == "DUAL_MOVING_AVERAGE":
                short_ma = data['close'].rolling(20).mean()
                long_ma = data['close'].rolling(50).mean()
                entries = (short_ma > long_ma) & (~(short_ma.shift(1) > long_ma.shift(1)))
                exits = (short_ma < long_ma) & (~(short_ma.shift(1) < long_ma.shift(1)))
            else:
                # 默認買入持有
                entries.iloc[0] = True

            signals_dict[symbol] = pd.DataFrame({
                'entries': entries,
                'exits': exits
            })

        return signals_dict

    def _apply_weights(
        self,
        assets: List[str],
        strategy: str,
        custom_weights: Optional[Dict[str, float]],
        signals_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """應用權重"""
        if custom_weights:
            # 使用自定義權重
            weights = custom_weights.copy()
            # 正規化權重
            total_weight = sum(weights.values())
            weights = {asset: weight/total_weight for asset, weight in weights.items()}
        else:
            # 使用預設權重
            if strategy == "EQUAL_WEIGHT":
                weight = 1.0 / len(assets)
                weights = {asset: weight for asset in assets}
            elif strategy == "OPTIMIZED_WEIGHTS":
                # 權重已在優化過程中計算
                weights = {asset: 1.0/len(assets) for asset in assets}
            else:
                # 默認等權重
                weight = 1.0 / len(assets)
                weights = {asset: weight for asset in assets}

        # 應用權重約束
        for asset in weights:
            weights[asset] = max(self.config.min_position_weight,
                               min(self.config.max_position_weight, weights[asset]))

        # 重新正規化
        total_weight = sum(weights.values())
        weights = {asset: weight/total_weight for asset, weight in weights.items()}

        return weights

    def _execute_portfolio_backtest(
        self,
        price_matrix: pd.DataFrame,
        signals_dict: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """執行投資組合回測"""
        # 準備信號數組 - 轉換為正確格式
        assets = list(signals_dict.keys())
        entries_list = []
        exits_list = []

        for asset in assets:
            # 確保信號是Series格式
            entries_series = signals_dict[asset]['entries']
            exits_series = signals_dict[asset]['exits']

            # 確保索引與price_matrix對齊
            entries_series = entries_series.reindex(price_matrix.index, fill_value=False)
            exits_series = exits_series.reindex(price_matrix.index, fill_value=False)

            entries_list.append(entries_series)
            exits_list.append(exits_series)

        # 計算每個資產的權重
        size_list = [weights.get(asset, 1.0/len(assets)) for asset in assets]

        # 創建投資組合 - 修復格式問題
        portfolio = vbt.Portfolio.from_signals(
            close=price_matrix,
            entries=entries_list,
            exits=exits_list,
            size=size_list,
            init_cash=self.config.initial_cash,
            fees=self.config.fees,
            slippage=self.config.slippage,
            freq=self.config.freq
        )

        # 計算指標
        returns = portfolio.returns()
        total_return = portfolio.total_return()
        sharpe_ratio = portfolio.sharpe_ratio()
        max_drawdown = portfolio.max_drawdown()
        volatility = returns.std() * np.sqrt(252)

        # Calmar比率
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() * 252) / (downside_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = 0.0

        # 交易統計
        trades = portfolio.trades
        win_rate = trades.win_rate() if len(trades) > 0 else 0.0
        profit_factor = trades.profit_factor() if len(trades) > 0 else 0.0
        total_trades = len(trades.records_readable) if len(trades) > 0 else 0

        return {
            'returns': returns,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }

    def _calculate_individual_metrics(
        self,
        data_dict: Dict[str, pd.DataFrame],
        signals_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """計算個別資產指標"""
        returns_dict = {}
        sharpes_dict = {}
        volatilities_dict = {}

        for asset, data in data_dict.items():
            signals = signals_dict[asset]

            # 創建單一資產組合
            portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=signals['entries'],
                exits=signals['exits'],
                init_cash=self.config.initial_cash,
                fees=self.config.fees,
                slippage=self.config.slippage
            )

            # 計算指標
            asset_returns = portfolio.returns()
            asset_return = portfolio.total_return()
            asset_sharpe = portfolio.sharpe_ratio()
            asset_volatility = asset_returns.std() * np.sqrt(252)

            returns_dict[asset] = asset_return
            sharpes_dict[asset] = asset_sharpe
            volatilities_dict[asset] = asset_volatility

        return {
            'returns': returns_dict,
            'sharpes': sharpes_dict,
            'volatilities': volatilities_dict
        }

    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """計算進階風險指標"""
        # VaR計算
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        # Expected Shortfall (CVaR)
        expected_shortfall = returns[returns <= var_95].mean()

        # Alpha和Beta (相對於市場基準)
        # 使用市場回報率作為基準 (簡化版本)
        market_returns = returns.rolling(20).mean()
        covariance = np.cov(returns.dropna(), market_returns.dropna())[0, 1]
        market_variance = np.var(market_returns.dropna())
        beta = covariance / market_variance if market_variance != 0 else 1.0

        # Alpha (簡化版本)
        risk_free_rate = 0.03 / 252  # 日無風險利率
        alpha = (returns.mean() - risk_free_rate) - beta * (market_returns.mean() - risk_free_rate)

        # Information Ratio
        tracking_error = (returns - market_returns).std()
        information_ratio = (returns.mean() - market_returns.mean()) / tracking_error if tracking_error != 0 else 0

        return {
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall': expected_shortfall,
            'beta': beta,
            'alpha': alpha,
            'information_ratio': information_ratio
        }

    def _maximize_sharpe_ratio(
        self,
        mean_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> np.ndarray:
        """最大化Sharpe比率"""
        num_assets = len(mean_returns)

        # 簡化版本：使用等權重作為起點
        weights = np.array([1/num_assets] * num_assets)

        # 在實際實現中，這裡會使用優化算法如scipy.optimize
        # 這裡使用簡化版本
        return weights

    def _minimize_volatility(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """最小化波動率"""
        num_assets = cov_matrix.shape[0]
        # 簡化版本：等權重
        return np.array([1/num_assets] * num_assets)

    def _equal_weights(self, num_assets: int) -> np.ndarray:
        """等權重"""
        return np.array([1/num_assets] * num_assets)

    def _risk_parity_weights(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """風險平價權重"""
        num_assets = cov_matrix.shape[0]
        # 簡化版本：基於波動率的倒數
        volatilities = np.sqrt(np.diag(cov_matrix))
        inv_vol = 1 / volatilities
        weights = inv_vol / inv_vol.sum()
        return weights

    def _apply_constraints(
        self,
        weights: np.ndarray,
        constraints: Dict[str, Any]
    ) -> np.ndarray:
        """應用約束條件"""
        # 簡化版本：應用權重範圍約束
        min_weight = constraints.get('min_weight', self.config.min_position_weight)
        max_weight = constraints.get('max_weight', self.config.max_position_weight)

        weights = np.maximum(weights, min_weight)
        weights = np.minimum(weights, max_weight)

        # 重新正規化
        weights = weights / weights.sum()

        return weights

# 便利函數
def create_portfolio_engine(config: Optional[PortfolioConfig] = None) -> PortfolioEngine:
    """創建投資組合引擎"""
    return PortfolioEngine(config)

def backtest_multi_asset_portfolio(
    data_dict: Dict[str, pd.DataFrame],
    strategy: str = "EQUAL_WEIGHT",
    weights: Optional[Dict[str, float]] = None
) -> PortfolioResult:
    """便利函數：多資產投資組合回測"""
    engine = PortfolioEngine()
    return engine.backtest_portfolio(data_dict, strategy, weights)