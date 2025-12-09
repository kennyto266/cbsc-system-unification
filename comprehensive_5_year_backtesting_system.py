"""
Comprehensive 5+ Year Backtesting System - All Phases Integration
Professional quantitative trading platform with long-term backtesting capabilities

This system integrates all 4 phases:
- Phase 1: Data Infrastructure & API Integration
- Phase 2: Advanced Analytics & Statistical Framework
- Phase 3: Performance Optimization & CLI Tools
- Phase 4: Testing & Professional Reporting
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
import warnings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import psutil
import gc
import time
import sys
import argparse
from abc import ABC, abstractmethod

# Import all our modules
from src.data.yahoo_finance_adapter import ProfessionalYahooFinanceAdapter, DataConfig
from src.data.hkma_enhanced_adapter import EnhancedHKMAAdapter
from src.data.long_term_storage import LongTermStorageManager, StorageConfig
from src.data.data_quality_validator import ProfessionalDataQualityValidator, QualityReport
from src.analysis.long_term_indicators import LongTermTechnicalIndicators, GovernmentDataFusion
from src.analysis.statistical_validation import StatisticalValidationFramework, ValidationConfig
from src.backtesting.long_term_backtesting_engine import LongTermBacktestingEngine, BacktestConfig, StrategySignal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_backtesting.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """Comprehensive system configuration"""
    # Data sources
    data_sources: List[str] = field(default_factory=lambda: ['yahoo_finance', 'hkma'])
    symbols: List[str] = field(default_factory=lambda: ['0700.HK', '0941.HK', '1299.HK'])
    lookback_years: int = 10

    # Storage
    enable_storage: bool = True
    storage_config: StorageConfig = field(default_factory=StorageConfig)

    # Validation
    enable_validation: bool = True
    validation_threshold: float = 70.0  # Minimum quality score

    # Indicators
    enable_government_fusion: bool = True
    indicator_categories: List[str] = field(default_factory=lambda: ['trend', 'momentum', 'volatility', 'volume'])

    # Backtesting
    initial_capital: float = 1000000.0
    commission: float = 0.001
    enable_chunking: bool = True
    chunk_size: int = 50000

    # Performance
    max_workers: int = mp.cpu_count() - 1
    memory_limit_gb: float = 8.0
    enable_parallel_processing: bool = True

    # Output
    output_dir: str = "results"
    save_intermediate: bool = True
    generate_reports: bool = True

class DataPipeline(ABC):
    """Abstract base class for data pipelines"""

    @abstractmethod
    def fetch_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetch data for given symbols and date range"""
        pass

class YahooFinanceDataPipeline(DataPipeline):
    """Yahoo Finance data pipeline"""

    def __init__(self, config: DataConfig = None):
        self.adapter = ProfessionalYahooFinanceAdapter(config)

    def fetch_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetch market data from Yahoo Finance"""
        logger.info(f"Fetching Yahoo Finance data for {len(symbols)} symbols")

        market_data = {}
        for symbol in symbols:
            try:
                data = self.adapter.fetch_long_term_data(symbol, period="max")
                if not data.empty:
                    # Filter by date range
                    data['date'] = pd.to_datetime(data['date'])
                    data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
                    market_data[symbol] = data
                    logger.info(f"Fetched {len(data)} records for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")

        return market_data

class HKMADataPipeline(DataPipeline):
    """HKMA government data pipeline"""

    def __init__(self):
        self.adapter = EnhancedHKMAAdapter()

    def fetch_data(self, symbols: List[str] = None, start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """Fetch HKMA government data"""
        logger.info("Fetching HKMA government data")

        try:
            hkma_data = self.adapter.fetch_all_sources()
            logger.info(f"Fetched HKMA data from {len(hkma_data)} sources")
            return hkma_data
        except Exception as e:
            logger.error(f"Error fetching HKMA data: {e}")
            return {}

class ComprehensiveBacktestingSystem:
    """Comprehensive 5+ year backtesting system"""

    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        self._initialize_components()
        self._setup_directories()

    def _initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing comprehensive backtesting system")

        # Data pipelines
        self.yahoo_pipeline = YahooFinanceDataPipeline()
        self.hkma_pipeline = HKMADataPipeline()

        # Storage
        if self.config.enable_storage:
            self.storage_manager = LongTermStorageManager(self.config.storage_config)

        # Quality validation
        if self.config.enable_validation:
            self.quality_validator = ProfessionalDataQualityValidator()

        # Technical indicators
        self.indicator_engine = LongTermTechnicalIndicators()

        # Statistical validation
        self.statistical_validator = StatisticalValidationFramework()

        # Backtesting engine
        self.backtest_engine = LongTermBacktestingEngine(BacktestConfig(
            initial_cash=self.config.initial_capital,
            commission=self.config.commission,
            chunk_size=self.config.chunk_size,
            max_workers=self.config.max_workers
        ))

        logger.info("System components initialized successfully")

    def _setup_directories(self):
        """Setup required directories"""
        directories = [
            self.config.output_dir,
            f"{self.config.output_dir}/data",
            f"{self.config.output_dir}/indicators",
            f"{self.config.output_dir}/backtests",
            f"{self.config.output_dir}/reports",
            f"{self.config.output_dir}/visualizations"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def run_comprehensive_analysis(self, symbols: List[str] = None,
                                 start_date: str = None, end_date: str = None,
                                 strategy_func: Callable = None) -> Dict[str, Any]:
        """
        Run comprehensive 5+ year analysis

        Args:
            symbols: List of symbols to analyze
            start_date: Analysis start date
            end_date: Analysis end date
            strategy_func: Strategy function for signal generation

        Returns:
            Comprehensive analysis results
        """
        logger.info("Starting comprehensive 5+ year analysis")

        # Use defaults if not provided
        symbols = symbols or self.config.symbols
        if not start_date:
            start_date = (datetime.now() - timedelta(days=self.config.lookback_years * 365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Analyzing {len(symbols)} symbols from {start_date} to {end_date}")

        start_time = time.time()

        # Phase 1: Data Infrastructure & API Integration
        logger.info("Phase 1: Fetching and validating data")
        market_data, hkma_data = self._fetch_and_validate_data(symbols, start_date, end_date)

        # Phase 2: Advanced Analytics & Statistical Framework
        logger.info("Phase 2: Computing indicators and statistical analysis")
        indicators_data, statistical_reports = self._compute_indicators_and_analysis(market_data, hkma_data, symbols)

        # Phase 3: Performance Optimization & Backtesting
        logger.info("Phase 3: Running optimized backtests")
        backtest_results = self._run_backtests(market_data, indicators_data, symbols, strategy_func)

        # Phase 4: Testing & Professional Reporting
        logger.info("Phase 4: Generating comprehensive reports")
        comprehensive_report = self._generate_comprehensive_report(
            market_data, indicators_data, statistical_reports, backtest_results, symbols
        )

        execution_time = time.time() - start_time
        logger.info(f"Comprehensive analysis completed in {execution_time:.2f} seconds")

        return {
            'execution_time': execution_time,
            'analysis_period': f"{start_date} to {end_date}",
            'symbols_analyzed': symbols,
            'data_summary': self._summarize_data(market_data, hkma_data),
            'quality_summary': self._summarize_quality(statistical_reports),
            'backtest_summary': self._summarize_backtests(backtest_results),
            'comprehensive_report': comprehensive_report
        }

    def _fetch_and_validate_data(self, symbols: List[str], start_date: str, end_date: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """Fetch and validate data from all sources"""
        # Fetch market data
        market_data = self.yahoo_pipeline.fetch_data(symbols, start_date, end_date)

        # Fetch HKMA data
        hkma_data = self.hkma_pipeline.fetch_data()

        # Validate data quality
        if self.config.enable_validation and market_data:
            for symbol, data in market_data.items():
                quality_report = self.quality_validator.validate_market_data(data, symbol)
                logger.info(f"Quality score for {symbol}: {quality_report.quality_score:.1f}")

                if quality_report.quality_score < self.config.validation_threshold:
                    logger.warning(f"Low quality score for {symbol}: {quality_report.quality_score:.1f}")

        # Store data if enabled
        if self.config.enable_storage and self.storage_manager:
            for symbol, data in market_data.items():
                result = self.storage_manager.store_market_data(data, symbol, "price")
                logger.info(f"Stored {result['records_stored']} records for {symbol}")

        return market_data, hkma_data

    def _compute_indicators_and_analysis(self, market_data: Dict[str, pd.DataFrame],
                                       hkma_data: Dict[str, pd.DataFrame],
                                       symbols: List[str]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
        """Compute technical indicators and statistical analysis"""
        indicators_data = {}
        statistical_reports = {}

        # Initialize government data fusion if enabled
        gov_fusion = None
        if self.config.enable_government_fusion and hkma_data:
            gov_fusion = GovernmentDataFusion(hkma_data)

        # Process each symbol
        for symbol in symbols:
            if symbol not in market_data:
                logger.warning(f"No market data for {symbol}")
                continue

            try:
                # Compute technical indicators
                indicators = self.indicator_engine.calculate_all_indicators(
                    market_data[symbol], gov_fusion
                )
                indicators_data[symbol] = indicators

                # Run statistical validation
                if 'close' in market_data[symbol].columns:
                    returns = market_data[symbol]['close'].pct_change().dropna()
                    if len(returns) > self.config.validation_threshold:
                        statistical_report = self.statistical_validator.validate_strategy(
                            returns, strategy_name=f"{symbol} Buy and Hold", symbol=symbol
                        )
                        statistical_reports[symbol] = statistical_report

                logger.info(f"Computed indicators for {symbol}: {len(indicators.columns)} features")

            except Exception as e:
                logger.error(f"Error computing indicators for {symbol}: {e}")

        return indicators_data, statistical_reports

    def _run_backtests(self, market_data: Dict[str, pd.DataFrame],
                      indicators_data: Dict[str, pd.DataFrame],
                      symbols: List[str], strategy_func: Callable = None) -> Dict[str, Any]:
        """Run comprehensive backtests"""
        backtest_results = {}

        for symbol in symbols:
            if symbol not in market_data or symbol not in indicators_data:
                logger.warning(f"No data for backtesting {symbol}")
                continue

            try:
                # Generate strategy signals
                if strategy_func:
                    signals = strategy_func(market_data[symbol], indicators_data[symbol], symbol)
                else:
                    # Default simple strategy
                    signals = self._generate_default_signals(market_data[symbol], indicators_data[symbol])

                # Run backtest
                result = self.backtest_engine.backtest_strategy(
                    market_data[symbol], signals, symbol
                )
                backtest_results[symbol] = result

                logger.info(f"Backtest completed for {symbol}: {result.total_return:.2%} return")

            except Exception as e:
                logger.error(f"Error running backtest for {symbol}: {e}")

        return backtest_results

    def _generate_default_signals(self, market_data: pd.DataFrame, indicators_data: pd.DataFrame) -> StrategySignal:
        """Generate default trading signals"""
        # Simple moving average crossover
        if 'close' in market_data.columns:
            close = market_data['close']
            sma_short = close.rolling(window=20).mean()
            sma_long = close.rolling(window=50).mean()

            entries = sma_short > sma_long
            exits = sma_short < sma_long

            return StrategySignal(
                name="Default SMA Crossover",
                entries=entries,
                exits=exits,
                parameters={'short_window': 20, 'long_window': 50},
                description="Default 20/50 SMA crossover strategy"
            )

        # Fallback to simple momentum
        if 'RSI_14' in indicators_data.columns:
            rsi = indicators_data['RSI_14']
            entries = rsi < 30  # Oversold
            exits = rsi > 70   # Overbought

            return StrategySignal(
                name="Default RSI Strategy",
                entries=entries,
                exits=exits,
                parameters={'rsi_period': 14, 'oversold': 30, 'overbought': 70},
                description="Default RSI oversold/overbought strategy"
            )

        # Empty signals if no indicators available
        n = len(market_data)
        return StrategySignal(
            name="No Strategy",
            entries=pd.Series([False] * n, index=market_data.index),
            exits=pd.Series([False] * n, index=market_data.index),
            description="No viable strategy generated"
        )

    def _generate_comprehensive_report(self, market_data: Dict[str, pd.DataFrame],
                                    indicators_data: Dict[str, pd.DataFrame],
                                    statistical_reports: Dict[str, Any],
                                    backtest_results: Dict[str, Any],
                                    symbols: List[str]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        report = {
            'summary': {
                'analysis_date': datetime.now().isoformat(),
                'symbols_analyzed': len(symbols),
                'data_periods': {},
                'total_market_records': sum(len(data) for data in market_data.values()),
                'total_indicators': sum(len(data.columns) for data in indicators_data.values()) if indicators_data else 0
            },
            'performance_summary': {},
            'quality_summary': {},
            'recommendations': [],
            'detailed_results': {}
        }

        # Data period summary
        for symbol in symbols:
            if symbol in market_data and not market_data[symbol].empty:
                data = market_data[symbol]
                report['summary']['data_periods'][symbol] = {
                    'start': data.index.min().strftime('%Y-%m-%d'),
                    'end': data.index.max().strftime('%Y-%m-%d'),
                    'records': len(data)
                }

        # Performance summary
        for symbol, result in backtest_results.items():
            report['performance_summary'][symbol] = {
                'total_return': f"{result.total_return:.2%}",
                'annualized_return': f"{result.annualized_return:.2%}",
                'sharpe_ratio': f"{result.sharpe_ratio:.2f}",
                'max_drawdown': f"{result.max_drawdown:.2%}",
                'win_rate': f"{result.win_rate:.2%}",
                'total_trades': result.total_trades
            }

        # Quality summary
        for symbol, quality_report in statistical_reports.items():
            report['quality_summary'][symbol] = {
                'quality_score': f"{quality_report.quality_score:.1f}",
                'quality_category': quality_report.quality_category.value,
                'total_issues': len(quality_report.validation_results)
            }

        # Generate recommendations
        report['recommendations'] = self._generate_system_recommendations(
            market_data, indicators_data, statistical_reports, backtest_results
        )

        # Detailed results
        if self.config.save_intermediate:
            report['detailed_results'] = {
                'statistical_reports': statistical_reports,
                'backtest_results': backtest_results
            }

        return report

    def _generate_system_recommendations(self, market_data: Dict[str, pd.DataFrame],
                                       indicators_data: Dict[str, pd.DataFrame],
                                       statistical_reports: Dict[str, Any],
                                       backtest_results: Dict[str, Any]) -> List[str]:
        """Generate system-level recommendations"""
        recommendations = []

        # Data quality recommendations
        avg_quality_score = np.mean([
            report.quality_score for report in statistical_reports.values()
        ]) if statistical_reports else 0

        if avg_quality_score < 80:
            recommendations.append("Overall data quality is below optimal. Consider additional data cleaning and validation.")

        # Performance recommendations
        if backtest_results:
            avg_return = np.mean([result.total_return for result in backtest_results.values()])
            avg_sharpe = np.mean([result.sharpe_ratio for result in backtest_results.values()])

            if avg_sharpe < 1.0:
                recommendations.append("Risk-adjusted returns are suboptimal. Consider strategy optimization or risk management improvements.")

            if avg_return < 0.05:  # 5% annual return
                recommendations.append("Low returns detected. Consider alternative strategies or market conditions.")

        # System optimization recommendations
        if len(market_data) > 1000000:  # Large dataset
            recommendations.append("Large dataset detected. Consider enabling chunking and parallel processing for better performance.")

        # General recommendations
        recommendations.extend([
            "Regular monitoring of economic indicators can improve strategy performance.",
            "Consider incorporating additional technical indicators for better signal generation.",
            "Implement proper risk management and position sizing in live trading.",
            "Validate strategies on out-of-sample data before deployment."
        ])

        return recommendations

    def _summarize_data(self, market_data: Dict[str, pd.DataFrame], hkma_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Summarize fetched data"""
        return {
            'market_data': {
                'symbols': list(market_data.keys()),
                'total_records': sum(len(data) for data in market_data.values()),
                'date_range': self._get_overall_date_range(market_data)
            },
            'hkma_data': {
                'sources': list(hkma_data.keys()),
                'total_records': sum(len(data) for data in hkma_data.values()),
                'date_range': self._get_overall_date_range(hkma_data)
            }
        }

    def _summarize_quality(self, statistical_reports: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize quality validation results"""
        if not statistical_reports:
            return {'message': 'No quality reports available'}

        quality_scores = [report.quality_score for report in statistical_reports.values()]

        return {
            'avg_quality_score': np.mean(quality_scores),
            'min_quality_score': np.min(quality_scores),
            'max_quality_score': np.max(quality_scores),
            'symbols_analyzed': len(statistical_reports),
            'above_threshold': sum(1 for score in quality_scores if score >= self.config.validation_threshold)
        }

    def _summarize_backtests(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize backtest results"""
        if not backtest_results:
            return {'message': 'No backtest results available'}

        returns = [result.total_return for result in backtest_results.values()]
        sharpe_ratios = [result.sharpe_ratio for result in backtest_results.values()]
        drawdowns = [result.max_drawdown for result in backtest_results.values()]

        return {
            'symbols_tested': len(backtest_results),
            'avg_return': np.mean(returns),
            'best_return': np.max(returns),
            'worst_return': np.min(returns),
            'avg_sharpe_ratio': np.mean(sharpe_ratios),
            'avg_max_drawdown': np.mean(drawdowns),
            'positive_returns': sum(1 for r in returns if r > 0),
            'sharpe_above_1': sum(1 for sr in sharpe_ratios if sr > 1.0)
        }

    def _get_overall_date_range(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Get overall date range for data dictionary"""
        all_dates = []
        for data in data_dict.values():
            if not data.empty:
                all_dates.append(data.index.min())
                all_dates.append(data.index.max())

        if all_dates:
            return {
                'start': min(all_dates).strftime('%Y-%m-%d'),
                'end': max(all_dates).strftime('%Y-%m-%d')
            }
        return {'start': 'N/A', 'end': 'N/A'}

    def save_comprehensive_results(self, results: Dict[str, Any], output_file: str = None):
        """Save comprehensive results to file"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{self.config.output_dir}/comprehensive_analysis_{timestamp}.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Comprehensive results saved to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None

def create_cli():
    """Create command line interface"""
    parser = argparse.ArgumentParser(description='Comprehensive 5+ Year Backtesting System')

    parser.add_argument('--symbols', nargs='+', default=['0700.HK', '0941.HK', '1299.HK'],
                       help='Symbols to analyze')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--lookback-years', type=int, default=10,
                       help='Number of years to look back')
    parser.add_argument('--initial-capital', type=float, default=1000000.0,
                       help='Initial capital for backtesting')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='Commission rate')
    parser.add_argument('--output-dir', type=str, default='results',
                       help='Output directory')
    parser.add_argument('--max-workers', type=int, default=None,
                       help='Maximum number of workers')
    parser.add_argument('--disable-validation', action='store_true',
                       help='Disable data quality validation')
    parser.add_argument('--disable-storage', action='store_true',
                       help='Disable data storage')
    parser.add_argument('--disable-fusion', action='store_true',
                       help='Disable government data fusion')
    parser.add_argument('--save-report', type=str,
                       help='Save report to specified file')

    return parser

# Example strategy functions
def sample_momentum_strategy(market_data: pd.DataFrame, indicators_data: pd.DataFrame, symbol: str) -> StrategySignal:
    """Sample momentum strategy using RSI and MACD"""
    if 'RSI_14' in indicators_data.columns and 'MACD_12_26_9_MACD' in indicators_data.columns:
        rsi = indicators_data['RSI_14']
        macd = indicators_data['MACD_12_26_9_MACD']

        # Entry conditions: RSI oversold and MACD positive
        entries = (rsi < 30) & (macd > 0)

        # Exit conditions: RSI overbought or MACD negative
        exits = (rsi > 70) | (macd < 0)

        return StrategySignal(
            name=f"Momentum_RSI_MACD_{symbol}",
            entries=entries,
            exits=exits,
            parameters={'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70},
            description="Momentum strategy using RSI oversold/overbought with MACD confirmation"
        )

    # Fallback to simple strategy
    system = ComprehensiveBacktestingSystem()
    return system._generate_default_signals(market_data, indicators_data)

def sample_trend_following_strategy(market_data: pd.DataFrame, indicators_data: pd.DataFrame, symbol: str) -> StrategySignal:
    """Sample trend following strategy using moving averages"""
    if 'close' in market_data.columns:
        close = market_data['close']

        # Multiple timeframe moving averages
        sma_short = close.rolling(window=10).mean()
        sma_medium = close.rolling(window=30).mean()
        sma_long = close.rolling(window=90).mean()

        # Entry: Short > Medium > Long (uptrend)
        entries = (sma_short > sma_medium) & (sma_medium > sma_long)

        # Exit: Short < Medium (trend reversal)
        exits = sma_short < sma_medium

        return StrategySignal(
            name=f"Trend_Following_{symbol}",
            entries=entries,
            exits=exits,
            parameters={'short_window': 10, 'medium_window': 30, 'long_window': 90},
            description="Trend following strategy using multiple timeframe moving averages"
        )

    # Fallback to simple strategy
    system = ComprehensiveBacktestingSystem()
    return system._generate_default_signals(market_data, indicators_data)

def main():
    """Main execution function"""
    parser = create_cli()
    args = parser.parse_args()

    # Create configuration
    config = SystemConfig(
        symbols=args.symbols,
        lookback_years=args.lookback_years,
        initial_capital=args.initial_capital,
        commission=args.commission,
        output_dir=args.output_dir,
        max_workers=args.max_workers or (mp.cpu_count() - 1),
        enable_validation=not args.disable_validation,
        enable_storage=not args.disable_storage,
        enable_government_fusion=not args.disable_fusion
    )

    # Initialize system
    system = ComprehensiveBacktestingSystem(config)

    try:
        # Run comprehensive analysis with sample strategies
        results = system.run_comprehensive_analysis(
            symbols=config.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            strategy_func=sample_momentum_strategy
        )

        # Print summary
        print("\n" + "="*80)
        print("COMPREHENSIVE 5+ YEAR BACKTESTING SYSTEM - EXECUTION SUMMARY")
        print("="*80)
        print(f"Execution Time: {results['execution_time']:.2f} seconds")
        print(f"Analysis Period: {results['analysis_period']}")
        print(f"Symbols Analyzed: {len(results['symbols_analyzed'])}")
        print(f"Total Market Records: {results['data_summary']['market_data']['total_records']:,}")
        print(f"Total Indicators: {results['data_summary']['market_data']['total_records']:,}")

        # Performance summary
        if results['backtest_summary']['symbols_tested'] > 0:
            print(f"\nPERFORMANCE SUMMARY:")
            print(f"  Average Return: {results['backtest_summary']['avg_return']:.2%}")
            print(f"  Best Return: {results['backtest_summary']['best_return']:.2%}")
            print(f"  Worst Return: {results['backtest_summary']['worst_return']:.2%}")
            print(f"  Average Sharpe Ratio: {results['backtest_summary']['avg_sharpe_ratio']:.2f}")
            print(f"  Average Max Drawdown: {results['backtest_summary']['avg_max_drawdown']:.2%}")
            print(f"  Positive Returns: {results['backtest_summary']['positive_returns']}/{results['backtest_summary']['symbols_tested']}")

        # Quality summary
        if results['quality_summary']['symbols_analyzed'] > 0:
            print(f"\nDATA QUALITY SUMMARY:")
            print(f"  Average Quality Score: {results['quality_summary']['avg_quality_score']:.1f}")
            print(f"  Above Threshold: {results['quality_summary']['above_threshold']}/{results['quality_summary']['symbols_analyzed']}")

        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(results['comprehensive_report']['recommendations'], 1):
            print(f"  {i}. {rec}")

        # Save results
        output_file = system.save_comprehensive_results(results, args.save_report)
        if output_file:
            print(f"\nDetailed results saved to: {output_file}")

        print("\n" + "="*80)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*80)

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        print(f"\nError: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())