"""
CBBC Sentiment-Based Trading Strategy
Uses CBSC market sentiment data to make trading decisions
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..services.cbbc_data_reader import CBBCDataReader
from ..services.market_sentiment_analyzer import MarketSentimentAnalyzer, SentimentLevel, MarketPhase

logger = logging.getLogger(__name__)


@dataclass
class StrategyParameters:
    """Parameters for the CBBC Sentiment Strategy"""
    # Sentiment thresholds
    extreme_fear_threshold: float = 20.0
    extreme_greed_threshold: float = 80.0
    fear_threshold: float = 40.0
    greed_threshold: float = 60.0

    # Position sizing
    base_position_size: float = 0.1  # 10% of capital
    max_position_size: float = 0.3   # 30% of capital
    position_scaling_factor: float = 2.0

    # Risk management
    stop_loss_pct: float = 0.02      # 2% stop loss
    take_profit_pct: float = 0.04    # 4% take profit
    max_drawdown: float = 0.1        # 10% maximum drawdown

    # Volatility filters
    min_volatility: float = 0.05     # 5% minimum volatility
    max_volatility: float = 0.5      # 50% maximum volatility

    # Signal confirmation
    require_volume_confirmation: bool = True
    volume_threshold_multiplier: float = 1.2
    sentiment_confirmation_periods: int = 3


@dataclass
class TradeSignal:
    """Represents a trading signal"""
    action: str  # BUY, SELL, CLOSE, HOLD
    strength: float  # 0-1 scale
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float
    reason: str
    confidence: float  # 0-1 scale


class CBBCSentimentStrategy:
    """Trading strategy based on CBBC market sentiment analysis"""

    def __init__(self, params: StrategyParameters = None):
        """
        Initialize the strategy

        Args:
            params: Strategy parameters (uses defaults if not provided)
        """
        self.params = params or StrategyParameters()
        self.cbbc_reader = CBBCDataReader()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        self.position_state = "FLAT"  # FLAT, LONG, SHORT
        self.current_position_size = 0.0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.trade_history = []
        self.equity_curve = []
        self.peak_equity = None

    async def initialize(self, data_path: str = None) -> bool:
        """
        Initialize the strategy with data

        Args:
            data_path: Path to CBSC data file

        Returns:
            bool: True if initialization successful
        """
        try:
            # Load and process data
            if data_path:
                self.cbbc_reader.data_path = data_path

            if not await self.cbbc_reader.load_data():
                logger.error("Failed to load CBSC data")
                return False

            self.cbbc_reader.preprocess_data()

            logger.info("Strategy initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize strategy: {str(e)}")
            return False

    def generate_signal(self, timestamp: datetime = None) -> TradeSignal:
        """
        Generate trading signal based on current market conditions

        Args:
            timestamp: Optional timestamp for the signal

        Returns:
            TradeSignal: Generated trading signal
        """
        if self.cbbc_reader._processed_data is None:
            raise ValueError("Strategy not initialized. Call initialize() first.")

        # Get current data and sentiment
        current_data = self.cbbc_reader._processed_data
        sentiment_metrics = self.sentiment_analyzer.analyze_sentiment(current_data)
        sentiment_level = self.sentiment_analyzer.get_current_sentiment_level(sentiment_metrics)
        market_phase = self.sentiment_analyzer.identify_market_phase(current_data)
        vol_regime = self.sentiment_analyzer.assess_volatility_regime(current_data)

        # Get latest price and indicators
        latest = current_data.iloc[-1]
        current_price = latest['HSIF_Close']
        current_vol = latest['Realized_Volatility'] or 0

        # Initialize signal
        signal = TradeSignal(
            action="HOLD",
            strength=0.0,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            position_size=0.0,
            reason="No clear signal",
            confidence=0.0
        )

        # Check volatility filter
        if not (self.params.min_volatility <= current_vol <= self.params.max_volatility):
            signal.reason = f"Volatility filter: {current_vol:.2%}"
            return signal

        # Volume confirmation check
        volume_confirmed = True
        if self.params.require_volume_confirmation:
            avg_volume = current_data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = latest['Volume']
            volume_confirmed = current_volume > (avg_volume * self.params.volume_threshold_multiplier)

        # Generate signals based on sentiment
        if sentiment_level == SentimentLevel.EXTREME_FEAR and volume_confirmed:
            # Strong buy signal
            signal = self._create_buy_signal(current_price, sentiment_metrics, "Extreme fear detected")
        elif sentiment_level == SentimentLevel.EXTREME_GREED and volume_confirmed:
            # Strong sell signal
            signal = self._create_sell_signal(current_price, sentiment_metrics, "Extreme greed detected")
        elif sentiment_level == SentimentLevel.FEAR and market_phase == MarketPhase.ACCUMULATION:
            # Moderate buy signal
            signal = self._create_buy_signal(current_price, sentiment_metrics, "Fear in accumulation phase")
        elif sentiment_level == SentimentLevel.GREED and market_phase == MarketPhase.DISTRIBUTION:
            # Moderate sell signal
            signal = self._create_sell_signal(current_price, sentiment_metrics, "Greed in distribution phase")
        else:
            # Check for position management signals
            signal = self._check_position_management(current_price, sentiment_level)

        # Adjust signal based on volatility regime
        signal = self._adjust_signal_for_volatility(signal, vol_regime)

        # Add timestamp
        signal.entry_price = current_price if signal.action != "HOLD" else None

        return signal

    def execute_trade(self, signal: TradeSignal, timestamp: datetime = None) -> Dict:
        """
        Execute a trade based on the signal

        Args:
            signal: Trading signal to execute
            timestamp: Trade timestamp

        Returns:
            Dict: Trade execution result
        """
        timestamp = timestamp or datetime.now()
        trade_result = {
            'timestamp': timestamp,
            'action': signal.action,
            'success': False,
            'reason': '',
            'position_size': 0.0,
            'price': 0.0,
            'pnl': 0.0
        }

        try:
            if signal.action == "BUY" and self.position_state == "FLAT":
                # Enter long position
                self.position_state = "LONG"
                self.current_position_size = signal.position_size
                self.entry_price = signal.entry_price
                self.stop_loss = signal.stop_loss
                self.take_profit = signal.take_profit

                trade_result.update({
                    'success': True,
                    'reason': signal.reason,
                    'position_size': signal.position_size,
                    'price': signal.entry_price
                })

            elif signal.action == "SELL" and self.position_state == "FLAT":
                # Enter short position
                self.position_state = "SHORT"
                self.current_position_size = signal.position_size
                self.entry_price = signal.entry_price
                self.stop_loss = signal.stop_loss
                self.take_profit = signal.take_profit

                trade_result.update({
                    'success': True,
                    'reason': signal.reason,
                    'position_size': -signal.position_size,
                    'price': signal.entry_price
                })

            elif signal.action == "CLOSE" and self.position_state != "FLAT":
                # Close existing position
                current_price = self.cbbc_reader._processed_data.iloc[-1]['HSIF_Close']
                pnl = self._calculate_pnl(self.position_state, current_price)

                trade_result.update({
                    'success': True,
                    'reason': signal.reason,
                    'position_size': -self.current_position_size,
                    'price': current_price,
                    'pnl': pnl
                })

                # Reset position
                self.position_state = "FLAT"
                self.current_position_size = 0.0
                self.entry_price = None
                self.stop_loss = None
                self.take_profit = None

            else:
                trade_result['reason'] = "No action taken - invalid state transition"

            # Record trade
            self.trade_history.append(trade_result)

        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            trade_result['reason'] = f"Execution error: {str(e)}"

        return trade_result

    def backtest(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Backtest the strategy on historical data

        Args:
            start_date: Start date for backtest
            end_date: End date for backtest

        Returns:
            Dict: Backtest results
        """
        if self.cbbc_reader._processed_data is None:
            raise ValueError("Strategy not initialized. Call initialize() first.")

        # Get test data
        data = self.cbbc_reader._processed_data.copy()

        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]

        # Reset state
        self._reset_state()

        # Run backtest
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'trade_history': [],
            'equity_curve': []
        }

        initial_capital = 100000
        current_capital = initial_capital
        max_capital = initial_capital

        for date, row in data.iterrows():
            # Update current data slice for analysis
            self.cbbc_reader._processed_data = data.loc[:date]

            # Generate signal
            signal = self.generate_signal(date)

            # Execute trade
            if signal.action in ["BUY", "SELL", "CLOSE"]:
                trade_result = self.execute_trade(signal, date)
                results['trade_history'].append(trade_result)

                # Update capital
                if trade_result['success'] and trade_result['pnl'] != 0:
                    current_capital += trade_result['pnl']
                    max_capital = max(max_capital, current_capital)

            # Track equity
            results['equity_curve'].append({
                'date': date,
                'equity': current_capital,
                'position': self.position_state,
                'position_size': self.current_position_size
            })

        # Calculate performance metrics
        results['total_return'] = (current_capital - initial_capital) / initial_capital
        results['max_drawdown'] = (max_capital - current_capital) / max_capital
        results['total_trades'] = len([t for t in results['trade_history'] if t['success']])
        results['winning_trades'] = len([t for t in results['trade_history'] if t['pnl'] > 0])
        results['losing_trades'] = len([t for t in results['trade_history'] if t['pnl'] < 0])

        # Calculate Sharpe ratio
        returns = [t['pnl'] / initial_capital for t in results['trade_history'] if t['pnl'] != 0]
        if returns:
            results['sharpe_ratio'] = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)

        return results

    def get_performance_metrics(self) -> Dict:
        """
        Get current performance metrics

        Returns:
            Dict: Performance metrics
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'current_position': self.position_state,
                'position_size': self.current_position_size
            }

        winning_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trade_history if t.get('pnl', 0) < 0]
        total_returns = [t.get('pnl', 0) for t in self.trade_history]

        return {
            'total_trades': len(self.trade_history),
            'win_rate': len(winning_trades) / len(self.trade_history),
            'avg_return': np.mean(total_returns),
            'win_avg': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            'loss_avg': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            'profit_factor': abs(sum([t['pnl'] for t in winning_trades]) / (sum([t['pnl'] for t in losing_trades]) + 1e-6)),
            'current_position': self.position_state,
            'position_size': self.current_position_size,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }

    # Private helper methods
    def _create_buy_signal(self, price: float, sentiment, reason: str) -> TradeSignal:
        """Create a buy signal"""
        # Calculate position size based on sentiment strength
        fear_greed_score = sentiment.fear_greed_score
        strength = 1.0 - (fear_greed_score / 100.0)  # Lower score = higher strength

        position_size = min(
            self.params.base_position_size * (1 + strength * self.params.position_scaling_factor),
            self.params.max_position_size
        )

        return TradeSignal(
            action="BUY",
            strength=strength,
            entry_price=price,
            stop_loss=price * (1 - self.params.stop_loss_pct),
            take_profit=price * (1 + self.params.take_profit_pct),
            position_size=position_size,
            reason=reason,
            confidence=strength * 0.8
        )

    def _create_sell_signal(self, price: float, sentiment, reason: str) -> TradeSignal:
        """Create a sell signal"""
        # Calculate position size based on sentiment strength
        fear_greed_score = sentiment.fear_greed_score
        strength = fear_greed_score / 100.0  # Higher score = higher strength

        position_size = min(
            self.params.base_position_size * (1 + strength * self.params.position_scaling_factor),
            self.params.max_position_size
        )

        return TradeSignal(
            action="SELL",
            strength=strength,
            entry_price=price,
            stop_loss=price * (1 + self.params.stop_loss_pct),
            take_profit=price * (1 - self.params.take_profit_pct),
            position_size=position_size,
            reason=reason,
            confidence=strength * 0.8
        )

    def _check_position_management(self, price: float, sentiment_level: SentimentLevel) -> TradeSignal:
        """Check if existing position should be closed"""
        if self.position_state == "FLAT":
            return TradeSignal(action="HOLD", strength=0.0, position_size=0.0, reason="No position")

        # Check stop loss
        if self.stop_loss and ((self.position_state == "LONG" and price <= self.stop_loss) or
                               (self.position_state == "SHORT" and price >= self.stop_loss)):
            return TradeSignal(
                action="CLOSE",
                strength=1.0,
                position_size=0.0,
                reason="Stop loss triggered",
                confidence=1.0
            )

        # Check take profit
        if self.take_profit and ((self.position_state == "LONG" and price >= self.take_profit) or
                                 (self.position_state == "SHORT" and price <= self.take_profit)):
            return TradeSignal(
                action="CLOSE",
                strength=1.0,
                position_size=0.0,
                reason="Take profit triggered",
                confidence=1.0
            )

        # Check sentiment reversal
        if (self.position_state == "LONG" and sentiment_level == SentimentLevel.EXTREME_GREED) or \
           (self.position_state == "SHORT" and sentiment_level == SentimentLevel.EXTREME_FEAR):
            return TradeSignal(
                action="CLOSE",
                strength=0.7,
                position_size=0.0,
                reason="Sentiment reversal detected",
                confidence=0.7
            )

        return TradeSignal(action="HOLD", strength=0.0, position_size=0.0, reason="Maintain position")

    def _adjust_signal_for_volatility(self, signal: TradeSignal, vol_regime) -> TradeSignal:
        """Adjust signal based on volatility regime"""
        # Reduce position size in high volatility
        if vol_regime.value == "HIGH":
            signal.position_size *= 0.5
            signal.confidence *= 0.7
        elif vol_regime.value == "ELEVATED":
            signal.position_size *= 0.75
            signal.confidence *= 0.85

        # Increase position size slightly in low volatility (with caution)
        elif vol_regime.value == "LOW":
            signal.position_size *= 1.1

        return signal

    def _calculate_pnl(self, position_state: str, exit_price: float) -> float:
        """Calculate P&L for closing position"""
        if not self.entry_price or self.current_position_size == 0:
            return 0.0

        price_change_pct = (exit_price - self.entry_price) / self.entry_price

        if position_state == "LONG":
            return self.current_position_size * self.entry_price * price_change_pct
        else:  # SHORT
            return -self.current_position_size * self.entry_price * price_change_pct

    def _reset_state(self):
        """Reset strategy state"""
        self.position_state = "FLAT"
        self.current_position_size = 0.0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.trade_history = []
        self.equity_curve = []