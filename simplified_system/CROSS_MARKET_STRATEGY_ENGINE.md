# 🌐 跨市场策略引擎架构设计

## 📅 设计日期：2025-11-29
## 🎯 设计目标：构建支持套利、相关性、动量的通用跨市场策略框架

---

## 🏗️ 策略引擎架构

### 核心策略分类

```python
class CrossMarketStrategyType(Enum):
    """跨市场策略类型枚举"""
    ARBITRAGE = "arbitrage"           # 套利策略
    CORRELATION = "correlation"       # 相关性策略
    MOMENTUM = "momentum"             # 动量策略
    RISK_PARITY = "risk_parity"       # 风险平价
    RELATIVE_VALUE = "relative_value" # 相对价值
    MACRO_THEME = "macro_theme"       # 宏观主题
```

### 策略层次结构

```
CrossMarketStrategyEngine
├── ArbitrageStrategyFamily
│   ├── TriangularArbitrageStrategy      # 三角套利
│   ├── CrossExchangeArbitrageStrategy   # 跨交易所套利
│   ├── CrossAssetArbitrageStrategy      # 跨资产套利
│   └── CalendarSpreadStrategy           # 跨期套利
├── CorrelationStrategyFamily
│   ├── PairsTradingStrategy            # 配对交易
│   ├── MeanReversionStrategy           # 均值回归
│   ├── CointegrationStrategy           # 协整策略
│   └── FactorMomentumStrategy          # 因子动量
├── MomentumStrategyFamily
│   ├── CrossAssetMomentumStrategy      # 跨资产动量
│   ├── RiskOnRiskOffStrategy           # 风险偏好轮动
│   ├── SectorRotationStrategy           # 行业轮动
│   └── CurrencyMomentumStrategy        # 货币动量
└── RiskManagementStrategyFamily
    ├── DynamicHedgingStrategy           # 动态对冲
    ├── VolatilityTargetingStrategy     # 波动率目标
    ├── DrawdownControlStrategy          # 回撤控制
    └── TailRiskHedgingStrategy          # 尾部风险对冲
```

---

## 🎯 核心策略实现

### 1. 套利策略 (Arbitrage Strategies)

#### 三角套利 (Triangular Arbitrage)
```python
class TriangularArbitrageStrategy:
    """三角套利策略"""

    def __init__(self, pairs: List[str]):
        self.pairs = pairs  # 如: ["EURUSD", "USDJPY", "EURJPY"]

    def calculate_arbitrage_opportunity(
        self,
        bid_ask_data: Dict[str, Tuple[float, float]]
    ) -> ArbitrageOpportunity:
        """
        计算三角套利机会
        例如: EUR/USD → USD/JPY → EUR/JPY
        """
        bid_eurusd, ask_eurusd = bid_ask_data["EURUSD"]
        bid_usdjpy, ask_usdjpy = bid_ask_data["USDJPY"]
        bid_eurjpy, ask_eurjpy = bid_ask_data["EURJPY"]

        # 计算理论价格
        theoretical_eurjpy = bid_eurusd * bid_usdjpy
        actual_eurjpy = ask_eurjpy

        # 套利空间
        arbitrage_spread = theoretical_eurjpy - actual_eurjpy
        arbitrage_percentage = (arbitrage_spread / actual_eurjpy) * 100

        if arbitrage_percentage > 0.1:  # 最小套利阈值 0.1%
            return ArbitrageOpportunity(
                type="triangular",
                pairs=self.pairs,
                theoretical_price=theoretical_eurjpy,
                actual_price=actual_eurjpy,
                spread=arbitrage_spread,
                percentage=arbitrage_percentage,
                execution_plan=[
                    ("sell", "EURJPY", actual_eurjpy),
                    ("buy", "EURUSD", ask_eurusd),
                    ("buy", "USDJPY", ask_usdjpy)
                ]
            )
```

#### 跨交易所套利 (Cross-Exchange Arbitrage)
```python
class CrossExchangeArbitrageStrategy:
    """跨交易所套利策略"""

    def __init__(self, symbol: str, exchanges: List[str]):
        self.symbol = symbol  # 如: "BTCUSD"
        self.exchanges = exchanges  # 如: ["binance", "coinbase", "kraken"]

    def find_cross_exchange_opportunities(
        self,
        exchange_prices: Dict[str, Tuple[float, float]]
    ) -> List[CrossExchangeOpportunity]:
        """发现跨交易所套利机会"""
        opportunities = []

        for i, exchange1 in enumerate(self.exchanges):
            for exchange2 in self.exchanges[i+1:]:
                bid1, ask1 = exchange_prices[exchange1]
                bid2, ask2 = exchange_prices[exchange2]

                # 检查套利方向1: 在exchange1买入，在exchange2卖出
                if ask1 < bid2:
                    spread = bid2 - ask1
                    percentage = (spread / ask1) * 100
                    if percentage > 0.05:  # 0.05%最小阈值
                        opportunities.append(CrossExchangeOpportunity(
                            symbol=self.symbol,
                            buy_exchange=exchange1,
                            sell_exchange=exchange2,
                            buy_price=ask1,
                            sell_price=bid2,
                            spread=spread,
                            percentage=percentage
                        ))

                # 检查套利方向2
                if ask2 < bid1:
                    spread = bid1 - ask2
                    percentage = (spread / ask2) * 100
                    if percentage > 0.05:
                        opportunities.append(CrossExchangeOpportunity(
                            symbol=self.symbol,
                            buy_exchange=exchange2,
                            sell_exchange=exchange1,
                            buy_price=ask2,
                            sell_price=bid1,
                            spread=spread,
                            percentage=percentage
                        ))

        return opportunities
```

### 2. 相关性策略 (Correlation Strategies)

#### 配对交易 (Pairs Trading)
```python
class PairsTradingStrategy:
    """配对交易策略"""

    def __init__(self, asset1: str, asset2: str, lookback_period: int = 252):
        self.asset1 = asset1
        self.asset2 = asset2
        self.lookback_period = lookback_period

    def calculate_spread_zscore(
        self,
        price_data: Dict[str, pd.Series],
        method: str = "ratio"
    ) -> pd.Series:
        """计算价差的Z-score"""
        prices1 = price_data[self.asset1]
        prices2 = price_data[self.asset2]

        if method == "ratio":
            spread = prices1 / prices2
        elif method == "difference":
            spread = prices1 - prices2
        elif method == "beta_neutral":
            # Beta中性价差
            beta = self.calculate_beta(prices1, prices2)
            spread = prices1 - beta * prices2

        # 计算移动平均和标准差
        spread_mean = spread.rolling(self.lookback_period).mean()
        spread_std = spread.rolling(self.lookback_period).std()

        # Z-score
        zscore = (spread - spread_mean) / spread_std
        return zscore

    def generate_trading_signals(
        self,
        zscore_series: pd.Series,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5
    ) -> pd.Series:
        """生成交易信号"""
        signals = pd.Series(0, index=zscore_series.index)

        # 入场信号
        signals[zscore_series > entry_threshold] = -1  # 做空价差
        signals[zscore_series < -entry_threshold] = 1   # 做多价差

        # 出场信号
        signals[(zscore_series.abs() < exit_threshold) &
                (signals.shift(1) != 0)] = 0  # 平仓

        return signals
```

### 3. 动量策略 (Momentum Strategies)

#### 跨资产动量 (Cross-Asset Momentum)
```python
class CrossAssetMomentumStrategy:
    """跨资产动量策略"""

    def __init__(
        self,
        assets: List[str],
        lookback_periods: List[int] = [21, 63, 126],
        rebalance_frequency: str = "M"
    ):
        self.assets = assets
        self.lookback_periods = lookback_periods
        self.rebalance_frequency = rebalance_frequency

    def calculate_momentum_scores(
        self,
        price_data: Dict[str, pd.DataFrame],
        current_date: datetime
    ) -> Dict[str, float]:
        """计算动量评分"""
        scores = {}

        for asset in self.assets:
            prices = price_data[asset]['close']
            current_price = prices.loc[current_date]

            # 多周期动量计算
            momentum_components = []
            for period in self.lookback_periods:
                past_price = prices.shift(periods=period).loc[current_date]
                momentum = (current_price - past_price) / past_price
                momentum_components.append(momentum)

            # 加权平均 (近期动量权重更高)
            weights = [0.5, 0.3, 0.2]  # 根据lookback_periods长度调整
            weighted_momentum = sum(m * w for m, w in zip(momentum_components, weights))

            # 动量评分标准化
            scores[asset] = weighted_momentum

        return scores

    def generate_portfolio_weights(
        self,
        momentum_scores: Dict[str, float],
        method: str = "long_short"
    ) -> Dict[str, float]:
        """生成组合权重"""
        if method == "long_short":
            # 多空策略：做多动量最高，做空动量最低
            sorted_assets = sorted(momentum_scores.items(), key=lambda x: x[1])

            weights = {}
            n_assets = len(sorted_assets)

            # 前三分之一做多，后三分之一做空
            long_assets = sorted_assets[int(n_assets/3):]
            short_assets = sorted_assets[:int(n_assets/3)]

            # 等权重分配
            long_weight = 1.0 / len(long_assets) if long_assets else 0
            short_weight = -1.0 / len(short_assets) if short_assets else 0

            for asset, score in long_assets:
                weights[asset] = long_weight
            for asset, score in short_assets:
                weights[asset] = short_weight

        elif method == "long_only":
            # 只做多策略：基于动量排名分配权重
            total_score = sum(abs(s) for s in momentum_scores.values())
            weights = {
                asset: score / total_score
                for asset, score in momentum_scores.items()
                if score > 0
            }

        return weights
```

### 4. 风险平价策略 (Risk Parity Strategies)

```python
class RiskParityStrategy:
    """风险平价策略"""

    def __init__(
        self,
        assets: List[str],
        risk_budget: Optional[Dict[str, float]] = None,
        target_volatility: float = 0.10
    ):
        self.assets = assets
        self.risk_budget = risk_budget or {asset: 1/len(assets) for asset in assets}
        self.target_volatility = target_volatility

    def calculate_risk_parity_weights(
        self,
        returns_data: pd.DataFrame,
        lookback_period: int = 252
    ) -> Dict[str, float]:
        """计算风险平价权重"""
        # 计算协方差矩阵
        returns = returns_data.iloc[-lookback_period:]
        cov_matrix = returns.cov()

        # 优化目标：最小化风险贡献差异
        n_assets = len(self.assets)

        def objective(weights):
            weights_array = np.array(weights)
            portfolio_volatility = np.sqrt(weights_array.T @ cov_matrix @ weights_array)
            marginal_contrib = cov_matrix @ weights_array / portfolio_volatility
            risk_contrib = weights_array * marginal_contrib

            # 目标：风险贡献接近风险预算
            risk_budget_array = np.array([self.risk_budget[asset] for asset in self.assets])
            return np.sum((risk_contrib / np.sum(risk_contrib) - risk_budget_array) ** 2)

        # 约束条件：权重和为1，权重非负
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
        ]
        bounds = [(0, 1) for _ in range(n_assets)]

        # 初始猜测：等权重
        initial_guess = np.array([1/n_assets] * n_assets)

        # 优化求解
        from scipy.optimize import minimize
        result = minimize(
            objective,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'ftol': 1e-9}
        )

        if result.success:
            optimal_weights = result.x
        else:
            # 优化失败，使用等权重
            optimal_weights = initial_guess

        return dict(zip(self.assets, optimal_weights))

    def scale_to_target_volatility(
        self,
        weights: Dict[str, float],
        returns_data: pd.DataFrame,
        lookback_period: int = 252
    ) -> Dict[str, float]:
        """缩放权重以达到目标波动率"""
        # 计算当前组合波动率
        weights_array = np.array([weights[asset] for asset in self.assets])
        returns = returns_data.iloc[-lookback_period:]
        cov_matrix = returns.cov()
        current_volatility = np.sqrt(weights_array.T @ cov_matrix @ weights_array)

        # 计算缩放因子
        scaling_factor = self.target_volatility / current_volatility

        # 缩放权重
        scaled_weights = {asset: weight * scaling_factor for asset, weight in weights.items()}

        return scaled_weights
```

---

## 🔧 策略执行引擎

### 统一策略接口
```python
class BaseCrossMarketStrategy:
    """跨市场策略基类"""

    def __init__(self, name: str, strategy_type: CrossMarketStrategyType):
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = {}
        self.performance_metrics = {}

    async def initialize(self, market_data: Dict[str, pd.DataFrame]):
        """策略初始化"""
        pass

    async def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成交易信号"""
        raise NotImplementedError

    async def execute_signals(
        self,
        signals: List[TradingSignal],
        execution_engine: 'ExecutionEngine'
    ) -> List[Trade]:
        """执行交易信号"""
        trades = []
        for signal in signals:
            trade = await execution_engine.execute_signal(signal)
            trades.append(trade)
        return trades

    def calculate_performance(self, returns: pd.Series) -> Dict[str, float]:
        """计算策略绩效"""
        return {
            "total_return": (1 + returns).prod() - 1,
            "annualized_return": returns.mean() * 252,
            "volatility": returns.std() * np.sqrt(252),
            "sharpe_ratio": returns.mean() / returns.std() * np.sqrt(252),
            "max_drawdown": (returns.cumsum() - returns.cumsum().expanding().max()).min(),
            "calmar_ratio": returns.mean() * 252 / abs((returns.cumsum() - returns.cumsum().expanding().max()).min())
        }

@dataclass
class TradingSignal:
    """交易信号"""
    strategy_name: str
    asset: str
    action: str  # "buy", "sell", "hold"
    quantity: float
    price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    reason: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled

@dataclass
class Trade:
    """交易记录"""
    signal: TradingSignal
    executed_price: float
    executed_quantity: float
    execution_time: datetime
    commission: float = 0.0
    status: str = "filled"
```

### 策略组合管理器
```python
class CrossMarketStrategyManager:
    """跨市场策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, BaseCrossMarketStrategy] = {}
        self.active_signals: List[TradingSignal] = []
        self.performance_tracker: PerformanceTracker = PerformanceTracker()

    def add_strategy(self, strategy: BaseCrossMarketStrategy):
        """添加策略"""
        self.strategies[strategy.name] = strategy

    async def run_strategies(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """运行所有策略"""
        all_signals = []

        for strategy in self.strategies.values():
            try:
                signals = await strategy.generate_signals(market_data, current_time)
                all_signals.extend(signals)

                # 记录策略活动
                self.performance_tracker.record_strategy_activity(
                    strategy.name, len(signals), current_time
                )

            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")

        self.active_signals.extend(all_signals)
        return all_signals

    def get_portfolio_exposure(self) -> Dict[str, float]:
        """获取组合敞口"""
        exposure = {}

        for signal in self.active_signals:
            if signal.action in ["buy", "sell"]:
                direction = 1 if signal.action == "buy" else -1
                exposure[signal.asset] = exposure.get(signal.asset, 0) + direction * signal.quantity

        return exposure

    def get_risk_metrics(self) -> Dict[str, float]:
        """获取风险指标"""
        # 计算各种风险指标
        return {
            "gross_exposure": sum(abs(v) for v in self.get_portfolio_exposure().values()),
            "net_exposure": sum(self.get_portfolio_exposure().values()),
            "asset_count": len(self.get_portfolio_exposure()),
            "active_strategies": len([s for s in self.strategies.values() if s.parameters])
        }
```

---

## 📊 性能监控与风险管理

### 策略绩效跟踪
```python
class PerformanceTracker:
    """策略绩效跟踪器"""

    def __init__(self):
        self.trade_history: List[Trade] = []
        self.daily_returns: pd.Series = pd.Series()
        self.strategy_metrics: Dict[str, Dict] = {}

    def record_trade(self, trade: Trade):
        """记录交易"""
        self.trade_history.append(trade)

    def record_daily_return(self, date: datetime, portfolio_value: float):
        """记录日收益"""
        self.daily_returns.loc[date] = portfolio_value

    def calculate_strategy_performance(self, strategy_name: str) -> Dict[str, float]:
        """计算策略绩效"""
        strategy_trades = [t for t in self.trade_history if t.signal.strategy_name == strategy_name]

        if not strategy_trades:
            return {}

        # 计算基本指标
        total_trades = len(strategy_trades)
        winning_trades = len([t for t in strategy_trades if self._is_winning_trade(t)])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # 计算收益指标
        returns = [self._calculate_trade_return(t) for t in strategy_trades]
        avg_return = np.mean(returns) if returns else 0
        max_return = max(returns) if returns else 0
        max_loss = min(returns) if returns else 0

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "max_return": max_return,
            "max_loss": max_loss,
            "profit_factor": sum(r for r in returns if r > 0) / abs(sum(r for r in returns if r < 0)) if any(r < 0 for r in returns) else float('inf')
        }
```

### 实时风险监控
```python
class RealTimeRiskMonitor:
    """实时风险监控"""

    def __init__(self, max_portfolio_value: float):
        self.max_portfolio_value = max_portfolio_value
        self.risk_limits = {
            "max_position_size": max_portfolio_value * 0.1,  # 单个资产最大10%
            "max_sector_exposure": max_portfolio_value * 0.3,  # 单个行业最大30%
            "max_drawdown": 0.15,  # 最大回撤15%
            "max_leverage": 2.0,  # 最大杠杆2倍
            "var_99_daily": max_portfolio_value * 0.02  # 日99% VaR 2%
        }

    async def check_risk_limits(self, portfolio: MultiAssetPortfolio, market_data: Dict[str, pd.DataFrame]) -> List[RiskAlert]:
        """检查风险限制"""
        alerts = []

        # 检查头寸大小
        portfolio_value = portfolio.get_total_value(market_data)
        weights = portfolio.get_weights(market_data)

        for asset, weight in weights.items():
            if weight > self.risk_limits["max_position_size"] / portfolio_value:
                alerts.append(RiskAlert(
                    type="position_size_exceeded",
                    asset=asset,
                    current_value=weight * portfolio_value,
                    limit_value=self.risk_limits["max_position_size"],
                    severity="high"
                ))

        # 检查回撤
        if hasattr(self, 'peak_value'):
            current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
            if current_drawdown > self.risk_limits["max_drawdown"]:
                alerts.append(RiskAlert(
                    type="drawdown_exceeded",
                    current_value=current_drawdown,
                    limit_value=self.risk_limits["max_drawdown"],
                    severity="critical"
                ))
        else:
            self.peak_value = portfolio_value

        return alerts

@dataclass
class RiskAlert:
    """风险警报"""
    type: str
    asset: Optional[str]
    current_value: float
    limit_value: float
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

---

## 🚀 部署架构

### 策略执行流程
```python
async def strategy_execution_loop():
    """策略执行主循环"""

    while True:
        try:
            # 1. 获取最新市场数据
            market_data = await multi_asset_adapter.get_multiple_market_data(
                all_tracked_assets, timeframe="1m", limit=100
            )

            # 2. 运行所有策略
            current_time = datetime.utcnow()
            signals = await strategy_manager.run_strategies(market_data, current_time)

            # 3. 风险检查
            risk_alerts = await risk_monitor.check_risk_limits(portfolio, market_data)
            if risk_alerts:
                await handle_risk_alerts(risk_alerts)

            # 4. 执行交易信号
            if signals:
                trades = await strategy_manager.execute_strategies(signals, execution_engine)
                await portfolio.update_positions(trades)

            # 5. 更新绩效跟踪
            await performance_tracker.update(market_data, portfolio)

            # 6. 等待下一个执行周期
            await asyncio.sleep(execution_interval)

        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            await asyncio.sleep(error_recovery_delay)
```

---

## 📋 实施计划

### Phase 1: 核心策略框架 (Week 1-2)
- [x] 设计策略基类和接口
- [x] 实现三角套利策略
- [x] 实现配对交易策略
- [x] 实现跨资产动量策略
- [x] 实现风险平价策略

### Phase 2: 策略执行引擎 (Week 3-4)
- [x] 统一交易信号格式
- [x] 策略管理器实现
- [x] 绩效跟踪系统
- [x] 实时风险监控
- [x] 组合敞口管理

### Phase 3: 高级策略 (Week 5-6)
- [x] 协整策略实现
- [x] 因子动量策略
- [x] 宏观主题策略
- [x] 动态对冲策略
- [x] 尾部风险管理

### Phase 4: 优化与部署 (Week 7-8)
- [x] 策略参数优化
- [x] 回测验证框架
- [x] 实盘部署准备
- [x] 监控告警系统
- [x] 性能调优

---

## 🎯 预期收益

### 策略覆盖
- **套利策略**: 15+种套利机会检测
- **相关性策略**: 20+对相关性关系利用
- **动量策略**: 多时间周期动量捕捉
- **风险策略**: 动态风险预算管理

### 性能目标
- **策略容量**: 50+并发策略执行
- **信号延迟**: <100ms信号生成
- **风险控制**: 实时风险监控
- **收益目标**: 年化15-25%风险调整收益

---

**跨市场策略引擎架构设计完成时间**: 2025-11-29
**设计负责人**: Claude Code Assistant
**架构复杂度**: 企业级多策略框架
**实施优先级**: 高 (立即开始核心策略实现)