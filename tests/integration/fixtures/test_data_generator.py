"""Test data generator for integration tests."""

import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path


class TestDataGenerator:
    """Generates test data for integration testing."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the test data generator.
        
        Args:
            seed: Random seed for reproducible data
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.hk_stocks = [
            "00700.HK",  # Tencent
            "00005.HK",  # HSBC
            "00003.HK",  # HKEX
            "00388.HK",  # HK Gas
            "00291.HK",  # China Resources
            "00002.HK",  # CLP Holdings
            "00027.HK",  # Galaxy Entertainment
            "01810.HK",  # Xiaomi
            "09988.HK",  # Alibaba
            "03690.HK",  # Meituan
            "00941.HK",  # China Mobile
            "01299.HK",  #友邦保險
            "02020.HK",  # Anta Sports
            "01024.HK",  # Kweichow Moutai
            "00011.HK",  # Sun Hung Kai Properties
            "00939.HK",  # CNOOC
            "00883.HK",  # CNOOC
            "02318.HK",  # Ping An Insurance
            "01093.HK",  # China Petroleum
            "01398.HK",  # Industrial and Commercial Bank of China
        ]
        
        self.us_stocks = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NVDA", "JPM",
            "JNJ", "V", "PG", "UNH", "HD", "MA", "BAC", "XOM", "CVX",
            "LLY", "ABBV", "PFE", "T", "KO", "PEP", "TMO", "COST",
            "AVGO", "NKE", "MRK", "DHR", "LIN", "TXN", "ABT", "CRM"
        ]
        
        self.crypto_symbols = [
            "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX",
            "DOT", "MATIC", "LINK", "UNI", "LTC", "ATOM", "XLM"
        ]

    def generate_market_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        frequency: str = "1min",
        base_price: Optional[float] = None
    ) -> pd.DataFrame:
        """Generate synthetic market data.
        
        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            frequency: Data frequency (1min, 5min, 1h, 1d)
            base_price: Starting price for simulation
            
        Returns:
            DataFrame with OHLCV data
        """
        # Set base price based on symbol type
        if base_price is None:
            if symbol.endswith(".HK"):
                base_price = random.uniform(50, 500)
            elif symbol in self.crypto_symbols:
                base_price = random.uniform(100, 50000)
            else:
                base_price = random.uniform(50, 1000)
        
        # Generate timestamps
        if frequency == "1min":
            freq = "1T"
        elif frequency == "5min":
            freq = "5T"
        elif frequency == "1h":
            freq = "1H"
        elif frequency == "1d":
            freq = "1D"
        else:
            freq = "1T"
        
        timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Generate price movements using random walk
        num_periods = len(timestamps)
        
        # Generate returns with slight positive bias and volatility
        daily_volatility = 0.02  # 2% daily volatility
        if frequency == "1min":
            minute_volatility = daily_volatility / np.sqrt(390)  # 390 trading minutes
            returns = np.random.normal(0.00001, minute_volatility, num_periods)
        elif frequency == "5min":
            returns = np.random.normal(0.00005, daily_volatility / np.sqrt(78), num_periods)
        elif frequency == "1h":
            returns = np.random.normal(0.0003, daily_volatility / np.sqrt(6.5), num_periods)
        else:  # daily
            returns = np.random.normal(0.0005, daily_volatility, num_periods)
        
        # Calculate prices
        prices = [base_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, base_price * 0.5))  # Prevent negative prices
        
        # Generate OHLC data
        data = []
        for i, ts in enumerate(timestamps):
            close = prices[i]
            
            # Generate realistic intraday movements
            if frequency in ["1min", "5min", "1h"]:
                # Intraday bars
                high_offset = random.uniform(0, 0.005)
                low_offset = random.uniform(0, 0.005)
                open_offset = random.uniform(-0.002, 0.002)
                
                high = close * (1 + high_offset)
                low = close * (1 - low_offset)
                
                if i > 0:
                    open_price = prices[i-1] * (1 + open_offset)
                else:
                    open_price = close
                
                # Ensure OHLC relationships
                high = max(high, open_price, close)
                low = min(low, open_price, close)
            else:
                # Daily bars
                high = close * random.uniform(1.0, 1.02)
                low = close * random.uniform(0.98, 1.0)
                open_price = close * random.uniform(0.99, 1.01)
                
                high = max(high, open_price)
                low = min(low, open_price)
            
            # Generate volume
            if symbol.endswith(".HK"):
                base_volume = random.uniform(1000000, 10000000)
            elif symbol in self.crypto_symbols:
                base_volume = random.uniform(100, 10000)
            else:
                base_volume = random.uniform(100000, 1000000)
            
            volume = int(base_volume * random.uniform(0.5, 2.0))
            
            # Calculate VWAP
            vwap = (high + low + close) / 3
            
            data.append({
                "timestamp": ts,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
                "vwap": round(vwap, 2),
                "num_trades": random.randint(100, 1000)
            })
        
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        
        return df

    def generate_trading_signals(
        self,
        symbols: List[str],
        num_signals: int = 100,
        signal_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate trading signals.
        
        Args:
            symbols: List of symbols to generate signals for
            num_signals: Number of signals to generate
            signal_types: List of signal types to use
            
        Returns:
            List of trading signal dictionaries
        """
        if signal_types is None:
            signal_types = ["BUY", "SELL", "HOLD"]
        
        signals = []
        
        for i in range(num_signals):
            symbol = random.choice(symbols)
            signal_type = random.choice(signal_types)
            confidence = random.uniform(0.5, 1.0)
            
            # Generate timestamp within last 30 days
            days_ago = random.uniform(0, 30)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            # Generate strategy-specific info
            strategy_id = random.choice([
                "momentum_strategy",
                "mean_reversion_strategy",
                "trend_following_strategy",
                "arbitrage_strategy",
                "ml_prediction_strategy"
            ])
            
            signal = {
                "id": f"signal_{i}_{int(timestamp.timestamp())}",
                "symbol": symbol,
                "action": signal_type,
                "confidence": round(confidence, 3),
                "timestamp": timestamp.isoformat(),
                "strategy_id": strategy_id,
                "parameters": {
                    "price": round(random.uniform(50, 500), 2),
                    "volume": random.randint(100, 10000),
                    "indicators": {
                        "rsi": round(random.uniform(0, 100), 2),
                        "macd": round(random.uniform(-5, 5), 3),
                        "bb_upper": round(random.uniform(100, 200), 2),
                        "bb_lower": round(random.uniform(50, 150), 2)
                    }
                },
                "metadata": {
                    "source": "test_generator",
                    "version": "1.0"
                }
            }
            
            signals.append(signal)
        
        # Sort by timestamp
        signals.sort(key=lambda x: x["timestamp"])
        
        return signals

    def generate_portfolio_data(
        self,
        symbols: List[str],
        total_value: float = 1000000.0,
        num_positions: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate portfolio data.
        
        Args:
            symbols: List of symbols for positions
            total_value: Total portfolio value
            num_positions: Number of positions to create
            
        Returns:
            Portfolio data dictionary
        """
        if num_positions is None:
            num_positions = min(len(symbols), 10)
        
        selected_symbols = random.sample(symbols, num_positions)
        
        # Generate positions
        positions = []
        remaining_value = total_value * 0.9  # Keep 10% cash
        
        for symbol in selected_symbols:
            # Allocate random portion of portfolio
            if len(positions) == len(selected_symbols) - 1:
                # Last position gets remaining value
                position_value = remaining_value
            else:
                position_value = remaining_value * random.uniform(0.05, 0.3)
                remaining_value -= position_value
            
            # Generate position details
            current_price = random.uniform(50, 500)
            quantity = int(position_value / current_price)
            avg_cost = current_price * random.uniform(0.9, 1.1)
            
            position = {
                "symbol": symbol,
                "quantity": quantity,
                "avg_cost": round(avg_cost, 2),
                "current_price": round(current_price, 2),
                "market_value": round(quantity * current_price, 2),
                "unrealized_pnl": round(
                    quantity * (current_price - avg_cost), 2
                ),
                "unrealized_pnl_pct": round(
                    (current_price - avg_cost) / avg_cost * 100, 2
                ),
                "weight": round(position_value / total_value * 100, 2)
            }
            
            positions.append(position)
        
        # Calculate portfolio metrics
        total_market_value = sum(p["market_value"] for p in positions)
        total_pnl = sum(p["unrealized_pnl"] for p in positions)
        cash_balance = total_value - total_market_value
        
        portfolio = {
            "id": f"portfolio_{int(datetime.utcnow().timestamp())}",
            "name": "Test Portfolio",
            "total_value": round(total_value, 2),
            "cash_balance": round(cash_balance, 2),
            "market_value": round(total_market_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl / (total_value - cash_balance) * 100, 2),
            "positions": positions,
            "sector_allocation": self._generate_sector_allocation(positions),
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "currency": "USD",
                "risk_level": random.choice(["low", "medium", "high"])
            }
        }
        
        return portfolio

    def generate_risk_metrics(
        self,
        portfolio_value: float = 1000000.0,
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """Generate risk metrics.
        
        Args:
            portfolio_value: Portfolio value for calculations
            lookback_days: Number of days for risk calculations
            
        Returns:
            Risk metrics dictionary
        """
        # Generate random daily returns
        daily_returns = np.random.normal(0.0005, 0.01, lookback_days)
        
        # Calculate metrics
        volatility = np.std(daily_returns) * np.sqrt(252)  # Annualized
        
        # VaR calculations (95% and 99%)
        var_95 = np.percentile(daily_returns, 5) * portfolio_value
        var_99 = np.percentile(daily_returns, 1) * portfolio_value
        
        # Expected Shortfall
        es_95 = np.mean(daily_returns[daily_returns <= var_95/portfolio_value]) * portfolio_value
        es_99 = np.mean(daily_returns[daily_returns <= var_99/portfolio_value]) * portfolio_value
        
        # Maximum Drawdown (simplified)
        cumulative_returns = np.cumprod(1 + daily_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Beta and Alpha (mock values)
        beta = random.uniform(0.7, 1.3)
        alpha = random.uniform(-0.02, 0.03)
        
        # Sharpe Ratio
        sharpe_ratio = (np.mean(daily_returns) * 252) / volatility
        
        # Sortino Ratio
        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = np.std(downside_returns) * np.sqrt(252)
        sortino_ratio = (np.mean(daily_returns) * 252) / downside_volatility
        
        # Concentration metrics
        positions = random.randint(5, 20)
        max_position_weight = random.uniform(0.05, 0.25)
        herfindahl_index = sum(
            (max_position_weight * random.uniform(0.5, 1.5))**2 
            for _ in range(positions)
        )
        
        risk_metrics = {
            "portfolio_value": portfolio_value,
            "volatility": round(volatility, 4),
            "var_95": round(abs(var_95), 2),
            "var_99": round(abs(var_99), 2),
            "expected_shortfall_95": round(abs(es_95), 2),
            "expected_shortfall_99": round(abs(es_99), 2),
            "max_drawdown": round(abs(max_drawdown), 4),
            "max_drawdown_duration": random.randint(10, 60),
            "beta": round(beta, 3),
            "alpha": round(alpha, 4),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "information_ratio": round(random.uniform(-0.5, 0.5), 3),
            "tracking_error": round(random.uniform(0.02, 0.08), 4),
            "concentration_metrics": {
                "num_positions": positions,
                "max_position_weight": round(max_position_weight, 4),
                "herfindahl_index": round(herfindahl_index, 4),
                "top_5_concentration": round(
                    max_position_weight * 5 * random.uniform(0.7, 1.0), 4
                )
            },
            "stress_test_results": {
                "market_crash": round(
                    portfolio_value * random.uniform(-0.15, -0.05), 2
                ),
                "interest_rate_shock": round(
                    portfolio_value * random.uniform(-0.10, -0.02), 2
                ),
                "liquidity_crisis": round(
                    portfolio_value * random.uniform(-0.12, -0.04), 2
                )
            },
            "metadata": {
                "calculated_at": datetime.utcnow().isoformat(),
                "lookback_period_days": lookback_days,
                "confidence_level": [95, 99]
            }
        }
        
        return risk_metrics

    def generate_system_metrics(self) -> Dict[str, Any]:
        """Generate system performance metrics.
        
        Returns:
            System metrics dictionary
        """
        # CPU metrics
        cpu_usage = random.uniform(20, 80)
        cpu_cores = random.choice([4, 8, 12, 16])
        
        # Memory metrics
        total_memory = random.choice([16, 32, 64, 128])  # GB
        memory_usage = total_memory * random.uniform(0.3, 0.8)
        
        # Disk metrics
        total_disk = random.choice([500, 1000, 2000])  # GB
        disk_usage = total_disk * random.uniform(0.4, 0.9)
        
        # Network metrics
        network_in = random.uniform(100, 1000)  # Mbps
        network_out = random.uniform(50, 500)   # Mbps
        
        # Database metrics
        db_connections = random.randint(10, 100)
        db_query_time = random.uniform(0.01, 0.5)  # seconds
        
        # API metrics
        api_requests_per_second = random.uniform(50, 500)
        api_response_time = random.uniform(50, 300)  # milliseconds
        api_error_rate = random.uniform(0.001, 0.01)
        
        # Trading metrics
        trades_per_second = random.uniform(0.1, 10)
        order_latency = random.uniform(10, 100)  # milliseconds
        
        system_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "usage_percent": round(cpu_usage, 2),
                "cores": cpu_cores,
                "load_average": [round(cpu_usage/cores * random.uniform(0.8, 1.2), 2) for _ in range(3)]
            },
            "memory": {
                "total_gb": total_memory,
                "used_gb": round(memory_usage, 2),
                "available_gb": round(total_memory - memory_usage, 2),
                "usage_percent": round(memory_usage / total_memory * 100, 2)
            },
            "disk": {
                "total_gb": total_disk,
                "used_gb": round(disk_usage, 2),
                "available_gb": round(total_disk - disk_usage, 2),
                "usage_percent": round(disk_usage / total_disk * 100, 2),
                "read_iops": random.randint(100, 1000),
                "write_iops": random.randint(50, 500)
            },
            "network": {
                "incoming_mbps": round(network_in, 2),
                "outgoing_mbps": round(network_out, 2),
                "connections": random.randint(100, 1000),
                "packets_per_second": random.randint(1000, 10000)
            },
            "database": {
                "active_connections": db_connections,
                "query_time_avg_ms": round(db_query_time * 1000, 2),
                "transactions_per_second": random.randint(100, 1000),
                "cache_hit_rate": round(random.uniform(0.85, 0.99), 4)
            },
            "api": {
                "requests_per_second": round(api_requests_per_second, 2),
                "response_time_avg_ms": round(api_response_time, 2),
                "response_time_p95_ms": round(api_response_time * random.uniform(1.5, 3), 2),
                "error_rate": round(api_error_rate, 4),
                "active_websockets": random.randint(50, 500)
            },
            "trading": {
                "trades_per_second": round(trades_per_second, 2),
                "order_latency_ms": round(order_latency, 2),
                "fill_rate": round(random.uniform(0.95, 0.99), 4),
                "pending_orders": random.randint(10, 100)
            },
            "alerts": {
                "critical": random.randint(0, 2),
                "warning": random.randint(0, 5),
                "info": random.randint(0, 10)
            },
            "health": {
                "overall_status": random.choice(["healthy", "warning", "critical"]),
                "uptime_seconds": random.randint(3600, 86400 * 30),
                "last_restart": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
            }
        }
        
        return system_metrics

    def _generate_sector_allocation(self, positions: List[Dict]) -> Dict[str, float]:
        """Generate sector allocation for portfolio positions.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            Dictionary mapping sectors to allocation percentages
        """
        sectors = [
            "Technology", "Finance", "Healthcare", "Consumer", "Energy",
            "Industrial", "Real Estate", "Utilities", "Materials", "Communication"
        ]
        
        # Assign random sectors to positions
        allocation = {}
        remaining = 100.0
        
        for i, position in enumerate(positions):
            if i == len(positions) - 1:
                # Last position gets remaining allocation
                allocation_pct = remaining
            else:
                allocation_pct = remaining * random.uniform(0.05, 0.3)
                remaining -= allocation_pct
            
            sector = random.choice(sectors)
            if sector in allocation:
                allocation[sector] += allocation_pct
            else:
                allocation[sector] = allocation_pct
        
        # Round percentages
        allocation = {k: round(v, 2) for k, v in allocation.items()}
        
        return allocation

    def save_test_data(
        self,
        data: Any,
        filename: str,
        directory: str = "test_data/integration"
    ) -> str:
        """Save test data to file.
        
        Args:
            data: Data to save
            filename: Filename for the data
            directory: Directory to save to
            
        Returns:
            Path to saved file
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = Path(directory) / filename
        
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath)
        elif isinstance(data, (dict, list)):
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
        
        return str(filepath)

    def load_test_data(
        self,
        filename: str,
        directory: str = "test_data/integration"
    ) -> Any:
        """Load test data from file.
        
        Args:
            filename: Filename to load
            directory: Directory to load from
            
        Returns:
            Loaded data
        """
        filepath = Path(directory) / filename
        
        if filepath.suffix == '.csv':
            return pd.read_csv(filepath, index_col=0, parse_dates=True)
        elif filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported file type: {filepath.suffix}")


# Example usage
if __name__ == "__main__":
    generator = TestDataGenerator(seed=42)
    
    # Generate sample market data
    market_data = generator.generate_market_data(
        symbol="00700.HK",
        start_date=datetime.utcnow() - timedelta(days=7),
        end_date=datetime.utcnow(),
        frequency="1min"
    )
    print(f"Generated {len(market_data)} rows of market data")
    
    # Generate trading signals
    signals = generator.generate_trading_signals(
        symbols=["00700.HK", "00005.HK", "00988.HK"],
        num_signals=50
    )
    print(f"Generated {len(signals)} trading signals")
    
    # Generate portfolio data
    portfolio = generator.generate_portfolio_data(
        symbols=generator.hk_stocks[:5],
        total_value=1000000
    )
    print(f"Generated portfolio with {len(portfolio['positions'])} positions")
    
    # Save test data
    generator.save_test_data(market_data, "sample_market_data.csv")
    generator.save_test_data(signals, "sample_signals.json")
    generator.save_test_data(portfolio, "sample_portfolio.json")
    print("Test data saved successfully")