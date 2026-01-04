"""
Data Source Configuration Module
真實數據源配置管理
"""
from typing import Optional


class DataSourceConfig:
    """數據源配置"""

    def __init__(
        self,
        yahoo_finance_enabled: bool = True,
        yahoo_finance_timeout: int = 30,
        yahoo_finance_retry_attempts: int = 3,
        yahoo_finance_retry_delay: int = 1,
        strict_mode: bool = True,
        data_validation_enabled: bool = True,
        enable_cache: bool = True,
        cache_ttl: int = 300,
        max_requests_per_minute: int = 60,
    ):
        # Yahoo Finance 配置
        self.yahoo_finance_enabled = yahoo_finance_enabled
        self.yahoo_finance_timeout = yahoo_finance_timeout  # seconds
        self.yahoo_finance_retry_attempts = yahoo_finance_retry_attempts
        self.yahoo_finance_retry_delay = yahoo_finance_retry_delay  # seconds

        # 嚴格模式配置
        self.strict_mode = strict_mode  # 不降級到 mock data
        self.data_validation_enabled = data_validation_enabled

        # 緩存配置
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl  # 5 minutes in seconds

        # API 限制
        self.max_requests_per_minute = max_requests_per_minute  # Yahoo Finance rate limit


class DataValidatorConfig:
    """數據驗證配置"""

    def __init__(
        self,
        max_missing_ratio: float = 0.05,
        min_price: float = 0.01,
        max_price_change_ratio: float = 0.5,
        allow_gaps: bool = False,
        max_gap_days: int = 7,
    ):
        # 缺失值容忍度
        self.max_missing_ratio = max_missing_ratio  # 最多 5% 缺失值

        # 價格異常值檢測
        self.min_price = min_price  # 最低價格
        self.max_price_change_ratio = max_price_change_ratio  # 單日最大漲跌幅 50%

        # 時間序列驗證
        self.allow_gaps = allow_gaps  # 是否允許日期間隙
        self.max_gap_days = max_gap_days  # 最大允許間隙天數


class BacktestConfig:
    """回測配置"""

    def __init__(
        self,
        use_real_data: bool = True,
        fallback_to_mock: bool = False,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
    ):
        # 數據源
        self.use_real_data = use_real_data  # 使用真實數據
        self.fallback_to_mock = fallback_to_mock  # 嚴格模式：不降級

        # 回測參數
        self.initial_capital = initial_capital  # 初始資金
        self.commission_rate = commission_rate  # 手續費率 0.1%
        self.slippage_rate = slippage_rate  # 滑點 0.05%


# Global configuration instances
data_source_config = DataSourceConfig()
validator_config = DataValidatorConfig()
backtest_config = BacktestConfig()
