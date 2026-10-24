"""
Configuration Management for Unified Backtesting Framework

Centralized configuration management for all backtesting components including
parameter ranges, performance settings, memory limits, and optimization options.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import multiprocessing as mp


@dataclass
class BacktestingConfig:
    """Configuration for the unified backtesting framework"""

    # Parameter Space Configuration
    param_range_start: int = 0
    param_range_end: int = 300
    param_step_size: int = 5

    # Performance Configuration
    max_workers: int = field(default_factory=lambda: min(32, os.cpu_count() or 8))
    chunk_size: int = 1000
    memory_limit_gb: float = 4.0

    # VectorBT Configuration
    vectorbt_batch_size: int = 10000
    vectorbt_memory_limit: str = "4GB"

    # Metrics Configuration
    risk_free_rate: float = 0.02
    benchmark_return: float = 0.10
    trading_days_per_year: int = 252

    # Data Configuration
    data_source: str = "yahoo_finance"
    start_date: str = "2020-01-01"
    end_date: str = "2024-12-31"

    # Strategy Configuration
    strategies: List[str] = field(default_factory=lambda: [
        "rsi_strategy",
        "macd_strategy",
        "bollinger_strategy",
        "sentiment_strategy"
    ])

    # Results Configuration
    output_directory: str = "optimization_results"
    save_intermediate_results: bool = True
    generate_plots: bool = True

    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = "unified_backtesting.log"

    def __post_init__(self):
        """Validate and adjust configuration after initialization"""
        # Ensure workers don't exceed CPU count
        cpu_count = os.cpu_count() or 8
        self.max_workers = min(self.max_workers, cpu_count)

        # Validate parameter range
        if self.param_range_start < 0:
            raise ValueError("Parameter range start must be >= 0")
        if self.param_range_end <= self.param_range_start:
            raise ValueError("Parameter range end must be > start")
        if self.param_step_size <= 0:
            raise ValueError("Parameter step size must be > 0")

        # Adjust memory limit based on available system memory
        try:
            import psutil
            available_memory = psutil.virtual_memory().total / (1024**3)  # GB
            self.memory_limit_gb = min(self.memory_limit_gb, available_memory * 0.8)
        except ImportError:
            # Fallback if psutil not available
            self.memory_limit_gb = min(self.memory_limit_gb, 8.0)

    @property
    def parameter_range(self) -> range:
        """Get the parameter range object"""
        return range(self.param_range_start, self.param_range_end + 1, self.param_step_size)

    @property
    def total_parameter_combinations(self) -> int:
        """Calculate total number of parameter combinations"""
        param_count = len(self.parameter_range)
        # For multi-parameter strategies, this grows exponentially
        # Conservative estimate for 4-parameter strategies
        return param_count ** 4

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'param_range_start': self.param_range_start,
            'param_range_end': self.param_range_end,
            'param_step_size': self.param_step_size,
            'max_workers': self.max_workers,
            'chunk_size': self.chunk_size,
            'memory_limit_gb': self.memory_limit_gb,
            'vectorbt_batch_size': self.vectorbt_batch_size,
            'risk_free_rate': self.risk_free_rate,
            'trading_days_per_year': self.trading_days_per_year,
            'total_parameter_combinations': self.total_parameter_combinations
        }

    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'BacktestingConfig':
        """Create configuration from dictionary"""
        return cls(**config_dict)

    def save(self, filepath: str):
        """Save configuration to JSON file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'BacktestingConfig':
        """Load configuration from JSON file"""
        import json
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)


# Default configuration instance
DEFAULT_CONFIG = BacktestingConfig()