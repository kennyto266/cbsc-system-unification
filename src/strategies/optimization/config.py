"""Configuration settings for optimization module"""
import os
from typing import Optional


class OptimizationConfig:
    """Configuration settings for market data optimization"""

    # HKEX API Configuration
    HKEX_BASE_URL: str = os.getenv(
        'HKEX_BASE_URL',
        'http://localhost:3007/api/market'
    )

    # Request timeout in seconds
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '10'))

    # Date format for validation
    DATE_FORMAT: str = '%Y-%m-%d'

    @classmethod
    def get_hkex_base_url(cls) -> str:
        """Get HKEX base URL from environment or default"""
        return cls.HKEX_BASE_URL

    @classmethod
    def set_hkex_base_url(cls, url: str) -> None:
        """Override HKEX base URL (useful for testing)"""
        cls.HKEX_BASE_URL = url
