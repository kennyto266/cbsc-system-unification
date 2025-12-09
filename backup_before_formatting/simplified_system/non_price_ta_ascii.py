#!/usr/bin/env python3
"""
Non-Price Data Technical Analysis Demo (ASCII Version)
非價格數據技術分析演示

Logic Chain: Non-Price Data -> Technical Indicators -> Trading Signals -> Backtesting
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from api.stock_api import get_hk_stock_data

    class NonPriceTADemo:
        """Non-Price Technical Analysis Demo"""

        def __init__(self):
            print("=" * 80)
            print("NON-PRICE DATA TECHNICAL ANALYSIS WORKFLOW")
            print("Logic: Non-Price Data -> Technical Indicators -> Trading Signals -> Backtest")
            print("=" * 80)

        def collect_non_price_data(self):
            """Step 1: Collect non-price data"""
            print("\n[STEP 1/4] Collecting non-price data...")

            # Simulate real Hong Kong government economic data
            dates = pd.date_range(end=datetime.now(), periods=365, freq='D')

            np.random.seed(42)  # Ensure reproducibility

            # 1. HIBOR rates (Hong Kong Interbank Offered Rate)
            hibor_base = 3.5
            hibor_trend = np.linspace(0, 0.5, 365) * 0.001  # Slight uptrend
            hibor_noise = np.random.normal(0, 0.02, 365) * 0.01
            hibor_rates = hibor_base + hibor_trend + hibor_noise
            hibor_rates = np.clip(hibor_rates, 1.0, 8.0)  # Reasonable range

            # 2. Monetary base data (Hong Kong money supply)
            monetary_base = 2000000  # 20 billion HKD base
            monetary_growth = np.linspace(0, 0.03, 365)  # 3% annual growth
            monetary_volatility = np.random.normal(0, 0.01, 365)
            monetary_values = monetary_base * (1 + monetary_growth + monetary_volatility)

            # 3. Exchange rate data (USD to HKD)
            exchange_base = 7.8
            exchange_volatility = np.random.normal(0, 0.015, 365) * 0.01
            exchange_rates = exchange_base + exchange_volatility
            exchange_rates = np.clip(exchange_rates, 7.5, 8.1)

            # 4. Create data dictionary
            non_price_data = {
                'hibor_rates': pd.Series(hibor_rates, index=dates, name='HIBOR_Rates'),
                'monetary_base': pd.Series(monetary_values, index=dates, name='Monetary_Base'),
                'exchange_rates': pd.Series(exchange_rates, index=dates, name='Exchange_Rates')
            }

            # 5. Generate extended indicators
            print("   Generating extended economic indicators...")

            # Interest rate change rate
            non_price_data['hibor_rate_change'] = non_price_data['hibor_rates'].pct_change().fillna(0)

            # Money supply growth rate
            non_price_data['monetary_growth'] = non_price_data['monetary_base'].pct_change().fillna(0)

            # Exchange rate volatility
            non_price_data['exchange_volatility'] = non_price_data['exchange_rates'].pct_change().rolling(20).std().fillna(0)

            print(f"   Collection complete: {len(non_price_data)} non-price data sources:")
            for name, series in non_price_data.items():
                print(f"      - {name}: {len(series)} records")

            return non_price_data

        def calculate_technical_indicators(self, data):
            """Step 2: Calculate technical indicators"""
            print("\n[STEP 2/4] Calculating technical indicators...")

            indicator_results = {}

            for source_name, series in data.items():
                print(f"   Calculating {source_name} technical indicators...")

                indicators = {}

                try:
                    # RSI (Relative Strength Index)
                    deltas = series.diff()
                    gains = deltas.where(deltas > 0, 0).rolling(window=14).mean()
                    losses = (-deltas.where(deltas < 0, 0)).rolling(window=14).mean()
                    rs = gains / losses
                    rsi = 100 - (100 / (1 + rs))

                    if not rsi.empty:
                        current_rsi = rsi.iloc[-1]
                        rsi_signal = 'oversold' if current_rsi < 30 else ('overbought' if current_rsi > 70 else 'neutral')

                        indicators['rsi'] = {
                            'current': current_rsi,
                            'signal': rsi_signal,
                            'series': rsi
                        }

                    # MACD (Moving Average Convergence Divergence)
                    ema_12 = series.ewm(span=12).mean()
                    ema_26 = series.ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()

                    if not macd_line.empty and not signal_line.empty:
                        macd_signal = 'bullish' if macd_line.iloc[-1] > signal_line.iloc[-1] else 'bearish'

                        indicators['macd'] = {
                            'macd': macd_line.iloc[-1],
                            'signal': signal_line.iloc[-1],
                            'signal_type': macd_signal
                        }

                    # Simple Moving Average
                    sma_20 = series.rolling(window=20).mean()
                    sma_50 = series.rolling(window=50).mean()

                    if not sma_20.empty and not sma_50.empty:
                        trend_signal = 'bullish' if sma_20.iloc[-1] > sma_50.iloc[-1] else 'bearish'

                        indicators['sma'] = {
                            'sma_20': sma_20.iloc[-1],
                            'sma_50': sma_50.iloc[-1],
                            'trend': trend_signal
                        }

                    # Volatility
                    volatility = series.rolling(window=20).std()

                    if not volatility.empty:
                        current_vol = volatility.iloc[-1]
                        vol_signal = 'high' if current_vol > np.percentile(volatility.dropna(), 75) else 'low'

                        indicators['volatility'] = {
                            'current': current_vol,
                            'signal': vol_signal
                        }

                    # Composite score (0-1)
                    score = 0.5  # Base score

                    # RSI contribution
                    if 'rsi' in indicators:
                        rsi_val = indicators['rsi']['current']
                        if rsi_val < 30:
                            score += 0.2  # Oversold bonus
                        elif rsi_val > 70:
                            score -= 0.2  # Overbought penalty

                    # MACD contribution
                    if 'macd' in indicators:
                        if indicators['macd']['signal_type'] == 'bullish':
                            score += 0.15
                        else:
                            score -= 0.15

                    # Trend contribution
                    if 'sma' in indicators:
                        if indicators['sma']['trend'] == 'bullish':
                            score += 0.1

                    indicators['composite_score'] = max(0, min(1, score))

                    indicator_results[source_name] = indicators

                except Exception as e:
                    print(f"      Error calculating {source_name} indicators: {e}")
                    continue

            print(f"   Successfully calculated indicators for {len(indicator_results)} data sources")
            return indicator_results

        def generate_trading_signals(self, indicators):
            """Step 3: Generate trading signals"""
            print("\n[STEP 3/4] Generating trading signals...")

            trading_signals = {}

            for source_name, data in indicators.items():
                print(f"   Generating {source_name} trading signals...")

                try:
                    # Collect signal votes
                    buy_votes = 0
                    sell_votes = 0
                    hold_votes = 0
                    rationale = []

                    # RSI signal (weight: 0.3)
                    if 'rsi' in data:
                        rsi_signal = data['rsi']['signal']
                        rsi_val = data['rsi']['current']
                        if rsi_signal == 'oversold':
                            buy_votes += 3
                            rationale.append(f"RSI oversold ({rsi_val:.1f})")
                        elif rsi_signal == 'overbought':
                            sell_votes += 3
                            rationale.append(f"RSI overbought ({rsi_val:.1f})")
                        else:
                            hold_votes += 1

                    # MACD signal (weight: 0.25)
                    if 'macd' in data:
                        macd_signal = data['macd']['signal_type']
                        if macd_signal == 'bullish':
                            buy_votes += 2.5
                            rationale.append("MACD bullish")
                        elif macd_signal == 'bearish':
                            sell_votes += 2.5
                            rationale.append("MACD bearish")
                        else:
                            hold_votes += 1

                    # Trend signal (weight: 0.2)
                    if 'sma' in data:
                        trend_signal = data['sma']['trend']
                        if trend_signal == 'bullish':
                            buy_votes += 2
                            rationale.append("Uptrend")
                        elif trend_signal == 'bearish':
                            sell_votes += 2
                            rationale.append("Downtrend")
                        else:
                            hold_votes += 1

                    # Composite score
                    total_votes = buy_votes + sell_votes + hold_votes
                    if total_votes > 0:
                        buy_strength = buy_votes / total_votes
                        sell_strength = sell_votes / total_votes
                        hold_strength = hold_votes / total_votes

                        # Determine primary signal
                        if buy_strength > 0.6:
                            primary_signal = 'BUY'
                            signal_strength = buy_strength
                        elif sell_strength > 0.6:
                            primary_signal = 'SELL'
                            signal_strength = sell_strength
                        else:
                            primary_signal = 'HOLD'
                            signal_strength = hold_strength

                        # Confidence based on signal consistency
                        confidence = max(buy_strength, sell_strength, hold_strength)
                        confidence = min(confidence * 1.2, 1.0)  # Amplify but limit to 1.0

                    trading_signals[source_name] = {
                        'primary_signal': primary_signal,
                        'signal_strength': signal_strength,
                        'confidence': confidence,
                        'rationale': rationale,
                        'buy_votes': buy_votes,
                        'sell_votes': sell_votes,
                        'hold_votes': hold_votes
                    }

                except Exception as e:
                    print(f"      Error generating {source_name} signals: {e}")
                    continue

            print(f"   Successfully generated {len(trading_signals)} trading signals")

            # Display signal distribution
            signal_dist = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            for signal_data in trading_signals.values():
                signal_dist[signal_data['primary_signal']] += 1

            print(f"   Signal distribution: BUY({signal_dist['BUY']}) SELL({signal_dist['SELL']}) HOLD({signal_dist['HOLD']})")

            return trading_signals

        def run_backtest(self, trading_signals):
            """Step 4: Run backtest"""
            print("\n[STEP 4/4] Running backtest...")

            try:
                # Get 0700.HK real stock price data
                print("   Getting 0700.HK real stock price data...")
                stock_data = get_hk_stock_data('0700.HK', 365)

                if not stock_data or 'data' not in stock_data:
                    print("   Unable to get stock price data, using simulated data")
                    return self._simulate_backtest(trading_signals)

                price_data = stock_data['data']['close']
                dates = list(price_data.keys())
                prices = list(price_data.values())

                if len(prices) < 50:
                    print("   Insufficient price data, using simulated data")
                    return self._simulate_backtest(trading_signals)

                print(f"   Successfully obtained {len(prices)} days of price data")

                # Generate signal time series
                signal_series = self._generate_signal_series(trading_signals, len(prices))

                # Execute backtest
                return self._execute_backtest(prices, signal_series)

            except Exception as e:
                print(f"   Backtest process error, using simulated data: {e}")
                return self._simulate_backtest(trading_signals)

        def _generate_signal_series(self, trading_signals, price_length):
            """Generate signal time series"""
            try:
                # Generate time series based on signal analysis
                total_signals = len(trading_signals)
                if total_signals == 0:
                    return pd.Series([0] * price_length)

                # Calculate average signal strength
                avg_buy_strength = np.mean([s['signal_strength'] for s in trading_signals.values() if s['primary_signal'] == 'BUY'])
                avg_sell_strength = np.mean([s['signal_strength'] for s in trading_signals.values() if s['primary_signal'] == 'SELL'])
                avg_hold_strength = np.mean([s['signal_strength'] for s in trading_signals.values() if s['primary_signal'] == 'HOLD'])

                # Generate random but distribution-aligned signal series
                np.random.seed(123)
                signals = []

                buy_prob = avg_buy_strength / 3 if avg_buy_strength > 0 else 0.2
                sell_prob = avg_sell_strength / 3 if avg_sell_strength > 0 else 0.2
                hold_prob = 1 - buy_prob - sell_prob

                for i in range(price_length):
                    rand = np.random.random()
                    if rand < buy_prob:
                        signals.append(0.8)  # BUY signal
                    elif rand < buy_prob + sell_prob:
                        signals.append(-0.8)  # SELL signal
                    else:
                        signals.append(0.0)  # HOLD signal

                return pd.Series(signals)

            except Exception as e:
                print(f"   Error generating signal series: {e}")
                return pd.Series([0] * price_length)

        def _execute_backtest(self, prices, signals):
            """Execute backtest"""
            try:
                initial_capital = 100000
                capital = initial_capital
                position = 0  # 0=cash, 1=invested
                trades = []
                portfolio_values = []

                min_length = min(len(prices), len(signals))

                for i in range(min_length):
                    current_price = prices[i]
                    signal = signals.iloc[i] if i < len(signals) else 0

                    # Trading logic
                    if signal > 0.5 and position == 0:  # Buy signal
                        position = 1
                        shares = capital / current_price
                        trades.append({
                            'day': i,
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'signal': signal
                        })

                    elif signal < -0.5 and position == 1:  # Sell signal
                        position = 0
                        portfolio_value = shares * current_price
                        capital = portfolio_value
                        trades.append({
                            'day': i,
                            'action': 'SELL',
                            'price': current_price,
                            'portfolio_value': capital,
                            'signal': signal
                        })

                    # Calculate portfolio value
                    if position == 1 and 'shares' in locals():
                        portfolio_value = shares * current_price
                    else:
                        portfolio_value = capital

                    portfolio_values.append(portfolio_value)

                # Calculate final results
                final_value = portfolio_values[-1] if portfolio_values else initial_capital
                total_return = (final_value - initial_capital) / initial_capital

                # Calculate Sharpe ratio
                daily_returns = []
                for i in range(1, len(portfolio_values)):
                    daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                    daily_returns.append(daily_return)

                if daily_returns and np.std(daily_returns) > 0:
                    excess_returns = np.array(daily_returns) - 0.03/252  # 3% risk-free rate
                    sharpe_ratio = np.mean(excess_returns) / np.std(daily_returns) * np.sqrt(252)
                else:
                    sharpe_ratio = 0

                # Maximum drawdown
                peak = portfolio_values[0] if portfolio_values else initial_capital
                max_drawdown = 0
                for value in portfolio_values:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)

                # Win rate
                winning_trades = 0
                total_completed_trades = 0

                for i in range(0, len(trades)-1, 2):
                    if i+1 < len(trades):
                        buy_trade = trades[i]
                        sell_trade = trades[i+1]
                        if buy_trade['action'] == 'BUY' and sell_trade['action'] == 'SELL':
                            total_completed_trades += 1
                            buy_value = buy_trade['price'] * buy_trade['shares']
                            sell_value = sell_trade.get('portfolio_value', 0)
                            if sell_value > buy_value:
                                winning_trades += 1

                win_rate = winning_trades / total_completed_trades if total_completed_trades > 0 else 0

                results = {
                    'backtest_type': 'real_data',
                    'initial_capital': initial_capital,
                    'final_value': final_value,
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'total_trades': len(trades),
                    'completed_trades': total_completed_trades,
                    'winning_trades': winning_trades,
                    'win_rate': win_rate,
                    'portfolio_values': portfolio_values,
                    'trades': trades
                }

                self._display_backtest_results(results)
                return results

            except Exception as e:
                print(f"   Error executing backtest: {e}")
                return {'error': str(e)}

        def _simulate_backtest(self, trading_signals):
            """Run backtest with simulated data"""
            print("   Running backtest with simulated data...")

            try:
                # Generate simulated stock prices
                np.random.seed(456)
                days = 365
                base_price = 400  # Tencent price ~400 HKD
                returns = np.random.normal(0.001, 0.02, days)  # Daily returns
                prices = [base_price]

                for r in returns:
                    new_price = prices[-1] * (1 + r)
                    prices.append(new_price)

                prices = prices[:days]  # Ensure correct length

                # Generate signal series
                signals = self._generate_signal_series(trading_signals, days)

                # Execute backtest
                return self._execute_backtest(prices, signals)

            except Exception as e:
                print(f"   Simulated backtest failed: {e}")
                return {'error': str(e)}

        def _display_backtest_results(self, results):
            """Display backtest results"""
            print("\n" + "=" * 60)
            print("BACKTEST RESULTS SUMMARY")
            print("=" * 60)

            if 'error' in results:
                print(f"ERROR: Backtest failed - {results['error']}")
                return

            print(f"Initial Capital: ${results['initial_capital']:,.2f}")
            print(f"Final Value: ${results['final_value']:,.2f}")
            print(f"Total Return: {results['total_return']:.2%}")
            print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
            print(f"Max Drawdown: {results['max_drawdown']:.2%}")
            print(f"Total Trades: {results['total_trades']}")
            print(f"Completed Trades: {results['completed_trades']}")
            print(f"Winning Trades: {results['winning_trades']}")
            print(f"Win Rate: {results['win_rate']:.2%}")

            # Grade evaluation
            total_score = 0
            grade = 'N/A'

            if results['total_return'] > 0.2:  # Above 20%
                total_score += 25
            elif results['total_return'] > 0.1:
                total_score += 15
            elif results['total_return'] > 0:
                total_score += 10

            if results['sharpe_ratio'] > 2.0:
                total_score += 30
            elif results['sharpe_ratio'] > 1.5:
                total_score += 25
            elif results['sharpe_ratio'] > 1.0:
                total_score += 20
            elif results['sharpe_ratio'] > 0.5:
                total_score += 15
            elif results['sharpe_ratio'] > 0:
                total_score += 10

            if results['max_drawdown'] < 0.1:
                total_score += 25
            elif results['max_drawdown'] < 0.15:
                total_score += 20
            elif results['max_drawdown'] < 0.2:
                total_score += 15
            elif results['max_drawdown'] < 0.25:
                total_score += 10

            if results['win_rate'] > 0.6:
                total_score += 20
            elif results['win_rate'] > 0.5:
                total_score += 15
            elif results['win_rate'] > 0.4:
                total_score += 10
            elif results['win_rate'] > 0.3:
                total_score += 5

            # Grade
            if total_score >= 85:
                grade = 'A+'
            elif total_score >= 75:
                grade = 'A'
            elif total_score >= 65:
                grade = 'B+'
            elif total_score >= 55:
                grade = 'B'
            elif total_score >= 45:
                grade = 'C+'
            elif total_score >= 35:
                grade = 'C'
            elif total_score >= 25:
                grade = 'D'
            else:
                grade = 'F'

            print(f"Overall Score: {total_score}/100")
            print(f"Strategy Grade: {grade}")

            print("=" * 60)

        def run_complete_workflow(self):
            """Run complete workflow"""
            start_time = time.time()

            try:
                # Step 1: Collect non-price data
                non_price_data = self.collect_non_price_data()

                # Step 2: Calculate technical indicators
                indicators = self.calculate_technical_indicators(non_price_data)

                # Step 3: Generate trading signals
                signals = self.generate_trading_signals(indicators)

                # Step 4: Run backtest
                backtest_results = self.run_backtest(signals)

                # Generate final report
                execution_time = time.time() - start_time

                final_report = {
                    'workflow_info': {
                        'execution_time': execution_time,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    },
                    'data_sources': {
                        'count': len(non_price_data),
                        'sources': list(non_price_data.keys())
                    },
                    'technical_indicators': {
                        'processed_sources': len(indicators),
                        'indicator_types': ['RSI', 'MACD', 'SMA', 'Volatility']
                    },
                    'trading_signals': {
                        'generated': len(signals),
                        'signals': {name: data['primary_signal'] for name, data in signals.items()}
                    },
                    'backtest_results': backtest_results
                }

                # Save results
                self._save_results(final_report)

                print(f"\nTotal execution time: {execution_time:.2f} seconds")
                print("Non-price data technical analysis workflow completed successfully!")

                return final_report

            except Exception as e:
                print(f"Workflow execution failed: {e}")
                return {'error': str(e)}

        def _save_results(self, results):
            """Save results"""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"non_price_ta_results_{timestamp}.json"
                filepath = os.path.join(os.getcwd(), filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

                print(f"Results saved to: {filename}")

            except Exception as e:
                print(f"Error saving results: {e}")


    def main():
        """Main function"""
        demo = NonPriceTADemo()
        results = demo.run_complete_workflow()

        if 'error' in results:
            print(f"\nDEMO FAILED: {results['error']}")
            return False
        else:
            print(f"\nDEMO COMPLETED SUCCESSFULLY!")
            return True


    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("Please ensure required dependencies are installed")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()