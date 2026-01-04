"""
Backtest Service v2.0
Integrated backtest service with new architecture
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from ..models.strategy_models_v2 import (
    Backtest, Strategy, StrategyInstance, Trade,
    BacktestStatus
)
from ..models.backtest_enhanced import BacktestResult, Position, BacktestConfig
from ..services.strategy_service_v2 import StrategyService
from ..strategies.enhanced_strategy_factory import EnhancedStrategyFactory
from ..strategies.strategy_factory_v2 import BaseStrategy
from ..backtest.enhanced_backtest_engine import (
    EnhancedBacktestEngine, BacktestMode
)
from ..services.influxdb_client import InfluxDBService

logger = logging.getLogger(__name__)


class BacktestServiceV2:
    """Enhanced backtest service integrated with new architecture"""

    def __init__(self, db: Session, influxdb_service: Optional[InfluxDBService] = None):
        self.db = db
        self.influxdb = influxdb_service
        self.strategy_service = StrategyService(db)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._running_backtests = {}

    async def run_backtest(
        self,
        backtest_id: UUID,
        data_source: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run backtest for given backtest configuration

        Args:
            backtest_id: Backtest ID
            data_source: Optional data source configuration

        Returns:
            Backtest results
        """
        try:
            # Get backtest configuration
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id
            ).first()

            if not backtest:
                raise ValueError(f"Backtest {backtest_id} not found")

            # Get strategy
            strategy = self.strategy_service.get_strategy(
                backtest.strategy_id,
                backtest.user_id
            )

            if not strategy:
                raise ValueError("Strategy not found or access denied")

            # Update backtest status
            backtest.status = BacktestStatus.RUNNING
            backtest.start_time = datetime.utcnow()
            self.db.commit()

            # Load historical data
            market_data = await self._load_market_data(
                backtest.symbols,
                backtest.start_date,
                backtest.end_date,
                data_source
            )

            # Create strategy instance
            strategy_instance = EnhancedStrategyFactory.create_strategy_from_config(
                strategy.strategy_type,
                strategy.config or {},
                backtest.parameters or {}
            )

            # Setup backtest configuration
            backtest_config = BacktestConfig(
                start_date=backtest.start_date,
                end_date=backtest.end_date,
                initial_capital=backtest.initial_capital,
                commission_rate=0.001,
                slippage_rate=0.0005,
                enable_risk_management=True,
                var_limit=0.02,
                max_drawdown_limit=0.15,
                leverage_limit=2.0,
                position_size_limit=0.3
            )

            # Create and run backtest engine
            engine = EnhancedBacktestEngine(backtest_config)

            # Run backtest
            logger.info(f"Starting backtest {backtest_id} for strategy {strategy.name}")
            result = engine.run_backtest(
                strategy=strategy_instance,
                market_data=market_data
            )

            # Process results
            await self._process_backtest_results(backtest, result)

            return {
                'backtest_id': str(backtest_id),
                'status': 'completed',
                'result': self._serialize_result(result)
            }

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            # Update backtest status
            if 'backtest' in locals():
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(e)
                backtest.end_time = datetime.utcnow()
                self.db.commit()

            raise

    async def run_parallel_backtests(
        self,
        backtest_ids: List[UUID],
        max_concurrent: int = 4
    ) -> List[Dict[str, Any]]:
        """Run multiple backtests in parallel"""
        results = []

        # Create semaphore to limit concurrent executions
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_single_backtest(backtest_id: UUID):
            async with semaphore:
                return await self.run_backtest(backtest_id)

        # Execute all backtests
        tasks = [run_single_backtest(bt_id) for bt_id in backtest_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _load_market_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        data_source: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Load historical market data for backtest"""
        try:
            if self.influxdb:
                # Load from InfluxDB
                data = {}
                for symbol in symbols:
                    market_data = self.influxdb.get_stock_prices(
                        symbol=symbol,
                        start_time=datetime.combine(start_date, datetime.min.time()),
                        end_time=datetime.combine(end_date, datetime.max.time())
                    )

                    if not market_data.empty:
                        data[symbol] = market_data.to_dict('records')
                    else:
                        # Fallback to alternative data source
                        data[symbol] = await self._load_fallback_data(symbol, start_date, end_date)

                return data
            else:
                # Load from alternative data sources
                data = {}
                for symbol in symbols:
                    data[symbol] = await self._load_fallback_data(symbol, start_date, end_date)
                return data

        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            raise

    async def _load_fallback_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Load data from fallback sources (e.g., yfinance)"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date,
                end=end_date + timedelta(days=1)  # Include end date
            )

            # Convert to list of dictionaries
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'date': date.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })

            return data

        except Exception as e:
            logger.error(f"Failed to load fallback data for {symbol}: {e}")
            return []

    async def _process_backtest_results(
        self,
        backtest: Backtest,
        result: BacktestResult
    ) -> None:
        """Process and store backtest results"""
        try:
            # Update backtest record
            backtest.status = BacktestStatus.COMPLETED
            backtest.end_time = datetime.utcnow()

            # Performance metrics
            backtest.final_equity = result.equity_curve.iloc[-1] if result.equity_curve is not None else None
            backtest.total_return = result.total_return
            backtest.annualized_return = result.annualized_return
            backtest.volatility = result.volatility
            backtest.max_drawdown = result.max_drawdown
            backtest.sharpe_ratio = result.sharpe_ratio
            backtest.var_95 = result.var_95
            backtest.expected_shortfall = result.expected_shortfall_95

            # Trading statistics
            if result.trades:
                backtest.total_trades = len(result.trades)

                # Calculate win rate
                winning_trades = sum(1 for t in result.trades if t.side == 'sell' and
                                   (t.price - t.commission - t.slippage) > 0)
                backtest.winning_trades = winning_trades
                backtest.losing_trades = backtest.total_trades - winning_trades

                if backtest.total_trades > 0:
                    backtest.win_rate = (winning_trades / backtest.total_trades) * 100

                # Calculate average win/loss
                wins = []
                losses = []
                for trade in result.trades:
                    pnl = (trade.price - trade.commission - trade.slippage) * trade.quantity
                    if pnl > 0:
                        wins.append(pnl)
                    else:
                        losses.append(abs(pnl))

                backtest.avg_win = sum(wins) / len(wins) if wins else None
                backtest.avg_loss = sum(losses) / len(losses) if losses else None

                if backtest.avg_loss and backtest.avg_loss > 0:
                    backtest.profit_factor = sum(wins) / sum(losses) if losses else None

            # Store detailed results
            backtest.equity_curve = result.equity_curve.to_dict() if result.equity_curve is not None else None
            backtest.trade_history = self._serialize_trades(result.trades) if result.trades else None

            # Calculate additional metrics
            backtest.calmar_ratio = result.calmar_ratio
            backtest.sortino_ratio = result.sortino_ratio

            self.db.commit()

            # Store performance records in InfluxDB
            if self.influxdb and result.equity_curve is not None:
                await self._store_performance_data(backtest, result)

            logger.info(f"Backtest {backtest.id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to process backtest results: {e}")
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.end_time = datetime.utcnow()
            self.db.commit()
            raise

    def _serialize_result(self, result: BacktestResult) -> Dict[str, Any]:
        """Serialize backtest result for API response"""
        return {
            'total_return': result.total_return,
            'annualized_return': result.annualized_return,
            'volatility': result.volatility,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'calmar_ratio': result.calmar_ratio,
            'var_95': result.var_95,
            'expected_shortfall': result.expected_shortfall_95,
            'total_trades': result.total_trades,
            'win_rate': result.win_rate,
            'avg_win': result.avg_win,
            'avg_loss': result.avg_loss,
            'profit_factor': result.profit_factor,
            'information_ratio': result.information_ratio,
            'sortino_ratio': result.sortino_ratio
        }

    def _serialize_trades(self, trades: List) -> List[Dict[str, Any]]:
        """Serialize trades for storage"""
        serialized = []
        for trade in trades:
            serialized.append({
                'timestamp': trade.timestamp.isoformat(),
                'symbol': trade.symbol,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'commission': trade.commission,
                'slippage': trade.slippage
            })
        return serialized

    async def _store_performance_data(
        self,
        backtest: Backtest,
        result: BacktestResult
    ) -> None:
        """Store daily performance data in InfluxDB"""
        try:
            if result.equity_curve is None:
                return

            # Calculate daily returns
            daily_returns = result.equity_curve.pct_change().dropna()

            # Store in InfluxDB
            performance_data = []
            current_date = backtest.start_date

            for i, (date, equity) in enumerate(result.equity_curve.items()):
                if i < len(daily_returns):
                    perf_record = {
                        'measurement': 'backtest_performance',
                        'timestamp': date,
                        'tags': {
                            'backtest_id': str(backtest.id),
                            'strategy_id': str(backtest.strategy_id)
                        },
                        'fields': {
                            'equity': equity,
                            'return': daily_returns.iloc[i] if i < len(daily_returns) else 0,
                            'cumulative_return': ((equity - backtest.initial_capital) /
                                                  backtest.initial_capital) * 100
                        }
                    }
                    performance_data.append(perf_record)

            # Batch write to InfluxDB
            if performance_data:
                success = await self.influxdb.write_market_data(
                    performance_data,
                    "backtest_performance",
                    "strategy_performance"
                )

                if success:
                    logger.info(f"Stored {len(performance_data)} performance records")

        except Exception as e:
            logger.error(f"Failed to store performance data: {e}")

    def get_backtest_results(
        self,
        backtest_id: UUID,
        include_detailed: bool = False
    ) -> Dict[str, Any]:
        """Get detailed backtest results"""
        backtest = self.db.query(Backtest).filter(
            Backtest.id == backtest_id
        ).first()

        if not backtest:
            raise ValueError(f"Backtest {backtest_id} not found")

        result = {
            'id': str(backtest.id),
            'name': backtest.name,
            'strategy_id': str(backtest.strategy_id),
            'status': backtest.status,
            'created_at': backtest.created_at.isoformat(),
            'start_date': backtest.start_date.isoformat(),
            'end_date': backtest.end_date.isoformat(),
            'initial_capital': backtest.initial_capital,
            'final_equity': backtest.final_equity,
            'total_return': backtest.total_return,
            'annualized_return': backtest.annualized_return,
            'max_drawdown': backtest.max_drawdown,
            'sharpe_ratio': backtest.sharpe_ratio,
            'total_trades': backtest.total_trades,
            'win_rate': backtest.win_rate,
            'profit_factor': backtest.profit_factor,
            'computation_time': backtest.computation_time,
            'error_message': backtest.error_message
        }

        if include_detailed:
            result['equity_curve'] = backtest.equity_curve
            result['trade_history'] = backtest.trade_history
            result['monthly_returns'] = self._calculate_monthly_returns(backtest)
            result['rolling_metrics'] = self._calculate_rolling_metrics(backtest)

        return result

    def _calculate_monthly_returns(self, backtest: Backtest) -> Dict[str, float]:
        """Calculate monthly returns from equity curve"""
        if not backtest.equity_curve:
            return {}

        try:
            equity_df = pd.DataFrame(backtest.equity_curve)
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            equity_df.set_index('date', inplace=True)

            # Calculate monthly returns
            monthly_returns = equity_df.resample('M').last().pct_change().dropna()

            return {date.strftime('%Y-%m'): float(ret)
                   for date, ret in monthly_returns.items()}
        except Exception as e:
            logger.error(f"Failed to calculate monthly returns: {e}")
            return {}

    def _calculate_rolling_metrics(self, backtest: Backtest) -> Dict[str, Any]:
        """Calculate rolling performance metrics"""
        if not backtest.equity_curve:
            return {}

        try:
            equity_df = pd.DataFrame(backtest.equity_curve)
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            equity_df.set_index('date', inplace=True)

            # Calculate rolling returns
            equity_df['returns'] = equity_df['equity'].pct_change()

            # Rolling Sharpe ratio (30-day)
            rolling_sharpe = equity_df['returns'].rolling(window=30).mean() / \
                           equity_df['returns'].rolling(window=30).std() * np.sqrt(252)

            # Rolling drawdown
            equity_df['cummax'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['cummax'] - equity_df['equity']) / equity_df['cummax']

            return {
                'rolling_sharpe_30d': rolling_sharpe.fillna(0).iloc[-30:].tolist() if len(rolling_sharpe) >= 30 else [],
                'rolling_drawdown': equity_df['drawdown'].tolist(),
                'max_rolling_drawdown': float(equity_df['drawdown'].max())
            }
        except Exception as e:
            logger.error(f"Failed to calculate rolling metrics: {e}")
            return {}

    def compare_backtests(
        self,
        backtest_ids: List[UUID]
    ) -> Dict[str, Any]:
        """Compare multiple backtests"""
        results = {}
        for bt_id in backtest_ids:
            try:
                results[str(bt_id)] = self.get_backtest_results(bt_id)
            except Exception as e:
                logger.error(f"Failed to get results for backtest {bt_id}: {e}")
                results[str(bt_id)] = {'error': str(e)}

        # Calculate comparison metrics
        comparison = self._calculate_comparison_metrics(results)

        return {
            'individual_results': results,
            'comparison': comparison
        }

    def _calculate_comparison_metrics(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between backtests"""
        valid_results = {k: v for k, v in results.items()
                          if 'error' not in v and 'total_return' in v}

        if not valid_results:
            return {}

        returns = [r['total_return'] for r in valid_results.values()]
        sharpe_ratios = [r.get('sharpe_ratio', 0) for r in valid_results.values()]
        max_drawdowns = [r.get('max_drawdown', 0) for r in valid_results.values()]

        return {
            'best_return': max(returns),
            'worst_return': min(returns),
            'average_return': sum(returns) / len(returns),
            'best_sharpe': max(sharpe_ratios),
            'average_sharpe': sum(sharpe_ratios) / len(sharpe_ratios),
            'lowest_drawdown': min(max_drawdowns),
            'average_drawdown': sum(max_drawdowns) / len(max_drawdowns),
            'ranking': self._rank_backtests(valid_results)
        }

    def _rank_backtests(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank backtests by composite score"""
        def calculate_score(r):
            # Composite score weighting
            return (
                r['total_return'] * 0.4 +
                (r.get('sharpe_ratio', 0) / 2) * 0.3 +
                (1 - r.get('max_drawdown', 0) / 0.3) * 0.3
            )

        ranked = sorted(
            [(bt_id, result, calculate_score(result))
             for bt_id, result in results.items()],
            key=lambda x: x[2],
            reverse=True
        )

        return [
            {
                'backtest_id': bt_id,
                'rank': i + 1,
                'score': score,
                'total_return': result['total_return'],
                'sharpe_ratio': result.get('sharpe_ratio', 0),
                'max_drawdown': result.get('max_drawdown', 0)
            }
            for i, (bt_id, result, score) in enumerate(ranked)
        ]

    def stop_backtest(self, backtest_id: UUID) -> bool:
        """Stop a running backtest"""
        try:
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id
            ).first()

            if not backtest:
                return False

            if backtest.status == BacktestStatus.RUNNING:
                # Update status
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = "Backtest stopped by user"
                backtest.end_time = datetime.utcnow()
                self.db.commit()

                # Remove from running backtests if exists
                if str(backtest_id) in self._running_backtests:
                    del self._running_backtests[str(backtest_id)]

                logger.info(f"Backtest {backtest_id} stopped")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to stop backtest {backtest_id}: {e}")
            return False

    def get_running_backtests(self) -> List[Dict[str, Any]]:
        """Get list of currently running backtests"""
        running_backtests = self.db.query(Backtest).filter(
            Backtest.status == BacktestStatus.RUNNING
        ).all()

        return [
            {
                'id': str(bt.id),
                'name': bt.name,
                'strategy_id': str(bt.strategy_id),
                'start_time': bt.start_time.isoformat() if bt.start_time else None,
                'progress': self._estimate_progress(bt)
            }
            for bt in running_backtests
        ]

    def _estimate_progress(self, backtest: Backtest) -> float:
        """Estimate backtest progress based on elapsed time"""
        if not backtest.start_time:
            return 0.0

        elapsed = datetime.utcnow() - backtest.start_time
        total_time = (backtest.end_date - backtest.start_date).total_seconds()

        # Rough estimation based on time
        progress = min((elapsed.total_seconds() / total_time) * 100, 100)
        return progress