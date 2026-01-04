"""
Data Source Configuration Module
真實數據源配置管理
"""
from pydantic import BaseSettings
from typing import Optional


class DataSourceConfig(BaseSettings):
    """數據源配置"""

    # Yahoo Finance 配置
    yahoo_finance_enabled: bool = True
    yahoo_finance_timeout: int = 30  # seconds
    yahoo_finance_retry_attempts: int = 3
    yahoo_finance_retry_delay: int = 1  # seconds

    # 嚴格模式配置
    strict_mode: bool = True  # 不降級到 mock data
    data_validation_enabled: bool = True

    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes in seconds

    # API 限制
    max_requests_per_minute: int = 60  # Yahoo Finance rate limit

    class Config:
        env_file = ".env"
        case_sensitive = False


class DataValidatorConfig(BaseSettings):
    """數據驗證配置"""

    # 缺失值容忍度
    max_missing_ratio: float = 0.05  # 最多 5% 缺失值

    # 價格異常值檢測
    min_price: float = 0.01  # 最低價格
    max_price_change_ratio: float = 0.5  # 單日最大漲跌幅 50%

    # 時間序列驗證
    allow_gaps: bool = False  # 是否允許日期間隙
    max_gap_days: int = 7  # 最大允許間隙天數

    class Config:
        env_file = ".env"


class BacktestConfig(BaseSettings):
    """回測配置"""

    # 數據源
    use_real_data: bool = True  # 使用真實數據
    fallback_to_mock: bool = False  # 嚴格模式：不降級

    # 回測參數
    initial_capital: float = 100000.0  # 初始資金
    commission_rate: float = 0.001  # 手續費率 0.1%
    slippage_rate: float = 0.0005  # 滑點 0.05%

    class Config:
        env_file = ".env"


# Global configuration instances
data_source_config = DataSourceConfig()
validator_config = DataValidatorConfig()
backtest_config = BacktestConfig()
