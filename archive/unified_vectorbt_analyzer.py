#!/usr/bin/env python3
"""
Unified VectorBT Professional Analyzer
Unified quantitative analysis entry point, integrating VectorBT Professional skill with existing system

Based on your CLAUDE.md project guidelines, this tool will:
- Use real data sources (Central API, Hong Kong government data)
- Calculate correct Sharpe Ratio (3% risk-free rate)
- Integrate with VectorBT Professional skill
- Provide professional-grade quantitative analysis
"""

import sys
import os
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Any, Optional

# Add VectorBT Professional script path
vbt_script_paths = [
    'C:\\Users\\Penguin8n\\.claude\\plugins\\marketplaces\\anthropic-agent-skills\\vectorbt-professional\\scripts',
    'C:\\Users\\Penguin8n\\.claude\\plugins\\marketplaces\\anthropic-agent-skills\\vectorbt-professional-installed\\vectorbt-professional\\scripts'
]

vbt_found = False
for vbt_script_path in vbt_script_paths:
    if os.path.exists(vbt_script_path):
        sys.path.append(vbt_script_path)
        print(f"Found VectorBT scripts at: {vbt_script_path}")
        vbt_found = True
        break

if not vbt_found:
    print("VectorBT scripts not found in any expected location")

try:
    from backtest_engine import BacktestEngine
    from indicator_calculator import IndicatorCalculator
    from portfolio_optimizer import PortfolioOptimizer
    VBT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: VectorBT Professional scripts not available: {e}")
    VBT_AVAILABLE = False

# Ignore warnings
warnings.filterwarnings('ignore')

class UnifiedVectorBTAnalyzer:
    """Unified VectorBT Analyzer"""

    def __init__(self):
        self.risk_free_rate = 0.03  # 3% risk-free rate
        self.base_url = "http://18.180.162.113:9191"

        if VBT_AVAILABLE:
            self.engine = BacktestEngine()
            self.calculator = IndicatorCalculator(cache_enabled=True)
            self.optimizer = PortfolioOptimizer(risk_free_rate=self.risk_free_rate)
        else:
            print("VectorBT not available, using fallback implementations")
            self._setup_fallback_implementations()

    def get_hk_stock_data(self, symbol: str, duration_days: int = 1095) -> pd.DataFrame:
        """Get Hong Kong stock real data"""
        try:
            url = self.base_url + "/inst/getInst"
            params = {
                "symbol": symbol.lower(),
                "duration": duration_days
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                # Parse nested data structure
                dates = list(data['data']['close'].keys())
                prices = list(data['data']['close'].values())

                df = pd.DataFrame({
                    'Date': pd.to_datetime(dates),
                    'Close': prices
                }).set_index('Date')

                # Generate OHLCV data (simplified version, real application needs more complete data)
                df['Open'] = df['Close'].shift(1)
                df['High'] = df['Close'] * 1.02  # Assume high price is 2% above close
                df['Low'] = df['Close'] * 0.98   # Assume low price is 2% below close
                df['Volume'] = 1000000  # Assume volume

                # Clean first row NaN
                df = df.dropna()

                print(f"Successfully fetched {symbol} data: {len(df)} records")
                print(f"   Time range: {df.index.min()} to {df.index.max()}")
                print(f"   Price range: {df['Close'].min():.2f} - {df['Close'].max():.2f}")

                return df
            else:
                print(f"[ERROR] Data format error: {symbol}")
                return None

        except Exception as e:
            print(f"[ERROR] Failed to fetch data {symbol}: {e}")
            return None

    def analyze_single_stock(self, symbol: str = "0700.HK") -> Dict[str, Any]:
        """Analyze single stock"""
        print(f"\n[INFO] Starting analysis for {symbol}...")

        # Get data
        data = self.get_hk_stock_data(symbol)
        if data is None:
            return {"error": "Failed to fetch data"}

        results = {}

        if VBT_AVAILABLE:
            # Use VectorBT Professional
            try:
                # Basic statistics
                results['basic_stats'] = {
                    'returns': data['Close'].pct_change().mean() * 252,
                    'volatility': data['Close'].pct_change().std() * np.sqrt(252),
                    'current_price': data['Close'].iloc[-1],
                    'price_change': (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
                }

                # Calculate technical indicators
                print("[INFO] Calculating technical indicators...")
                indicators = ['RSI', 'MACD', 'BBANDS', 'ATR']
                indicator_results = self.calculator.calculate_multiple_indicators(data, indicators)

                results['indicators'] = {}
                for name, df in indicator_results.items():
                    if not df.empty:
                        results['indicators'][name] = {
                            'latest_value': df.iloc[-1, 0] if len(df.columns) == 1 else df.iloc[-1].to_dict(),
                            'mean': df.mean().mean() if len(df.columns) == 1 else df.mean().to_dict(),
                            'std': df.std().std() if len(df.columns) == 1 else df.std().to_dict()
                        }

                # Create and test RSI strategy
                print("[INFO] Testing RSI strategy...")
                rsi_strategy = self.engine.create_strategy('rsi', window=14, oversold=30, overbought=70)
                portfolio = self.engine.run_backtest(data, rsi_strategy)

                # Calculate performance metrics
                returns = portfolio.returns()
                results['backtest'] = self._calculate_performance_metrics(returns)

                print(f"[SUCCESS] {symbol} analysis completed")

            except Exception as e:
                print(f"[ERROR] VectorBT analysis failed: {e}")
                results['error'] = str(e)
        else:
            # Fallback implementation
            print("[WARNING] Using basic analysis method...")
            results = self._basic_analysis(data)

        return results

    def analyze_portfolio(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Analyze portfolio"""
        if symbols is None:
            # Default HSI constituents
            symbols = ["0700.HK", "0941.HK", "1299.HK", "0388.HK", "1398.HK", "3988.HK"]

        print(f"\n[INFO] Starting portfolio analysis: {symbols}")

        # Get all stock data
        stock_data = {}
        for symbol in symbols:
            data = self.get_hk_stock_data(symbol, duration_days=365)  # 1 year data
            if data is not None:
                stock_data[symbol] = data

        if len(stock_data) < 2:
            return {"error": "Insufficient data for portfolio analysis"}

        # Build returns matrix
        returns_data = {}
        for symbol, data in stock_data.items():
            returns_data[symbol] = data['Close'].pct_change().dropna()

        returns_df = pd.DataFrame(returns_data)

        results = {}

        if VBT_AVAILABLE:
            try:
                # Portfolio optimization
                print("[INFO] Performing portfolio optimization...")
                opt_result = self.optimizer.optimize_portfolio(returns_df, objective='sharpe')

                if opt_result['success']:
                    results['optimization'] = {
                        'weights': opt_result['weights'].to_dict(),
                        'expected_return': opt_result['metrics']['annual_return'],
                        'expected_volatility': opt_result['metrics']['annual_volatility'],
                        'sharpe_ratio': opt_result['metrics']['sharpe_ratio']
                    }
                    print("[SUCCESS] Portfolio optimization completed")
                else:
                    results['error'] = "Optimization failed: " + opt_result.get('error', 'Unknown error')

                # Equal weight portfolio benchmark
                equal_weights = np.array([1/len(symbols)] * len(symbols))
                equal_returns = returns_df.dot(equal_weights)

                results['benchmark'] = self._calculate_performance_metrics(equal_returns)
                results['benchmark']['weights'] = {symbol: 1/len(symbols) for symbol in symbols}

            except Exception as e:
                print(f"[ERROR] Portfolio analysis failed: {e}")
                results['error'] = str(e)
        else:
            # Basic portfolio analysis
            results = self._basic_portfolio_analysis(returns_df, symbols)

        return results

    def _calculate_performance_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate performance metrics"""
        if len(returns) == 0:
            return {}

        # Basic metrics
        total_return = (1 + returns).prod() - 1
        annual_return = returns.mean() * 252
        volatility = returns.std() * np.sqrt(252)

        # Sharpe Ratio (using 3% risk-free rate)
        if volatility > 0:
            sharpe_ratio = (annual_return - self.risk_free_rate) / volatility
        else:
            sharpe_ratio = 0

        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = drawdowns.min()

        # Other metrics
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (annual_return - self.risk_free_rate) / (downside_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = float('inf') if annual_return > self.risk_free_rate else 0

        # Win rate
        win_rate = (returns > 0).mean()

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'var_95': returns.quantile(0.05),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }

    def _basic_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Basic analysis (fallback method)"""
        returns = data['Close'].pct_change().dropna()

        return {
            'basic_stats': {
                'returns_mean': returns.mean() * 252,
                'returns_std': returns.std() * np.sqrt(252),
                'current_price': data['Close'].iloc[-1],
                'total_return': (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
            },
            'performance': self._calculate_performance_metrics(returns)
        }

    def _basic_portfolio_analysis(self, returns_df: pd.DataFrame, symbols: List[str]) -> Dict[str, Any]:
        """Basic portfolio analysis (fallback method)"""
        # Equal weights
        equal_weights = np.array([1/len(symbols)] * len(symbols))
        equal_returns = returns_df.dot(equal_weights)

        return {
            'benchmark': {
                'weights': {symbol: 1/len(symbols) for symbol in symbols},
                'performance': self._calculate_performance_metrics(equal_returns)
            },
            'analysis_date': datetime.now().isoformat(),
            'symbols_analyzed': symbols
        }

    def _setup_fallback_implementations(self):
        """Setup fallback implementations"""
        self.engine = None
        self.calculator = None
        self.optimizer = None

    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Generate analysis report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
# VectorBT Professional Analysis Report
Generated at: {timestamp}

## Analysis Results Summary

"""

        if 'error' in results:
            report += f"[ERROR] Analysis failed: {results['error']}\n"
        else:
            if 'basic_stats' in results:
                stats = results['basic_stats']
                report += f"""
### Basic Statistics
- Return Rate: {stats.get('returns', 0):.2%}
- Volatility: {stats.get('volatility', 0):.2%}
- Current Price: {stats.get('current_price', 0):.2f}
- Total Return: {stats.get('price_change', 0):.2f}%

"""

            if 'backtest' in results:
                metrics = results['backtest']
                report += f"""
### Backtest Results
- Total Return: {metrics['total_return']:.2%}
- Annual Return: {metrics['annual_return']:.2%}
- Sharpe Ratio: {metrics['sharpe_ratio']:.3f}
- Max Drawdown: {metrics['max_drawdown']:.2%}
- Win Rate: {metrics['win_rate']:.2%}
- Sortino Ratio: {metrics['sortino_ratio']:.3f}

"""

            if 'optimization' in results:
                opt = results['optimization']
                report += f"""
### Portfolio Optimization
- Expected Annual Return: {opt['expected_return']:.2%}
- Expected Volatility: {opt['expected_volatility']:.2%}
- Optimized Sharpe Ratio: {opt['sharpe_ratio']:.3f}

Optimal Weight Allocation:
"""
                for symbol, weight in opt['weights'].items():
                    if weight > 0.01:  # Only show weights greater than 1%
                        report += f"- {symbol}: {weight:.2%}\n"

        report += "\n---\n*Report generated by VectorBT Professional*"

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"[INFO] Report saved to: {output_file}")

        return report


def main():
    """Main function"""
    print("VectorBT Professional Unified Analyzer")
    print("=" * 50)

    analyzer = UnifiedVectorBTAnalyzer()

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "single":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "0700.HK"
            results = analyzer.analyze_single_stock(symbol)

        elif command == "portfolio":
            if len(sys.argv) > 2:
                symbols = sys.argv[2].split(',')
            else:
                symbols = None  # Use default list
            results = analyzer.analyze_portfolio(symbols)

        elif command == "test":
            # Test mode
            print("[INFO] Running test...")
            results = analyzer.analyze_single_stock("0700.HK")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: single, portfolio, test")
            return 1
    else:
        # Default: analyze single stock
        results = analyzer.analyze_single_stock("0700.HK")

    # Generate report
    output_file = f"vectorbt_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    analyzer.generate_report(results, output_file)

    return 0


if __name__ == "__main__":
    exit(main())